from django.urls import path
from core.api.views import AnalyzeDocumentAPI, DocumentListAPI, DocumentDetailAPI
from core.api.views import DocumentTagAPI
from core.api.views import EmailRelayLogAPI, EmailRelayUsernameAPI, ProfileAPI, ProfileSearchAPI
from core.api.views import AnalyzeDocumentAPI, DocumentListAPI, DocumentDetailAPI
from core.api.views import ToggleDocumentFavoriteAPI, ToggleDocumentReviewAPI, UploadDocumentAPI

urlpatterns = [
    # Documents
    path('analyze-document/', AnalyzeDocumentAPI.as_view(), name='analyze-document'),
    path('documents/', DocumentListAPI.as_view(), name='document-list-json'),
    path('document/<uuid:pk>/', DocumentDetailAPI.as_view(), name='document-detail-api'), # View / Edit Document details
    path('document/<uuid:pk>/favorite/', ToggleDocumentFavoriteAPI.as_view(), name='toggle-document-favorite-api'), # Toggle Document Favorite status
    path('document/<uuid:pk>/review/', ToggleDocumentReviewAPI.as_view(), name='toggle-document-review-api'), # Toggle Document review status
    path('document/<uuid:doc_pk>/tag/<int:pk>/', DocumentTagAPI.as_view(), name='document-tag-api'), # Add document tag
    
    # Email Relay APIs
    # log/ must be registered before the username pattern, which would otherwise capture "log".
    path('email-relay/log/', EmailRelayLogAPI.as_view(), name='email-relay-log'),
    path('email-relay/<str:email_relay>', EmailRelayUsernameAPI.as_view(), name='email-relay-username'),

    # Upload a document
    path('upload-document/', UploadDocumentAPI.as_view(), name='upload-document'),

    # User Profile 
    path('profile/<int:pk>', ProfileAPI.as_view(), name='profile-detail-api'),
    path('profiles', ProfileSearchAPI.as_view(), name='profile-search-api'),
]