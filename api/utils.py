"""
Beauty Salon - Utility Functions

1. generate_cloudinary_signature: Frontend direct upload ke liye
2. send_notification: In-app notifications create karna
3. razorpay_client: Razorpay client instance
"""

import hashlib
import hmac
import time

from django.conf import settings


def generate_cloudinary_signature(folder: str, timestamp: int = None) -> str:
    """
    Cloudinary direct upload ke liye signature generate karta hai.
    
    Frontend flow:
    1. GET /api/cloudinary/signature/?folder=gallery
    2. Backend yeh function call karta hai
    3. Frontend response use karke directly Cloudinary pe upload karta hai
    4. Cloudinary URL backend ko POST karta hai
    
    Args:
        folder: Cloudinary folder name (services, products, gallery, profiles)
        timestamp: Unix timestamp (default: current time)
    
    Returns:
        SHA1 signature string
    """
    if timestamp is None:
        timestamp = int(time.time())

    # Params to sign (alphabetically ordered)
    params_to_sign = f"folder={folder}&timestamp={timestamp}{settings.CLOUDINARY_API_SECRET}"

    signature = hashlib.sha1(params_to_sign.encode()).hexdigest()
    return signature


def send_notification(user, title: str, message: str,
                      notification_type: str = 'general', booking=None):
    """
    User ke liye in-app notification create karta hai.
    
    Args:
        user: User instance
        title: Notification title
        message: Notification body
        notification_type: Type from Notification.NOTIFICATION_TYPE_CHOICES
        booking: Optional Booking instance for deep linking
    """
    from .models import Notification

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        booking=booking
    )


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Razorpay payment signature verify karta hai.
    
    Args:
        order_id: Razorpay order ID
        payment_id: Razorpay payment ID
        signature: Signature from frontend
    
    Returns:
        True if valid, False otherwise
    """
    generated = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()
    return generated == signature


def calculate_discounted_price(original_price: float, discount_percent: float) -> float:
    """Price calculation helper."""
    if discount_percent <= 0:
        return original_price
    discount = original_price * discount_percent / 100
    return round(original_price - discount, 2)


def get_cloudinary_upload_url(cloud_name: str = None) -> str:
    """Cloudinary upload URL return karta hai."""
    name = cloud_name or settings.CLOUDINARY_CLOUD_NAME
    return f"https://api.cloudinary.com/v1_1/{name}/image/upload"