"""
Custom Permission Classes
- IsAdminUser: Sirf admin panel wale users ke liye
- IsOwnerOrAdmin: Object ka owner ya admin access kar sake
- IsCustomerOrAdmin: Authenticated user ya admin
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """Sirf is_staff=True users ko allow karta hai."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: sirf object ka owner ya admin.
    GET (read) sabke liye allowed hai.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # obj.user field check karta hai
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Read operations (GET, HEAD, OPTIONS) sabke liye.
    Write operations sirf authenticated users ke liye.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)


class IsAdminOrReadOnly(BasePermission):
    """
    Read: sabke liye.
    Write (POST/PUT/DELETE): sirf admin.
    Services, Products, Offers ke liye useful.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)