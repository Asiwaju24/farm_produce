from django.conf import settings
from django.db import models


class AdminActivityLog(models.Model):
    """
    Records important actions performed by administrators/staff.
    """

    class ActionType(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"

        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

        STATUS_CHANGE = "status_change", "Status Change"
        STOCK_UPDATE = "stock_update", "Stock Update"
        PAYMENT_UPDATE = "payment_update", "Payment Update"

        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="admin_activity_logs",
    )

    action = models.CharField(
        max_length=30,
        choices=ActionType.choices,
    )

    description = models.TextField()

    # Example:
    # Product, Order, User, Payment, etc.
    object_type = models.CharField(
        max_length=100,
        blank=True,
    )

    # ID of the affected object.
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        username = (
            self.user.username
            if self.user
            else "Unknown user"
        )

        return f"{username} - {self.action}"


class AdminNotification(models.Model):
    """
    Notifications displayed inside the admin dashboard.
    """

    class NotificationType(models.TextChoices):
        INFO = "info", "Information"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    title = models.CharField(
        max_length=150,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )

    # If this is assigned to a specific admin/staff member.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="admin_notifications",
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title