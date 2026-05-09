"""
Beauty Salon - All API Views

Architecture:
- JWT Authentication
- Frontend Cloudinary direct upload → backend stores URL
- Admin: is_staff=True users
- Customer: authenticated regular users
"""

import hashlib
import hmac
import time

import cloudinary
import cloudinary.uploader
import razorpay
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from project.permissions import IsOwnerOrAdmin, IsAdminOrReadOnly
from .filters import ServiceFilter, ProductFilter
from .models import (
    User, ServiceCategory, Service, ProductCategory, Product,
    Offer, TimeSlot, Booking, GalleryPhoto, Wishlist,
    Review, Notification, Coupon, Payment
)
from .serializers import (
    CustomTokenObtainPairSerializer, RegisterSerializer,
    UserProfileSerializer, ChangePasswordSerializer,
    ServiceCategorySerializer, ServiceListSerializer,
    ServiceDetailSerializer, ServiceWriteSerializer,
    ProductCategorySerializer, ProductListSerializer,
    ProductDetailSerializer, ProductWriteSerializer,
    OfferSerializer, OfferWriteSerializer,
    TimeSlotSerializer, BookingCreateSerializer,
    BookingListSerializer, BookingDetailSerializer,
    BookingStatusUpdateSerializer, GalleryPhotoSerializer,
    GalleryPhotoWriteSerializer, WishlistSerializer,
    ReviewSerializer, NotificationSerializer,
    CouponVerifySerializer, CouponSerializer,
    PaymentCreateSerializer, PaymentVerifySerializer,
    PaymentSerializer, CloudinarySignatureSerializer
)
from .utils import send_notification, generate_cloudinary_signature


# ─────────────────────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    Returns: { "access": "...", "refresh": "...", "user": {...} }
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Body: { username, email, first_name, last_name, phone, avatar_url, password, password2 }
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto-generate JWT after registration
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Body: { "refresh": "..." }
    Blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data['refresh'])
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/  → Get own profile
    PUT  /api/auth/profile/  → Update profile (avatar_url Cloudinary se milta hai)
    PATCH /api/auth/profile/ → Partial update
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/auth/change-password/"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Password changed successfully.'})


# ─────────────────────────────────────────────────────────────
# CLOUDINARY - FRONTEND DIRECT UPLOAD SUPPORT
# ─────────────────────────────────────────────────────────────

class CloudinarySignatureView(APIView):
    """
    GET /api/cloudinary/signature/?folder=services
    
    Flutter/JS frontend is endpoint se signed params leta hai,
    phir seedha Cloudinary pe upload karta hai.
    Backend ko sirf final URL submit karna hota hai.
    
    Flow:
    1. Frontend → GET /api/cloudinary/signature/?folder=gallery
    2. Backend → Returns { signature, timestamp, api_key, cloud_name, folder }
    3. Frontend → POST directly to Cloudinary with file + these params
    4. Cloudinary → Returns { secure_url, public_id, ... }
    5. Frontend → POST/PUT to backend with only the secure_url
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CloudinarySignatureSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        folder = serializer.validated_data['folder']
        timestamp = int(time.time())

        # Generate signature for direct upload
        signature = generate_cloudinary_signature(folder, timestamp)

        return Response({
            'signature': signature,
            'timestamp': timestamp,
            'api_key': settings.CLOUDINARY_API_KEY,
            'cloud_name': settings.CLOUDINARY_CLOUD_NAME,
            'folder': folder,
            'upload_url': f'https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/image/upload',
        })


# ─────────────────────────────────────────────────────────────
# SERVICE VIEWS
# ─────────────────────────────────────────────────────────────

class ServiceCategoryListView(generics.ListCreateAPIView):
    """
    GET  /api/services/categories/        → All categories (public)
    POST /api/services/categories/        → Create (admin only)
    """
    queryset = ServiceCategory.objects.filter(is_active=True)
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class ServiceCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/services/categories/<id>/
    PUT    /api/services/categories/<id>/  (admin)
    DELETE /api/services/categories/<id>/  (admin)
    """
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ServiceListView(generics.ListCreateAPIView):
    """
    GET  /api/services/
    Filters: category, is_featured, min_price, max_price
    Search: name, description
    Ordering: original_price, discount_percent, created_at
    
    POST /api/services/  → Admin creates service
    image_url = Cloudinary URL (frontend uploaded)
    """
    queryset = Service.objects.filter(is_active=True).select_related('category')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ServiceFilter
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['original_price', 'discount_percent', 'created_at', 'name']
    ordering = ['-is_featured', 'name']
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ServiceWriteSerializer
        return ServiceListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Admin sabke dekh sakta hai including inactive
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Service.objects.all().select_related('category')
        return qs


class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/services/<id>/     → Full detail with reviews & gallery
    PUT    /api/services/<id>/     → Admin update
    PATCH  /api/services/<id>/     → Admin partial update
    DELETE /api/services/<id>/     → Admin delete
    """
    queryset = Service.objects.all().select_related('category')
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ServiceWriteSerializer
        return ServiceDetailSerializer


class FeaturedServicesView(generics.ListAPIView):
    """GET /api/services/featured/ → Home screen featured services."""
    queryset = Service.objects.filter(is_active=True, is_featured=True).select_related('category')
    serializer_class = ServiceListSerializer
    permission_classes = [AllowAny]


# ─────────────────────────────────────────────────────────────
# PRODUCT VIEWS
# ─────────────────────────────────────────────────────────────

class ProductCategoryListView(generics.ListCreateAPIView):
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductListView(generics.ListCreateAPIView):
    """
    GET  /api/products/
    Filters: category, is_featured, min_price, max_price, in_stock
    
    POST /api/products/  → Admin creates product
    image_url aur image_urls = Cloudinary URLs
    """
    queryset = Product.objects.filter(is_active=True).select_related('category')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'brand', 'category__name']
    ordering_fields = ['original_price', 'discount_percent', 'created_at', 'name']
    ordering = ['-is_featured', 'name']
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductWriteSerializer
        return ProductListSerializer


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all().select_related('category')
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ProductWriteSerializer
        return ProductDetailSerializer


class FeaturedProductsView(generics.ListAPIView):
    """GET /api/products/featured/ → Home screen featured products."""
    queryset = Product.objects.filter(is_active=True, is_featured=True)
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]


# ─────────────────────────────────────────────────────────────
# OFFER / BANNER VIEWS
# ─────────────────────────────────────────────────────────────

class OfferListView(generics.ListCreateAPIView):
    """
    GET  /api/offers/          → Active offers (public, home screen)
    POST /api/offers/          → Admin creates offer (image_url = Cloudinary)
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        now = timezone.now()
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return Offer.objects.all()
        return Offer.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('order')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OfferWriteSerializer
        return OfferSerializer


class OfferDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Offer.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return OfferWriteSerializer
        return OfferSerializer


# ─────────────────────────────────────────────────────────────
# BOOKING VIEWS
# ─────────────────────────────────────────────────────────────

class TimeSlotListView(generics.ListAPIView):
    """GET /api/bookings/slots/ → Available time slots."""
    queryset = TimeSlot.objects.filter(is_active=True)
    serializer_class = TimeSlotSerializer
    permission_classes = [AllowAny]


class AvailableSlotsView(APIView):
    """
    GET /api/bookings/available-slots/?service_id=1&date=2024-12-25
    Returns slots not already booked for this service+date.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        service_id = request.query_params.get('service_id')
        date = request.query_params.get('date')

        if not service_id or not date:
            return Response(
                {'error': 'service_id and date are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booked_slots = Booking.objects.filter(
            service_id=service_id,
            booking_date=date,
            status__in=['pending', 'confirmed']
        ).values_list('time_slot_id', flat=True)

        available = TimeSlot.objects.filter(is_active=True).exclude(id__in=booked_slots)
        return Response(TimeSlotSerializer(available, many=True).data)


class BookingCreateView(generics.CreateAPIView):
    """
    POST /api/bookings/
    Body: { service, booking_date, time_slot, coupon (optional), notes }
    """
    serializer_class = BookingCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        booking = serializer.save()
        # Send notification
        send_notification(
            user=booking.user,
            title='Booking Received!',
            message=f'Your booking for {booking.service.name} on {booking.booking_date} is pending confirmation.',
            notification_type='booking_confirmed',
            booking=booking
        )


class UserBookingListView(generics.ListAPIView):
    """GET /api/bookings/my/ → Logged-in user ke apne bookings."""
    serializer_class = BookingListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering = ['-created_at']

    def get_queryset(self):
        return Booking.objects.filter(
            user=self.request.user
        ).select_related('service', 'time_slot')


class UserBookingDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/bookings/my/<id>/    → Booking detail
    DELETE /api/bookings/my/<id>/    → Cancel booking
    """
    serializer_class = BookingDetailSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status in ['completed', 'cancelled']:
            return Response(
                {'error': f'Cannot cancel a {booking.status} booking.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        booking.status = 'cancelled'
        booking.save()
        return Response({'message': 'Booking cancelled successfully.'})


# Admin Booking Management
class AdminBookingListView(generics.ListAPIView):
    """GET /api/admin/bookings/ → All bookings (admin)."""
    serializer_class = BookingListSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'booking_date', 'service']
    search_fields = ['user__username', 'user__phone', 'service__name']
    ordering = ['-created_at']
    queryset = Booking.objects.all().select_related('user', 'service', 'time_slot')


class AdminBookingUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/admin/bookings/<id>/status/
    Body: { "status": "confirmed" | "rejected" | "completed", "admin_notes": "..." }
    """
    serializer_class = BookingStatusUpdateSerializer
    permission_classes = [IsAdminUser]
    queryset = Booking.objects.all()

    def perform_update(self, serializer):
        booking = serializer.save()
        # Notify user of status change
        msg_map = {
            'confirmed': f'Your booking for {booking.service.name} on {booking.booking_date} is confirmed!',
            'rejected': f'Your booking for {booking.service.name} was not accepted. Reason: {booking.admin_notes}',
            'completed': f'Your appointment for {booking.service.name} is completed. Thank you!',
        }
        if booking.status in msg_map:
            send_notification(
                user=booking.user,
                title=f'Booking {booking.status.title()}',
                message=msg_map[booking.status],
                notification_type=f'booking_{booking.status}',
                booking=booking
            )


# ─────────────────────────────────────────────────────────────
# GALLERY VIEWS
# ─────────────────────────────────────────────────────────────

class GalleryListView(generics.ListAPIView):
    """
    GET /api/gallery/
    Filters: category, service, is_featured
    """
    queryset = GalleryPhoto.objects.filter(is_active=True).select_related('service')
    serializer_class = GalleryPhotoSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['category', 'service', 'is_featured']
    ordering = ['-is_featured', '-created_at']


class GalleryCreateView(generics.CreateAPIView):
    """
    POST /api/gallery/
    Admin uploads gallery photo.
    Body: { title, category, before_image_url, after_image_url, service }
    before_image_url & after_image_url = Cloudinary URLs from frontend upload
    """
    serializer_class = GalleryPhotoWriteSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class GalleryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GalleryPhoto.objects.all()
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return GalleryPhotoWriteSerializer
        return GalleryPhotoSerializer


# ─────────────────────────────────────────────────────────────
# WISHLIST VIEWS
# ─────────────────────────────────────────────────────────────

class WishlistView(generics.ListCreateAPIView):
    """
    GET  /api/wishlist/     → User ke wishlist items
    POST /api/wishlist/     → Add to wishlist { service: 1 } or { product: 1 }
    """
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related(
            'service', 'product'
        )


class WishlistDeleteView(generics.DestroyAPIView):
    """DELETE /api/wishlist/<id>/ → Remove from wishlist."""
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


# ─────────────────────────────────────────────────────────────
# REVIEW VIEWS
# ─────────────────────────────────────────────────────────────

class ReviewCreateView(generics.CreateAPIView):
    """
    POST /api/reviews/
    Body: { service OR product, rating (1-5), comment }
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]


class ReviewListView(generics.ListAPIView):
    """
    GET /api/reviews/?service=1  → Service reviews
    GET /api/reviews/?product=1  → Product reviews
    """
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['service', 'product', 'rating']
    ordering = ['-created_at']

    def get_queryset(self):
        return Review.objects.filter(is_approved=True).select_related('user')


# ─────────────────────────────────────────────────────────────
# NOTIFICATION VIEWS
# ─────────────────────────────────────────────────────────────

class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/ → User ke notifications."""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationMarkReadView(APIView):
    """
    POST /api/notifications/mark-read/
    Body: { "ids": [1, 2, 3] } or {} (all)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ids = request.data.get('ids', [])
        qs = Notification.objects.filter(user=request.user)
        if ids:
            qs = qs.filter(id__in=ids)
        count = qs.update(is_read=True)
        return Response({'marked_read': count})


class UnreadNotificationCountView(APIView):
    """GET /api/notifications/unread-count/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


# ─────────────────────────────────────────────────────────────
# COUPON VIEWS
# ─────────────────────────────────────────────────────────────

class CouponVerifyView(APIView):
    """
    POST /api/coupons/verify/
    Body: { "code": "SAVE20", "amount": 500.00 }
    Returns: { coupon details, discount_amount, final_amount }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        coupon = data['coupon']

        return Response({
            'valid': True,
            'coupon_id': coupon.id,
            'code': coupon.code,
            'description': coupon.description,
            'discount_type': coupon.discount_type,
            'discount_value': str(coupon.discount_value),
            'discount_amount': data['discount_amount'],
            'final_amount': data['final_amount'],
        })


# Admin coupon management
class AdminCouponListView(generics.ListCreateAPIView):
    """GET/POST /api/admin/coupons/"""
    queryset = Coupon.objects.all().order_by('-created_at')
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]


class AdminCouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/admin/coupons/<id>/"""
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]


# ─────────────────────────────────────────────────────────────
# PAYMENT VIEWS (Razorpay)
# ─────────────────────────────────────────────────────────────

class PaymentCreateView(APIView):
    """
    DEMO PAYMENT
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        serializer.is_valid(raise_exception=True)

        booking = Booking.objects.get(
            id=serializer.validated_data['booking_id']
        )

        payment, created = Payment.objects.get_or_create(
            booking=booking,
            defaults={
                'user': request.user,
                'amount': booking.total_amount,
                'status': 'created'
            }
        )

        return Response({
            'success': True,
            'payment_type': 'demo',
            'booking_id': booking.id,
            'amount': booking.total_amount,
            'message': 'Demo payment created successfully.'
        })


class PaymentVerifyView(APIView):
    """
    DEMO PAYMENT VERIFY
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        booking_id = request.data.get('booking_id')

        if not booking_id:
            return Response({
                'error': 'booking_id is required'
            }, status=400)

        try:
            booking = Booking.objects.get(
                id=booking_id,
                user=request.user
            )

            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'user': request.user,
                    'amount': booking.total_amount
                }
            )

            payment.status = 'paid'
            payment.save()

            booking.status = 'confirmed'
            booking.save()

            send_notification(
                user=request.user,
                title='Demo Payment Successful ✅',
                message=f'Your booking for {booking.service.name} is confirmed.',
                notification_type='booking_confirmed',
                booking=booking
            )

            return Response({
                'success': True,
                'payment_status': 'paid',
                'booking_status': 'confirmed',
                'message': 'Demo payment successful.'
            })

        except Booking.DoesNotExist:
            return Response({
                'error': 'Booking not found.'
            }, status=404)

# ─────────────────────────────────────────────────────────────
# HOME SCREEN DATA
# ─────────────────────────────────────────────────────────────

class HomeScreenView(APIView):
    """
    GET /api/home/
    Single endpoint for home screen:
    - Active banners/offers
    - Featured services
    - Featured products
    - Featured gallery photos
    
    Flutter/Web ek hi call mein home screen data le sakta hai.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()

        # Active offers/banners
        offers = Offer.objects.filter(
            is_active=True, start_date__lte=now, end_date__gte=now
        ).order_by('order')[:5]

        # Featured services
        featured_services = Service.objects.filter(
            is_active=True, is_featured=True
        ).select_related('category')[:6]

        # Featured products
        featured_products = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related('category')[:6]

        # Featured gallery
        gallery = GalleryPhoto.objects.filter(
            is_active=True, is_featured=True
        )[:4]

        return Response({
            'banners': OfferSerializer(offers, many=True).data,
            'featured_services': ServiceListSerializer(featured_services, many=True).data,
            'featured_products': ProductListSerializer(featured_products, many=True).data,
            'gallery_preview': GalleryPhotoSerializer(gallery, many=True).data,
        })


# ─────────────────────────────────────────────────────────────
# ADMIN DASHBOARD STATS
# ─────────────────────────────────────────────────────────────

class AdminDashboardView(APIView):
    """GET /api/admin/dashboard/ → Quick stats for admin panel."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        return Response({
            'total_users': User.objects.filter(is_staff=False).count(),
            'total_bookings': Booking.objects.count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'today_bookings': Booking.objects.filter(booking_date=today).count(),
            'total_services': Service.objects.filter(is_active=True).count(),
            'total_products': Product.objects.filter(is_active=True).count(),
            'active_offers': Offer.objects.filter(
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).count(),
        })


# Admin User Management
class AdminUserListView(generics.ListAPIView):
    """GET /api/admin/users/ → All users."""
    queryset = User.objects.filter(is_staff=False).order_by('-date_joined')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/admin/users/<id>/"""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]