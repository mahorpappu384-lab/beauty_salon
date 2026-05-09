"""
Beauty Salon - All Serializers

Note: image fields are URLField, not ImageField.
Frontend Cloudinary pe upload karta hai, backend ko URL milta hai.
"""

from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    User, ServiceCategory, Service, ProductCategory, Product,
    Offer, TimeSlot, Booking, GalleryPhoto, Wishlist,
    Review, Notification, Coupon, Payment
)


# ─────────────────────────────────────────────────────────────
# AUTH SERIALIZERS
# ─────────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login - extra user info token mein dalta hai."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserProfileSerializer(self.user).data
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """New user registration."""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'phone', 'avatar_url', 'password', 'password2']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'Email already registered.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile read/update."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'phone', 'avatar_url', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'username', 'is_staff', 'date_joined']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# ─────────────────────────────────────────────────────────────
# SERVICE SERIALIZERS
# ─────────────────────────────────────────────────────────────

class ServiceCategorySerializer(serializers.ModelSerializer):
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCategory
        fields = ['id', 'name', 'icon_url', 'is_active', 'order', 'service_count']

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()


class ServiceListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.ReadOnlyField()
    savings = serializers.ReadOnlyField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'category', 'category_name', 'image_url', 'description',
            'original_price', 'discount_percent', 'discounted_price', 'savings',
            'duration_minutes', 'is_featured', 'avg_rating', 'is_active'
        ]

    def get_avg_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(
                avg=serializers.models.Avg('rating') if False else
                __import__('django.db.models', fromlist=['Avg']).Avg('rating')
            )['avg'] or 0, 1)
        return None


class ServiceDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail view - includes reviews."""
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.ReadOnlyField()
    savings = serializers.ReadOnlyField()
    reviews = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'image_url', 'original_price', 'discount_percent',
            'discounted_price', 'savings', 'duration_minutes',
            'is_featured', 'is_active', 'avg_rating', 'reviews',
            'gallery', 'created_at'
        ]

    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True).select_related('user')[:5]
        return ReviewSerializer(reviews, many=True).data

    def get_avg_rating(self, obj):
        from django.db.models import Avg
        result = obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))
        return round(result['avg'] or 0, 1) if result['avg'] else None

    def get_gallery(self, obj):
        photos = obj.gallery.filter(is_active=True)[:4]
        return GalleryPhotoSerializer(photos, many=True).data


class ServiceWriteSerializer(serializers.ModelSerializer):
    """For admin: create/update service. image_url Cloudinary se milta hai."""

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'image_url',
            'original_price', 'discount_percent', 'duration_minutes',
            'is_featured', 'is_active'
        ]


# ─────────────────────────────────────────────────────────────
# PRODUCT SERIALIZERS
# ─────────────────────────────────────────────────────────────

class ProductCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'icon_url', 'is_active', 'product_count']

    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'category', 'category_name',
            'image_url', 'original_price', 'discount_percent',
            'discounted_price', 'in_stock', 'stock', 'is_featured', 'avg_rating'
        ]

    def get_avg_rating(self, obj):
        from django.db.models import Avg
        result = obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))
        return round(result['avg'] or 0, 1) if result['avg'] else None


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.ReadOnlyField()
    in_stock = serializers.ReadOnlyField()
    reviews = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'category', 'category_name',
            'image_url', 'image_urls', 'original_price', 'discount_percent',
            'discounted_price', 'stock', 'in_stock', 'is_featured',
            'avg_rating', 'reviews', 'created_at'
        ]

    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True).select_related('user')[:5]
        return ReviewSerializer(reviews, many=True).data

    def get_avg_rating(self, obj):
        from django.db.models import Avg
        result = obj.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))
        return round(result['avg'] or 0, 1) if result['avg'] else None


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'brand', 'category',
            'image_url', 'image_urls', 'original_price', 'discount_percent',
            'stock', 'is_featured', 'is_active'
        ]


# ─────────────────────────────────────────────────────────────
# OFFER / BANNER SERIALIZERS
# ─────────────────────────────────────────────────────────────

class OfferSerializer(serializers.ModelSerializer):
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'subtitle', 'description', 'image_url',
            'offer_type', 'linked_service', 'linked_product',
            'discount_percent', 'start_date', 'end_date',
            'is_active', 'order', 'is_valid'
        ]

    def get_is_valid(self, obj):
        now = timezone.now()
        return obj.is_active and obj.start_date <= now <= obj.end_date


class OfferWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = '__all__'


# ─────────────────────────────────────────────────────────────
# BOOKING SERIALIZERS
# ─────────────────────────────────────────────────────────────

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'is_active']


class BookingCreateSerializer(serializers.ModelSerializer):
    """Customer creates booking."""

    class Meta:
        model = Booking
        fields = ['id', 'service', 'booking_date', 'time_slot', 'coupon', 'notes']

    def validate_booking_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError('Booking date cannot be in the past.')
        return value

    def validate(self, attrs):
        # Check if slot is already booked
        existing = Booking.objects.filter(
            service=attrs['service'],
            booking_date=attrs['booking_date'],
            time_slot=attrs['time_slot'],
            status__in=['pending', 'confirmed']
        ).exists()
        if existing:
            raise serializers.ValidationError(
                'This time slot is already booked. Please choose another.'
            )
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        service = validated_data['service']
        coupon = validated_data.get('coupon')

        # Calculate total amount
        amount = service.discounted_price
        if coupon:
            discount = coupon.calculate_discount(amount)
            amount = max(0, amount - discount)

        booking = Booking.objects.create(
            user=user,
            total_amount=amount,
            **validated_data
        )

        # Update coupon usage
        if coupon:
            coupon.used_count += 1
            coupon.save()

        return booking


class BookingListSerializer(serializers.ModelSerializer):
    """Compact view for booking list."""
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_image = serializers.URLField(source='service.image_url', read_only=True)
    time_slot_display = serializers.CharField(source='time_slot.__str__', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'service', 'service_name', 'service_image',
            'booking_date', 'time_slot', 'time_slot_display',
            'status', 'total_amount', 'user_name', 'user_phone', 'created_at'
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    service_detail = ServiceListSerializer(source='service', read_only=True)
    time_slot_detail = TimeSlotSerializer(source='time_slot', read_only=True)
    user_detail = UserProfileSerializer(source='user', read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'


class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    """Admin uses this to accept/reject bookings."""

    class Meta:
        model = Booking
        fields = ['status', 'admin_notes']

    def validate_status(self, value):
        allowed = ['confirmed', 'rejected', 'completed']
        if value not in allowed:
            raise serializers.ValidationError(f'Status must be one of: {allowed}')
        return value


# ─────────────────────────────────────────────────────────────
# GALLERY SERIALIZERS
# ─────────────────────────────────────────────────────────────

class GalleryPhotoSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = GalleryPhoto
        fields = [
            'id', 'title', 'category', 'before_image_url', 'after_image_url',
            'service', 'service_name', 'is_featured', 'is_active', 'created_at'
        ]


class GalleryPhotoWriteSerializer(serializers.ModelSerializer):
    """
    Admin/frontend se gallery photo add karne ke liye.
    before_image_url aur after_image_url Cloudinary se aate hain.
    Frontend pehle Cloudinary pe upload karta hai, phir yeh URLs POST karta hai.
    """

    class Meta:
        model = GalleryPhoto
        fields = [
            'id', 'title', 'category', 'before_image_url',
            'after_image_url', 'service', 'is_featured'
        ]

    def validate(self, attrs):
        if not attrs.get('before_image_url') or not attrs.get('after_image_url'):
            raise serializers.ValidationError(
                'Both before_image_url and after_image_url are required.'
            )
        return attrs


# ─────────────────────────────────────────────────────────────
# WISHLIST SERIALIZERS
# ─────────────────────────────────────────────────────────────

class WishlistSerializer(serializers.ModelSerializer):
    service_detail = ServiceListSerializer(source='service', read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'service', 'product', 'service_detail', 'product_detail', 'created_at']

    def validate(self, attrs):
        if not attrs.get('service') and not attrs.get('product'):
            raise serializers.ValidationError('Either service or product is required.')
        if attrs.get('service') and attrs.get('product'):
            raise serializers.ValidationError('Provide either service or product, not both.')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return Wishlist.objects.get_or_create(user=user, **validated_data)[0]


# ─────────────────────────────────────────────────────────────
# REVIEW SERIALIZERS
# ─────────────────────────────────────────────────────────────

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_avatar = serializers.URLField(source='user.avatar_url', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'user_name', 'user_avatar',
            'service', 'product', 'rating', 'comment',
            'is_approved', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'is_approved', 'created_at']

    def validate(self, attrs):
        if not attrs.get('service') and not attrs.get('product'):
            raise serializers.ValidationError('Either service or product is required.')
        user = self.context['request'].user

        # Check if user already reviewed
        if attrs.get('service'):
            if Review.objects.filter(user=user, service=attrs['service']).exists():
                raise serializers.ValidationError('You have already reviewed this service.')
        if attrs.get('product'):
            if Review.objects.filter(user=user, product=attrs['product']).exists():
                raise serializers.ValidationError('You have already reviewed this product.')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ─────────────────────────────────────────────────────────────
# NOTIFICATION SERIALIZERS
# ─────────────────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'is_read', 'booking', 'created_at'
        ]
        read_only_fields = ['id', 'title', 'message', 'notification_type', 'booking', 'created_at']


# ─────────────────────────────────────────────────────────────
# COUPON SERIALIZERS
# ─────────────────────────────────────────────────────────────

class CouponVerifySerializer(serializers.Serializer):
    """Frontend se coupon verify karne ke liye."""
    code = serializers.CharField(max_length=50)
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)

    def validate(self, attrs):
        now = timezone.now()
        try:
            coupon = Coupon.objects.get(
                code__iexact=attrs['code'],
                is_active=True,
                valid_from__lte=now,
                valid_till__gte=now
            )
        except Coupon.DoesNotExist:
            raise serializers.ValidationError({'code': 'Invalid or expired coupon code.'})

        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            raise serializers.ValidationError({'code': 'Coupon usage limit reached.'})

        if float(attrs['amount']) < float(coupon.minimum_order):
            raise serializers.ValidationError({
                'code': f'Minimum order amount is ₹{coupon.minimum_order}'
            })

        attrs['coupon'] = coupon
        attrs['discount_amount'] = coupon.calculate_discount(attrs['amount'])
        attrs['final_amount'] = max(0, float(attrs['amount']) - attrs['discount_amount'])
        return attrs


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'


# ─────────────────────────────────────────────────────────────
# PAYMENT SERIALIZERS
# ─────────────────────────────────────────────────────────────

class PaymentCreateSerializer(serializers.Serializer):
    """Create Razorpay order."""
    booking_id = serializers.IntegerField()

    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(id=value, user=self.context['request'].user)
        except Booking.DoesNotExist:
            raise serializers.ValidationError('Booking not found.')
        if hasattr(booking, 'payment') and booking.payment.status == 'paid':
            raise serializers.ValidationError('This booking is already paid.')
        return value


class PaymentVerifySerializer(serializers.Serializer):
    """Verify Razorpay payment signature."""
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# ─────────────────────────────────────────────────────────────
# CLOUDINARY SIGNATURE SERIALIZER
# ─────────────────────────────────────────────────────────────

class CloudinarySignatureSerializer(serializers.Serializer):
    """
    Frontend direct upload ke liye signed params generate karta hai.
    Flutter ya JS seedha Cloudinary pe upload karta hai in params ke saath.
    Backend ko sirf final URL milta hai.
    """
    folder = serializers.CharField(
        default='beauty_salon',
        help_text='Cloudinary folder: services, products, gallery, profiles etc.'
    )