"""
Beauty Salon - Admin Panel Configuration
Sab models admin mein register hain with proper list views and filters.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
    User, ServiceCategory, Service, ProductCategory, Product,
    Offer, TimeSlot, Booking, GalleryPhoto, Wishlist,
    Review, Notification, Coupon, Payment
)

admin.site.site_header = "Beauty Salon Admin"
admin.site.site_title = "Beauty Salon"
admin.site.index_title = "Dashboard"


# ─── USER ──────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Extra Info', {'fields': ('phone', 'avatar_url', 'fcm_token')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Extra Info', {'fields': ('phone', 'avatar_url')}),
    )


# ─── SERVICES ──────────────────────────────────────────────────

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'original_price', 'discount_percent',
        'get_discounted_price', 'duration_minutes', 'is_featured', 'is_active'
    ]
    list_filter = ['category', 'is_featured', 'is_active']
    list_editable = ['is_featured', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-is_featured', 'name']

    def get_discounted_price(self, obj):
        return f"₹{obj.discounted_price}"
    get_discounted_price.short_description = 'Final Price'


# ─── PRODUCTS ──────────────────────────────────────────────────

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_editable = ['is_active']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'brand', 'category', 'original_price', 'discount_percent',
        'stock', 'is_featured', 'is_active'
    ]
    list_filter = ['category', 'is_featured', 'is_active']
    list_editable = ['is_featured', 'is_active', 'stock']
    search_fields = ['name', 'brand', 'description']


# ─── OFFERS ────────────────────────────────────────────────────

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'offer_type', 'discount_percent', 'start_date', 'end_date', 'is_active', 'order']
    list_filter = ['offer_type', 'is_active']
    list_editable = ['is_active', 'order']
    search_fields = ['title', 'description']


# ─── BOOKINGS ──────────────────────────────────────────────────

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['start_time', 'end_time', 'is_active']
    list_editable = ['is_active']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'service', 'booking_date', 'time_slot',
        'status', 'total_amount', 'created_at'
    ]
    list_filter = ['status', 'booking_date', 'service']
    search_fields = ['user__username', 'user__email', 'user__phone', 'service__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['confirm_bookings', 'reject_bookings']

    def confirm_bookings(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{updated} bookings confirmed.')
    confirm_bookings.short_description = 'Confirm selected bookings'

    def reject_bookings(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(request, f'{updated} bookings rejected.')
    reject_bookings.short_description = 'Reject selected bookings'


# ─── GALLERY ───────────────────────────────────────────────────

@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category', 'service', 'is_featured', 'is_active', 'created_at']
    list_filter = ['category', 'is_featured', 'is_active']
    list_editable = ['is_featured', 'is_active']
    search_fields = ['title']

    def preview(self, obj):
        if obj.after_image_url:
            return format_html('<img src="{}" height="50"/>', obj.after_image_url)
        return '-'
    preview.short_description = 'After'


# ─── REVIEWS ───────────────────────────────────────────────────

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'product', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved']
    list_editable = ['is_approved']
    search_fields = ['user__username', 'comment']


# ─── NOTIFICATIONS ─────────────────────────────────────────────

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']
    search_fields = ['user__username', 'title', 'message']


# ─── COUPONS ───────────────────────────────────────────────────

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'minimum_order',
        'used_count', 'usage_limit', 'valid_from', 'valid_till', 'is_active'
    ]
    list_filter = ['discount_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['code', 'description']


# ─── PAYMENTS ──────────────────────────────────────────────────

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'booking', 'amount', 'status',
        'razorpay_order_id', 'razorpay_payment_id', 'created_at'
    ]
    list_filter = ['status', 'currency']
    search_fields = ['user__username', 'razorpay_order_id', 'razorpay_payment_id']
    readonly_fields = ['created_at', 'updated_at']


# Wishlist (basic)
admin.site.register(Wishlist)