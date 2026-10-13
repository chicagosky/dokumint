import logging
from io import BytesIO

from allauth.account.views import PasswordChangeView
from cloudpathlib import S3Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.forms import modelform_factory
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, View
from django.views.generic.edit import FormMixin
from view_breadcrumbs import DetailBreadcrumbMixin

from core.forms import UploadDocumentForm
from core.messages import ErrorMessages
from core.models import Document, DocumentType, Profile
from core.processors.cloud_processors import DocumentProcessorAbstractClass
from core.utils import get_app_setting, get_file_extension, get_file_type

logger = logging.getLogger(settings.DOKUMINT_SETTINGS["default"]["logger"])

class DocumentDetailView(LoginRequiredMixin, DetailView, DeleteView):
    """
    """
    model = Document
    template_name = '' #TODO: assign default template for documents
    excluded_data = ['csrfmiddlewaretoken']
    response_data = {}

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)
        context['types'] = DocumentType.objects.all()
        return context
    
    def get_object(self):
        return self.model.objects.get(user=self.request.user, pk=self.kwargs.get('pk'))
    
    def get(self, request, *args, **kwargs):
        self._set_template_name()
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        try:
            _document = Document.objects.get(user=request.user, pk=kwargs['pk'])
            _document.delete()
        except ObjectDoesNotExist as o:
            logger.error('Error loading document::[user_id=%s]::[kwargs=%s]',request.user.id,kwargs)
        except Exception as e:
            logger.error('Error downloading document image::[user_id=%s]::[kwargs=%s]',request.user.id,kwargs)
            logger.error(e)

        return redirect('core:documents')
    
    def _set_template_name(self, **kwargs):
        """
        Determines the template to be used based on document type
        """
        doc = self.get_object()
        self.template_name = doc.type.detail_template


class DocumentImageView(LoginRequiredMixin, View):
    model = Document

    def get(self, request, *args, **kwargs):
        image_file = BytesIO() # TODO: Set a default image in the bytes stream
        try:
            _document = Document.objects.get(user=request.user, pk=kwargs['pk'])
            _s3_uri = S3Path(_document.image_url)
            _image_name = _s3_uri.key
            _bucket = _s3_uri.bucket
            _processor = DocumentProcessorAbstractClass.get_cloud_processor()
            _processor.download_document_to_stream(_image_name, _bucket, image_file)
        except ObjectDoesNotExist as o:
            logger.error('Error loading document::[user_id=%s]::[kwargs=%s]',request.user.id,kwargs)
        except Exception as e:
            logger.error('Error downloading document image::[user_id=%s]::[kwargs=%s]',request.user.id,kwargs)
            logger.error(e)

        return HttpResponse(image_file.getvalue(), content_type=get_file_type(image_file)) 


class DocumentListView(FormMixin, LoginRequiredMixin, ListView):
    context_object_name = "documents"
    form_class = UploadDocumentForm
    model = Document
    paginate_by = get_app_setting('', 'default.page_size')
    template_name = "documents_list.html"

    def get_context_data(self, **kwargs):
        _context = super().get_context_data(**kwargs)
        _types = DocumentType.objects.all()
        _context['types'] = _types
        return _context
    
    def get_queryset(self):
        qs = super(DocumentListView, self).get_queryset().filter(user=self.request.user)
        qs = qs.filter(type=self.kwargs.get('type')) if self.kwargs.get('type') is not None else qs
        return qs

    def get(self, request, *args, **kwargs):
        # From FormMixin
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        # From ListView
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list, form=self.form)
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        form = UploadDocumentForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                _document = request.FILES['upload_file']
                _extension = get_file_extension(_document.name)
                _type = request.POST.get('document_type', 'EXP')

                # Upload document
                _bucket = request.user.profile.storage_bucket
                _processor = DocumentProcessorAbstractClass.get_cloud_processor()
                _s3_uri = _processor.upload_document(_document, _extension, _bucket)

                # Analyze document
                _analysis_response = _processor.analyze_document(_s3_uri, _type, '')
                
                # Save document
                document_url = _processor.save_document(
                    _analysis_response, 
                    _type, 
                    '', 
                    user_id=request.user.id, 
                    image_url=_s3_uri
                )
                return redirect(document_url)
        except Exception as e:
            logger.error('Error uploading document::[user_id=%s]', request.user.id)
            logger.exception(e)
            messages.add_message(request, messages.ERROR, ErrorMessages.DOCUMENT_UPLOAD_FAILURE.value)

        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list, form=form)
        return self.render_to_response(context)
    

class DokumintPasswordChangeView(PasswordChangeView):
    template_name = 'account/profile.html'

    def get_success_url(self):
        return reverse_lazy('core:account-profile', kwargs={"pk": self.request.user.id})


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = "account/profile.html"
    allowed_profile_fields = ('postal_code', 'email_relay', 'notifications_allowed', 'analytics_allowed')
    allowed_user_fields = ('first_name', 'last_name')

    def get_object(self, queryset=None):
        return Profile.objects.get(user=self.request.user)

    def post(self, request, *args, **kwargs):
        profile_fields = [name for name in self.allowed_profile_fields if name in request.POST]
        user_fields = [name for name in self.allowed_user_fields if name in request.POST]
        profile = Profile.objects.get(user=request.user)
        profile_form = None
        user_form = None
        if profile_fields:
            ProfileForm = modelform_factory(Profile, fields=profile_fields)
            profile_form = ProfileForm(request.POST, instance=profile)
        if user_fields:
            UserForm = modelform_factory(User, fields=user_fields)
            user_form = UserForm(request.POST, instance=request.user)

        if profile_form is None and user_form is None:
            messages.add_message(request, messages.ERROR, ErrorMessages.USER_PROFILE_UPDATE_FAILURE.value)
            return redirect('core:account-profile', request.user.id)

        try:
            profile_valid = profile_form is None or profile_form.is_valid()
            user_valid = user_form is None or user_form.is_valid()
            if profile_valid and user_valid:
                if profile_form is not None:
                    profile_form.save()
                if user_form is not None:
                    user_form.save()
                return redirect('core:account-profile', request.user.id)
        except Exception as e:
            logger.error('Error updating user profile::[user_id=%s]', request.user.id)
            logger.exception(e)

        if profile_form is not None:
            for field in profile_form.errors:
                messages.add_message(request, messages.ERROR, profile_form.errors[field])
        if user_form is not None:
            for field in user_form.errors:
                messages.add_message(request, messages.ERROR, user_form.errors[field])
        return render(request, self.template_name, {'profile': profile, 'object': profile})
