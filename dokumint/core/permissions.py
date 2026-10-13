from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    """
    Object level permissions that allow only owners of Objects (Documents etc.)
    to view, edit them
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
    