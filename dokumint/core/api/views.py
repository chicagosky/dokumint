import binascii, logging, base64
from io import BytesIO
from urllib.parse import urlparse

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework import generics, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey


from core import enums
from core.messages import ErrorMessages
from core.forms import normalize_upload_extension, upload_bytes_error
from core.models import DocumentTag
from core.models import ExpenseDocument as ExpenseRecord
from core.models import Profile
from core.mongo import ExpenseDocument
from core.processors.cloud_processors import DocumentProcessorAbstractClass
from core.api.serializers import DocumentSerializer, DocumentTagSerializer, EmailRelayLogSerializer
from core.api.serializers import ProfileSerializer, ProfileServiceSerializer, DocSerializer
from core.utils import get_app_setting
from core.validators import EmailRelayUsernameValidator

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

def _service_profile(user_id):
    """Profile for a service-key call. The caller cannot choose the storage bucket."""
    if user_id is None or str(user_id).strip() == '':
        return None
    return Profile.objects.filter(user_id=user_id).first()

def _owned_document(user, pk):
    return get_object_or_404(ExpenseRecord, user=user, pk=pk)

def _s3_location(uri):
    parsed = urlparse(uri or '')
    if parsed.scheme != 's3' or not parsed.netloc:
        return None, None
    return parsed.netloc, parsed.path.lstrip('/')

class AnalyzeDocumentAPI(APIView):
    """
    API to invoke analysis of document and extraction of document elements.
    The API key is a service credential. The object must already live in that user's bucket.
    """
    permission_classes = [HasAPIKey]

    def post(self, request, format=None):
        profile = _service_profile(request.POST.get('user_id'))
        if profile is None or not profile.storage_bucket:
            return JsonResponse({'error': 'Unknown user.'}, status=status.HTTP_400_BAD_REQUEST)

        s3_uri = request.POST.get('s3_uri', '')
        bucket, key = _s3_location(s3_uri)
        documents_prefix = get_app_setting('', 'cloud_processor.folders.documents')
        if bucket != profile.storage_bucket or not key or not key.startswith(documents_prefix):
            return JsonResponse({'error': 'Document is outside this user\'s storage.'}, status=status.HTTP_403_FORBIDDEN)

        _processor = DocumentProcessorAbstractClass.get_cloud_processor()
        _analysis_response = _processor.analyze_document(
            s3_uri,
            request.POST.get('type', ''),
            ''
        )
        document_url = _processor.save_document(
            _analysis_response,
            request.POST.get('type', ''),
            '',
            user_id=profile.user_id,
            image_url=s3_uri
        )
        return JsonResponse({'document_url': document_url})
        

class DocumentDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer
    #serializer_class = DocSerializer
    template_name = 'includes/expense_document_body.html'

    def get_queryset(self):
        return ExpenseRecord.objects.filter(user=self.request.user)
    
    def get_object(self):
        return _owned_document(self.request.user, self.kwargs.get('pk'))
        #return ExpenseDocument.objects.get()
    
    def destroy(self, request, pk, *args, **kwargs):
        return super().destroy(request, pk, *args, **kwargs)
    
    def update(self, request, pk, *args, **kwargs):
        try:
            super().update(request, pk, *args, **kwargs)
            document = self.get_object()
            return JsonResponse({
                'expense-line-item-id': pk, 
                'html': render_to_string(self.template_name, {'document': document})
            })
        except ValidationError as v:
            logger.error('Validation error updating document::[pk=%s]::[error=%s]', pk, v.detail)
            return Response({'errors': v.detail}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error('Error updating document::[pk=%s]', pk)
            logger.error(e.with_traceback())
            error = {messages.ERROR: ErrorMessages.DOCUMENT_UPDATE_FAILURE.value}
            return Response({'errors': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentListAPI(generics.ListAPIView):
    #serializer_class = DocumentSerializer
    serializer_class = DocSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExpenseDocument.objects.filter(user_id=self.request.user.id)

  
class DocumentTagAPI(mixins.CreateModelMixin, generics.RetrieveDestroyAPIView):
    """
    API for adding or deleting tags associated with a document
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentTagSerializer

    def get_queryset(self):
        document_ids = ExpenseRecord.objects.filter(user=self.request.user).values_list('id', flat=True)
        return DocumentTag.objects.filter(document__in=document_ids)
    
    def put(self, request, doc_pk, pk, *args, **kwargs):
        _owned_document(request.user, doc_pk)
        if pk is None or pk==0:
            res = self.create(request, doc_pk, *args, **kwargs)
            return JsonResponse({
                'id': res.data['id'],
                'text': res.data['text']
            })

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return JsonResponse({ 'id': kwargs.get('pk') })

class EmailRelayLogAPI(generics.CreateAPIView):
    """
    API to log an email relay
    """
    permission_classes = [HasAPIKey]
    serializer_class = EmailRelayLogSerializer
    

class EmailRelayUsernameAPI(APIView):
    """
    Availability check for the signed-in user choosing a relay name.
    Returns only a boolean. The user's own current name is treated as available.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, email_relay, format=None):
        try:
            EmailRelayUsernameValidator()(email_relay)
        except DjangoValidationError:
            return JsonResponse({'available': False})
        taken = Profile.objects.filter(
            email_relay__iexact=email_relay
        ).exclude(user=request.user).exists()
        return JsonResponse({'available': not taken})


class GoogleLogin(SocialLoginView): 
    """
    DJ-REST-AUTH Social login view to exchange authorization code for access token
    If you want to use Authorization Code Grant, use this
    """
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.REST_AUTH['GOOGLE_AUTH_CALLBACK']
    client_class = OAuth2Client


class ProfileAPI(generics.RetrieveUpdateAPIView):
    """
    API for retrieving and updating user profile
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    
    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)
    

class ProfileSearchAPI(generics.ListAPIView):
    """
    Exact relay lookup for the email Lambda. An empty search returns nothing.
    """
    permission_classes = [HasAPIKey]
    serializer_class = ProfileServiceSerializer

    def get_queryset(self):
        term = self.request.query_params.get('search', '').strip()
        if not term:
            return Profile.objects.none()
        return Profile.objects.filter(email_relay__iexact=term)


class ToggleDocumentFavoriteAPI(generics.UpdateAPIView):
    """
    API for toggling favorite status of document
    """
    serializer_class = DocumentSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        return ExpenseRecord.objects.filter(user=self.request.user)
    
    def put(self, request, *args, **kwargs):
        doc = _owned_document(request.user, kwargs.get('pk'))
        doc.is_favorite = not doc.is_favorite
        doc.save()
        return JsonResponse({
            'is_favorite': doc.is_favorite,
            'document_id': kwargs.get('pk')
        })


class ToggleDocumentReviewAPI(generics.UpdateAPIView):
    """
    API for toggling review status of document
    """
    serializer_class = DocumentSerializer
    permission_classes=[IsAuthenticated]
    
    def get_queryset(self):
        return ExpenseRecord.objects.filter(user=self.request.user)
    
    def put(self, request, *args, **kwargs):
        doc = _owned_document(request.user, kwargs.get('pk'))
        doc.review_status = not doc.review_status
        doc.save()
        return JsonResponse({
            'review_status': doc.review_status,
            'review_status_text': enums.DOCUMENT_REIVEW_STATUS_MAPPING.get(str(doc.review_status))
        })
    

class UploadDocumentAPI(APIView):
    """
    API to upload a single document to user storage bucket
    """
    permission_classes=[HasAPIKey]

    def post(self, request, format=None):
        profile = _service_profile(request.POST.get('user_id'))
        if profile is None or not profile.storage_bucket:
            return JsonResponse({'error': 'Unknown user.'}, status=status.HTTP_400_BAD_REQUEST)

        raw = request.POST.get('file', '')
        encoded = str(request.POST.get('base64encoded', '')).lower() in {'1', 'true', 'yes'}
        try:
            file_bytes = base64.b64decode(raw) if encoded else raw.encode()
        except (binascii.Error, ValueError, TypeError):
            return JsonResponse({'error': 'File could not be read.'}, status=status.HTTP_400_BAD_REQUEST)
        extension = normalize_upload_extension(request.POST.get('file_ext', ''))
        error = upload_bytes_error(file_bytes, extension)
        if error:
            return JsonResponse({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        _processor = DocumentProcessorAbstractClass.get_cloud_processor()
        s3_uri = _processor.upload_document(
            BytesIO(file_bytes),
            extension,
            profile.storage_bucket
        )
        if not s3_uri:
            return JsonResponse({'error': 'Upload failed.'}, status=status.HTTP_502_BAD_GATEWAY)
        return JsonResponse({'s3_uri': s3_uri})
        
