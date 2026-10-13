from django.urls import include, path
from core.views import DocumentDetailView, DocumentListView, DocumentImageView, DokumintPasswordChangeView
from core.views import ProfileDetailView

urlpatterns = [
    # Documents
    path('', DocumentListView.as_view(), name='documents'),
    path('documents/', DocumentListView.as_view(), name='document_list'),
    path('document/<uuid:pk>', DocumentDetailView.as_view(), name='document_detail'),
    path('document/<uuid:pk>/image', DocumentImageView.as_view(), name='document-image'),
    path('document/<uuid:pk>/delete/', DocumentDetailView.as_view(), name='delete-document'),

    # Profile
    path('password/change/', DokumintPasswordChangeView.as_view(), name='account-change-password'),
    path('profile/<int:pk>', ProfileDetailView.as_view(), name='account-profile'), 

    # APIs
    path('api/', include('core.api.urls'))
]