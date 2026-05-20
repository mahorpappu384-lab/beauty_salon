"""
Beauty Salon API - URL Routes

All routes start with /api/ (defined in project/urls.py)

Auth:
  POST   /api/auth/login/
  POST   /api/auth/register/
  POST   /api/auth/logout/
  GET    /api/auth/profile/
  PUT    /api/auth/profile/
  POST   /api/auth/change-password/
  POST   /api/auth/token/refresh/

Cloudinary:
  GET    /api/cloudinary/signature/?folder=services

Home:
  GET    /api/home/

Services:
  GET    /api/services/
  POST   /api/services/                   (admin)
  GET    /api/services/featured/
  GET    /api/services/categories/
  GET    /api/services/<id>/
  PUT    /api/services/<id>/              (admin)
  DELETE /api/services/<id>/             (admin)

Products:
  GET    /api/products/
  POST   /api/products/                   (admin)
  GET    /api/products/featured/
  GET    /api/products/categories/
  GET    /api/products/<id>/

Offers:
  GET    /api/offers/
  POST   /api/offers/                     (admin)
  GET    /api/offers/<id>/
  PATCH  /api/offers/<id>/               (admin)

Bookings:
  GET    /api/bookings/slots/
  GET    /api/bookings/available-slots/?service_id=1&date=2024-12-25
  POST   /api/bookings/
  GET    /api/bookings/my/
  GET    /api/bookings/my/<id>/
  DELETE /api/bookings/my/<id>/          (cancel)

Gallery:
  GET    /api/gallery/
  POST   /api/gallery/                   (admin)
  GET    /api/gallery/<id>/
  PATCH  /api/gallery/<id>/             (admin)
  DELETE /api/gallery/<id>/             (admin)

Wishlist:
  GET    /api/wishlist/
  POST   /api/wishlist/
  DELETE /api/wishlist/<id>/

Reviews:
  GET    /api/reviews/
  POST   /api/reviews/

Notifications:
  GET    /api/notifications/
  POST   /api/notifications/mark-read/
  GET    /api/notifications/unread-count/

Coupons:
  POST   /api/coupons/verify/

Payments:
  POST   /api/payments/create/
  POST   /api/payments/verify/

Admin:
  GET    /api/admin/dashboard/
  GET    /api/admin/users/
  GET    /api/admin/users/<id>/
  GET    /api/admin/bookings/
  PATCH  /api/admin/bookings/<id>/status/
  GET    /api/admin/coupons/
  POST   /api/admin/coupons/
  GET    /api/admin/coupons/<id>/

Docs:
  GET    /api/docs/          (Swagger UI)
  GET    /api/redoc/         (ReDoc)
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [

    # ─── AUTH ─────────────────────────────────────────────────
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('auth/profile/', views.ProfileView.as_view(), name='auth-profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ─── CLOUDINARY DIRECT UPLOAD ─────────────────────────────
    path('cloudinary/signature/', views.CloudinarySignatureView.as_view(), name='cloudinary-signature'),

    # ─── HOME SCREEN ──────────────────────────────────────────
    path('home/', views.HomeScreenView.as_view(), name='home'),
    # urls.py mein yeh line add karo

    path('home/splash/', views.SplashUpdateView.as_view(), name='splash-update'),
    path('health/', views.HealthView.as_view(), name='health'),
    path('auth/send-otp/', views.SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    # Address URLs
    path('orders/addresses/', views.AddressListCreateView.as_view(), name='address-list'),
    path('orders/addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('orders/addresses/<int:pk>/set-default/', views.AddressSetDefaultView.as_view(), name='address-set-default'),

# Order URLs
    path('orders/', views.ProductOrderCreateView.as_view(), name='product-order-create'),
    path('orders/my/', views.MyOrderListView.as_view(), name='my-orders'),
    path('orders/my/<int:pk>/', views.MyOrderDetailView.as_view(), name='my-order-detail'),
    path('orders/my/<int:pk>/cancel/', views.CancelOrderView.as_view(), name='order-cancel'),
    path('orders/my/<int:pk>/return/', views.ReturnOrderView.as_view(), name='order-return'),

# Admin
    path('admin/orders/', views.AdminOrderListView.as_view(), name='admin-orders'),
    path('admin/orders/<int:pk>/', views.AdminOrderDetailView.as_view(), name='admin-order-detail'),   # ← Naya
    path('admin/orders/<int:pk>/status/', views.AdminOrderUpdateView.as_view(), name='admin-order-status'),

    # ─── SERVICES ─────────────────────────────────────────────
    path('services/', views.ServiceListView.as_view(), name='service-list'),
    path('services/featured/', views.FeaturedServicesView.as_view(), name='service-featured'),
    path('services/categories/', views.ServiceCategoryListView.as_view(), name='service-category-list'),
    path('services/categories/<int:pk>/', views.ServiceCategoryDetailView.as_view(), name='service-category-detail'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service-detail'),

    # ─── PRODUCTS ─────────────────────────────────────────────
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/featured/', views.FeaturedProductsView.as_view(), name='product-featured'),
    path('products/categories/', views.ProductCategoryListView.as_view(), name='product-category-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    # ─── OFFERS / BANNERS ─────────────────────────────────────
    path('offers/', views.OfferListView.as_view(), name='offer-list'),
    path('offers/<int:pk>/', views.OfferDetailView.as_view(), name='offer-detail'),

    # ─── BOOKINGS ─────────────────────────────────────────────
    path('bookings/slots/', views.TimeSlotListView.as_view(), name='time-slots'),
    path('bookings/available-slots/', views.AvailableSlotsView.as_view(), name='available-slots'),
    path('bookings/', views.BookingCreateView.as_view(), name='booking-create'),
    path('bookings/my/', views.UserBookingListView.as_view(), name='my-bookings'),
    path('bookings/my/<int:pk>/', views.UserBookingDetailView.as_view(), name='my-booking-detail'),

    # ─── GALLERY ──────────────────────────────────────────────
    path('gallery/', views.GalleryListView.as_view(), name='gallery-list'),
    path('gallery/add/', views.GalleryCreateView.as_view(), name='gallery-create'),
    path('gallery/<int:pk>/', views.GalleryDetailView.as_view(), name='gallery-detail'),

    # ─── WISHLIST ─────────────────────────────────────────────
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:pk>/', views.WishlistDeleteView.as_view(), name='wishlist-delete'),

    # ─── REVIEWS ──────────────────────────────────────────────
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/add/', views.ReviewCreateView.as_view(), name='review-create'),

    # ─── NOTIFICATIONS ────────────────────────────────────────
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/', views.NotificationMarkReadView.as_view(), name='notifications-mark-read'),
    path('notifications/unread-count/', views.UnreadNotificationCountView.as_view(), name='notifications-unread'),

    # ─── COUPONS ──────────────────────────────────────────────
    path('coupons/verify/', views.CouponVerifyView.as_view(), name='coupon-verify'),

    # ─── PAYMENTS (Razorpay) ──────────────────────────────────
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('payments/verify/', views.PaymentVerifyView.as_view(), name='payment-verify'),

    # ─── ADMIN PANEL ──────────────────────────────────────────
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/bookings/', views.AdminBookingListView.as_view(), name='admin-bookings'),
    path('admin/bookings/<int:pk>/status/', views.AdminBookingUpdateView.as_view(), name='admin-booking-status'),
    path('admin/coupons/', views.AdminCouponListView.as_view(), name='admin-coupons'),
    path('admin/coupons/<int:pk>/', views.AdminCouponDetailView.as_view(), name='admin-coupon-detail'),
]