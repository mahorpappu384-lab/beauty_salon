"""
Beauty Salon - Django Signals

Booking status change hone par automatically notification bhejta hai.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Booking
from .utils import send_notification


@receiver(post_save, sender=Booking)
def booking_status_notification(sender, instance, created, **kwargs):
    """
    Booking create ya update hone par user ko notification milti hai.
    """
    if created:
        return  # View already handles creation notification

    # Status change notification
    if instance.status == 'confirmed':
        send_notification(
            user=instance.user,
            title='Booking Confirmed! ✅',
            message=f'Your appointment for {instance.service.name} on {instance.booking_date} '
                    f'at {instance.time_slot} is confirmed.',
            notification_type='booking_confirmed',
            booking=instance
        )
    elif instance.status == 'rejected':
        reason = f' Reason: {instance.admin_notes}' if instance.admin_notes else ''
        send_notification(
            user=instance.user,
            title='Booking Update',
            message=f'Your booking for {instance.service.name} could not be accepted.{reason}',
            notification_type='booking_rejected',
            booking=instance
        )
    elif instance.status == 'completed':
        send_notification(
            user=instance.user,
            title='Service Completed! ⭐',
            message=f'Thank you for visiting! How was your {instance.service.name} experience? Leave a review.',
            notification_type='booking_completed',
            booking=instance
        )