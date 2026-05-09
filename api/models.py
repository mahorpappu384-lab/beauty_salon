"""
Beauty Salon - All Database Models

Photo handling strategy:
- Frontend (Flutter/JS) Cloudinary pe seedha upload karta hai
- Backend ko sirf Cloudinary URL aata hai (CharField)
- Koi file upload backend pe nahi hoti
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# ─────────────────────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────────────────────

class User(AbstractUser):
    """Extended User model."""
    phone = models.CharField(max_length=15, blank=True)
    avatar_url = models.URLField(blank=True)        # Cloudinary URL from frontend
    fcm_token = models.TextField(blank=True)         # Firebase push notification token
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.email})"


# ─────────────────────────────────────────────────────────────
# SERVICE
# ─────────────────────────────────────────────────────────────

class ServiceCategory(models.Model):
    """Hair, Facial, Makeup, Nail Art, etc."""
    name = models.CharField(max_length=100, unique=True)
    icon_url = models.URLField(blank=True)          # Cloudinary URL
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'service_categories'
        ordering = ['order', 'name']
        verbose_name = 'Service Category'
        verbose_name_plural = 'Service Categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    """Individual services like Hair Wash, Bridal Makeup, etc."""
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL,
        null=True, related_name='services'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)          # Cloudinary URL from frontend
    duration_minutes = models.PositiveIntegerField(default=30)

    # Pricing
    original_price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'services'
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        if self.discount_percent > 0:
            return round(
                float(self.original_price) * (1 - float(self.discount_percent) / 100), 2
            )
        return float(self.original_price)

    @property
    def savings(self):
        return round(float(self.original_price) - self.discounted_price, 2)


# ─────────────────────────────────────────────────────────────
# PRODUCT
# ─────────────────────────────────────────────────────────────

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'product_categories'
        verbose_name_plural = 'Product Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Beauty products for sale."""
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL,
        null=True, related_name='products'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)

    # Multiple images from Cloudinary (stored as comma-separated URLs or JSON)
    image_url = models.URLField(blank=True)              # Main image - Cloudinary URL
    image_urls = models.JSONField(default=list, blank=True)  # Additional images

    # Pricing
    original_price = models.DecimalField(max_digits=8, decimal_places=2)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    stock = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-is_featured', 'name']

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
        if self.discount_percent > 0:
            return round(
                float(self.original_price) * (1 - float(self.discount_percent) / 100), 2
            )
        return float(self.original_price)

    @property
    def in_stock(self):
        return self.stock > 0


# ─────────────────────────────────────────────────────────────
# OFFER / BANNER
# ─────────────────────────────────────────────────────────────

class Offer(models.Model):
    """Home screen banners and promotional offers."""
    OFFER_TYPE_CHOICES = [
        ('banner', 'Banner'),
        ('service', 'Service Offer'),
        ('product', 'Product Offer'),
        ('coupon', 'Coupon Offer'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True)              # Cloudinary URL from frontend
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPE_CHOICES, default='banner')

    # Optional link to service or product
    linked_service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers'
    )
    linked_product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers'
    )

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'offers'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────────────────────
# BOOKING
# ─────────────────────────────────────────────────────────────

class TimeSlot(models.Model):
    """Available time slots for booking."""
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'time_slots'
        ordering = ['start_time']

    def __str__(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Booking(models.Model):
    """Customer service booking."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    booking_date = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Optional coupon applied
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings'
    )

    notes = models.TextField(blank=True)              # Customer special requests
    admin_notes = models.TextField(blank=True)        # Admin rejection reason etc.

    # Final amount after discount
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.service.name} on {self.booking_date}"


# ─────────────────────────────────────────────────────────────
# GALLERY
# ─────────────────────────────────────────────────────────────

class GalleryPhoto(models.Model):
    """Customer before/after transformation photos."""
    CATEGORY_CHOICES = [
        ('hair', 'Hair'),
        ('facial', 'Facial'),
        ('makeup', 'Makeup'),
        ('nail', 'Nail Art'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')

    # Both URLs from Cloudinary - admin panel se ya frontend se upload
    before_image_url = models.URLField()   # Required - Cloudinary URL
    after_image_url = models.URLField()    # Required - Cloudinary URL

    service = models.ForeignKey(
        Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='gallery'
    )
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='gallery_photos'
    )

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'gallery_photos'
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.category} - {self.title or self.id}"


# ─────────────────────────────────────────────────────────────
# WISHLIST
# ─────────────────────────────────────────────────────────────

class Wishlist(models.Model):
    """User wishlist for services and products."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, null=True, blank=True, related_name='wishlisted_by'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlists'
        # Ek user ek service/product ek hi baar wishlist mein add kar sakta hai
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'service'],
                condition=models.Q(service__isnull=False),
                name='unique_user_service_wishlist'
            ),
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=models.Q(product__isnull=False),
                name='unique_user_product_wishlist'
            ),
        ]

    def __str__(self):
        item = self.service or self.product
        return f"{self.user.username} → {item}"


# ─────────────────────────────────────────────────────────────
# REVIEW & RATING
# ─────────────────────────────────────────────────────────────

class Review(models.Model):
    """Customer reviews for services and products."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'service'],
                condition=models.Q(service__isnull=False),
                name='unique_user_service_review'
            ),
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=models.Q(product__isnull=False),
                name='unique_user_product_review'
            ),
        ]

    def __str__(self):
        item = self.service or self.product
        return f"{self.user.username} rated {item} → {self.rating}/5"


# ─────────────────────────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────────────────────────

class Notification(models.Model):
    """In-app notifications for users."""
    NOTIFICATION_TYPE_CHOICES = [
        ('booking_confirmed', 'Booking Confirmed'),
        ('booking_rejected', 'Booking Rejected'),
        ('booking_completed', 'Booking Completed'),
        ('new_offer', 'New Offer'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default='general'
    )
    is_read = models.BooleanField(default=False)

    # Optional deep link data
    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"


# ─────────────────────────────────────────────────────────────
# COUPON
# ─────────────────────────────────────────────────────────────

class Coupon(models.Model):
    """Discount coupon codes."""
    DISCOUNT_TYPE_CHOICES = [
        ('percent', 'Percentage'),
        ('flat', 'Flat Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES, default='percent')
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )  # Cap for percentage coupons

    usage_limit = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_till = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupons'

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'%' if self.discount_type == 'percent' else '₹'} off)"

    def calculate_discount(self, amount):
        """Given order amount, return discount amount."""
        if self.discount_type == 'percent':
            disc = float(amount) * float(self.discount_value) / 100
            if self.maximum_discount:
                disc = min(disc, float(self.maximum_discount))
        else:
            disc = float(self.discount_value)
        return round(disc, 2)


# ─────────────────────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────────────────────

class Payment(models.Model):
    """Razorpay payment records."""
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='INR')

    # Razorpay IDs
    razorpay_order_id = models.CharField(max_length=200, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, blank=True)
    razorpay_signature = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment #{self.id} - {self.status} - ₹{self.amount}"