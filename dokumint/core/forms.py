from django import forms
from django.contrib.auth.models import User
from django.forms import ModelForm
from upload_validator import FileTypeValidator

from core.models import Profile

ALLOWED_UPLOAD_EXTENSIONS = {'.jpeg', '.jpg', '.png', '.pdf'}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_UPLOAD_SIGNATURES = {
    '.pdf': (b'%PDF',),
    '.jpg': (b'\xff\xd8\xff',),
    '.jpeg': (b'\xff\xd8\xff',),
    '.png': (b'\x89PNG\r\n\x1a\n',),
}

file_ext_validator = FileTypeValidator(
    allowed_types=['application/pdf', 'image/jpeg', 'image/png'],
    allowed_extensions=['.jpeg', '.jpg', '.png', '.pdf']
)

def normalize_upload_extension(ext):
    ext = (ext or '').lower().strip()
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    return ext

def upload_bytes_error(data, ext):
    """Return an error message when uploaded bytes are not an allowed receipt file."""
    ext = normalize_upload_extension(ext)
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return 'Unsupported file type.'
    if not data or len(data) > MAX_UPLOAD_BYTES:
        return 'File is empty or larger than 20 MB.'
    if not any(data.startswith(signature) for signature in _UPLOAD_SIGNATURES[ext]):
        return 'File contents do not match the extension.'
    return None

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['postal_code']

class UploadDocumentForm(forms.Form):
    upload_file = forms.FileField(
        help_text="Accepted formats are JPG, JPEG, PDF or PNG", 
        validators=[file_ext_validator],
        widget=forms.FileInput()
    )

    class Meta:
        fields = ["upload_file"]

class UpdateUserForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']