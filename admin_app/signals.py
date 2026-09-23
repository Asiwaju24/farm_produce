from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import Order

from .models import AdminNotification


@receiver(post_save, sender=Order)
def notify_admin_on_new_order(sender, instance, created, **kwargs):
    """
    Create an admin notification whenever a new order is placed,
    regardless of which view created it.
    """

    if not created:
        return

    customer_name = (
        instance.user.full_name
        or instance.user.get_full_name()
        or instance.user.username
    )

    AdminNotification.objects.create(
        title="New order received",
        message=(
            f"Order FH-{instance.id:05d} was placed by {customer_name}."
        ),
        notification_type=AdminNotification.NotificationType.SUCCESS,
    )