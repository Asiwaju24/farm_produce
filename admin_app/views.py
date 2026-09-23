# admin_app/views.py

import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from app.models import (
    Category,
    Order,
    Payment,
    Product,
    Rider,
)

from .models import AdminActivityLog, AdminNotification
import logging

from django.conf import settings
from django.core.mail import send_mail



logger = logging.getLogger(__name__)

LOW_STOCK_THRESHOLD = 20


# ============================================================
# ADMIN ACCESS
# ============================================================

def admin_required(view_func):
    """
    Allow access only to:
    - superusers
    - staff users
    - users with role='admin'
    """

    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        if not (
            user.is_superuser
            or user.is_staff
            or user.role == "admin"
        ):
            return JsonResponse(
                {
                    "success": False,
                    "error": (
                        "You do not have permission to access "
                        "the admin dashboard."
                    ),
                },
                status=403,
            )

        return view_func(request, *args, **kwargs)

    return wrapper


# ============================================================
# ACTIVITY LOGGING
# ============================================================

def log_admin_action(
    request,
    action,
    description,
    object_type="",
    object_id=None,
):
    """
    Record an action performed by an administrator.
    """

    AdminActivityLog.objects.create(
        user=(
            request.user
            if request.user.is_authenticated
            else None
        ),
        action=action,
        description=description,
        object_type=object_type,
        object_id=object_id,
        ip_address=request.META.get("REMOTE_ADDR"),
    )


# ============================================================
# SERIALIZERS / DATA HELPERS
# ============================================================

def product_to_dict(product):
    """
    Convert Product instance into JSON-friendly dictionary.
    """

    image_url = ""

    if product.image:
        try:
            image_url = product.image.url
        except ValueError:
            image_url = ""

    rating = product.reviews.filter(
        is_approved=True
    ).aggregate(
        average=Avg("rating"),
        count=Count("id"),
    )

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category_id": product.category_id,
        "category": product.category.name,
        "price": float(product.price),
        "unit": product.unit,
        "stock": product.stock,
        "farmOrigin": product.farm_origin,
        "harvestDate": (
            product.harvest_date.isoformat()
            if product.harvest_date
            else ""
        ),
        "isOrganic": product.is_organic,
        "isAvailable": product.is_active,
        "image": image_url,
        "rating": (
            round(rating["average"], 1)
            if rating["average"] is not None
            else 0
        ),
        "reviewCount": rating["count"] or 0,
    }


def order_to_dict(order):
    """
    Convert Order instance into JSON-friendly dictionary.
    """

    items = order.items.select_related("product")

    items_summary = ", ".join(
        f"{item.quantity}x {item.product.name}"
        for item in items
    )

    payment = (
        order.payments
        .order_by("-payment_date")
        .first()
    )

    address = getattr(
        order,
        "shipping_address",
        None,
    )

    address_text = ""

    if address:
        address_text = (
            f"{address.street}, "
            f"{address.city}, "
            f"{address.state}"
        )

    return {
        "id": order.id,
        "reference": f"FH-{order.id:05d}",

        "customerName": (
            order.user.full_name
            or order.user.get_full_name()
            or order.user.username
        ),

        "customerId": order.user.id,

        "address": address_text,

        "itemsSummary": items_summary,

        "total": float(order.total_price),

        "status": order.status,

        "statusLabel": order.get_status_display(),

        "paymentMethod": (
            payment.payment_method
            if payment
            else None
        ),

        "paymentMethodLabel": (
            payment.get_payment_method_display()
            if payment
            else "Not recorded"
        ),

        "paymentStatus": (
            payment.status
            if payment
            else None
        ),

        "paymentCollected": (
            payment.status
            == Payment.Status.SUCCESSFUL
            if payment
            else False
        ),

        "date": order.order_date.isoformat(),
    }


def rider_to_dict(rider):
    """
    Convert Rider instance into JSON-friendly dictionary.
    """

    active_deliveries = rider.orders.filter(
        status__in=[
            Order.Status.PROCESSING,
            Order.Status.SHIPPED,
        ]
    ).count()

    cash = (
        Payment.objects.filter(
            order__rider=rider,
            payment_method=Payment.PaymentMethod.CASH,
            status=Payment.Status.SUCCESSFUL,
            payment_date__date=timezone.localdate(),
        )
        .aggregate(total=Sum("amount"))
        ["total"]
        or 0
    )

    return {
        "id": rider.id,
        "name": rider.name,
        "phone": rider.phone_number,
        "riderCode": rider.rider_code,
        "activeDeliveries": active_deliveries,
        "posTerminalId": rider.pos_terminal_id,
        "cashOnHand": float(cash),
        "status": rider.get_status_display(),
    }


# ============================================================
# DASHBOARD
# ============================================================

@admin_required
def dashboard(request):
    """
    Render the single-page admin dashboard.
    """

    products = (
        Product.objects
        .select_related("category")
        .order_by("-created_at")
    )

    orders = (
        Order.objects
        .select_related("user")
        .prefetch_related(
            "items__product",
            "payments",
        )
        .order_by("-order_date")
    )

    riders = (
        Rider.objects
        .filter(is_active=True)
        .order_by("name")
    )

    categories = list(
        Category.objects
        .order_by("name")
        .values(
            "id",
            "name",
        )
    )

    context = {
        "admin_user": request.user,

        "products": [
            product_to_dict(product)
            for product in products
        ],

        "orders": [
            order_to_dict(order)
            for order in orders
        ],

        "riders": [
            rider_to_dict(rider)
            for rider in riders
        ],

        "categories": categories,
    }

    return render(
        request,
        "admin_app/index.html",
        context,
    )


@admin_required
def dashboard_data(request):
    """
    AJAX endpoint for dashboard KPIs.
    """

    total_sales = (
        Payment.objects
        .filter(
            status=Payment.Status.SUCCESSFUL,
        )
        .aggregate(total=Sum("amount"))
        ["total"]
        or 0
    )

    completed_orders = (
        Order.objects
        .filter(
            status=Order.Status.DELIVERED
        )
        .count()
    )

    active_inventory = (
        Product.objects
        .filter(is_active=True)
        .aggregate(total=Sum("stock"))
        ["total"]
        or 0
    )

    low_stock = (
        Product.objects
        .filter(
            is_active=True,
            stock__lt=LOW_STOCK_THRESHOLD,
        )
        .count()
    )

    pending_pod = (
        Payment.objects
        .filter(
            payment_method__in=[
                Payment.PaymentMethod.CASH,
                Payment.PaymentMethod.CARD,
            ],
            status=Payment.Status.PENDING,
        )
        .aggregate(total=Sum("amount"))
        ["total"]
        or 0
    )

    # ------------------------------------------------------
    # NEW: distinct customers who have placed at least one
    # order. Adjust this definition if "customers" should
    # instead mean all registered users regardless of
    # whether they've ordered.
    # ------------------------------------------------------
    total_customers = (
        Order.objects
        .values("user")
        .distinct()
        .count()
    )

    # ------------------------------------------------------
    # NEW: actual low-stock product list (not just the
    # count) so the dashboard's Low Stock card has
    # something to render.
    # ------------------------------------------------------
    low_stock_products = [
        {
            "name": product.name,
            "category": product.category.name,
            "stock": product.stock,
            "price": float(product.price),
        }
        for product in (
            Product.objects
            .filter(
                is_active=True,
                stock__lt=LOW_STOCK_THRESHOLD,
            )
            .select_related("category")
            .order_by("stock")[:10]
        )
    ]

    return JsonResponse(
        {
            "success": True,

            "kpis": {
                "totalSales": float(total_sales),
                "completedOrders": completed_orders,
                "activeInventory": active_inventory,
                "lowStock": low_stock,
                "pendingPOD": float(pending_pod),
                "totalCustomers": total_customers,
            },

            "counts": {
                "products": Product.objects.count(),
                "orders": Order.objects.count(),
                "riders": Rider.objects.filter(
                    is_active=True
                ).count(),
            },

            "low_stock_products": low_stock_products,
        }
    )


# ============================================================
# PRODUCTS
# ============================================================

@admin_required
def products_api(request):
    """
    Return all products for the admin dashboard.
    """

    products = (
        Product.objects
        .select_related("category")
        .order_by("-created_at")
    )

    return JsonResponse(
        {
            "success": True,
            "products": [
                product_to_dict(product)
                for product in products
            ],
        }
    )


@admin_required
@require_POST
def create_product(request):
    """
    Create a new product.
    """

    name = request.POST.get(
        "name",
        "",
    ).strip()

    description = request.POST.get(
        "description",
        "",
    ).strip()

    category_id = request.POST.get("category")
    price = request.POST.get("price")
    stock = request.POST.get(
        "stock",
        0,
    )

    unit = request.POST.get(
        "unit",
        "per kg",
    )

    farm_origin = request.POST.get(
        "farm_origin",
        "",
    ).strip()

    harvest_date = (
        request.POST.get("harvest_date")
        or None
    )

    is_organic = (
        request.POST.get("is_organic")
        in ["true", "1", "on"]
    )

    image = request.FILES.get("image")

    if not name:
        return JsonResponse(
            {
                "success": False,
                "error": "Product name is required.",
            },
            status=400,
        )

    if not category_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Category is required.",
            },
            status=400,
        )

    if not price:
        return JsonResponse(
            {
                "success": False,
                "error": "Product price is required.",
            },
            status=400,
        )

    category = get_object_or_404(
        Category,
        pk=category_id,
    )

    product = Product.objects.create(
        name=name,
        description=description,
        category=category,
        price=price,
        stock=stock,
        unit=unit,
        farm_origin=farm_origin,
        harvest_date=harvest_date,
        is_organic=is_organic,
        image=image,
        is_active=True,
    )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.CREATE,
        f"Created product: {product.name}",
        "Product",
        product.id,
    )

    return JsonResponse(
        {
            "success": True,
            "message": (
                f"{product.name} created successfully."
            ),
            "product": product_to_dict(product),
        }
    )


@admin_required
@require_POST
def update_product(request, product_id):
    """
    Update an existing product.
    """

    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    name = request.POST.get(
        "name",
        "",
    ).strip()

    description = request.POST.get(
        "description",
        "",
    ).strip()

    category_id = request.POST.get("category")
    price = request.POST.get("price")
    stock = request.POST.get(
        "stock",
        product.stock,
    )

    unit = request.POST.get(
        "unit",
        product.unit,
    )

    farm_origin = request.POST.get(
        "farm_origin",
        product.farm_origin,
    ).strip()

    harvest_date = (
        request.POST.get("harvest_date")
        or None
    )

    is_organic = (
        request.POST.get("is_organic")
        in ["true", "1", "on"]
    )

    if not name:
        return JsonResponse(
            {
                "success": False,
                "error": "Product name is required.",
            },
            status=400,
        )

    if not category_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Category is required.",
            },
            status=400,
        )

    category = get_object_or_404(
        Category,
        pk=category_id,
    )

    product.name = name
    product.description = description
    product.category = category
    product.price = price
    product.stock = stock
    product.unit = unit
    product.farm_origin = farm_origin
    product.harvest_date = harvest_date
    product.is_organic = is_organic

    image = request.FILES.get("image")

    if image:
        product.image = image

    product.save()

    log_admin_action(
        request,
        AdminActivityLog.ActionType.UPDATE,
        f"Updated product: {product.name}",
        "Product",
        product.id,
    )

    return JsonResponse(
        {
            "success": True,
            "message": (
                f"{product.name} updated successfully."
            ),
            "product": product_to_dict(product),
        }
    )


@admin_required
@require_POST
def update_product_stock(request, product_id):
    """
    Increase or decrease product stock.
    """

    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    try:
        delta = int(
            request.POST.get(
                "delta",
                0,
            )
        )
    except (TypeError, ValueError):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid stock adjustment.",
            },
            status=400,
        )

    new_stock = max(
        0,
        product.stock + delta,
    )

    old_stock = product.stock

    product.stock = new_stock

    product.save(
        update_fields=[
            "stock",
            "updated_at",
        ]
    )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.STOCK_UPDATE,
        (
            f"Updated stock for {product.name}: "
            f"{old_stock} → {new_stock}"
        ),
        "Product",
        product.id,
    )

    return JsonResponse(
        {
            "success": True,
            "stock": new_stock,
        }
    )


@admin_required
@require_POST
def toggle_product(request, product_id):
    """
    Enable/disable product availability.
    """

    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    product.is_active = not product.is_active

    product.save(
        update_fields=[
            "is_active",
            "updated_at",
        ]
    )

    action_word = (
        "activated"
        if product.is_active
        else "disabled"
    )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.STATUS_CHANGE,
        (
            f"{product.name} was "
            f"{action_word}."
        ),
        "Product",
        product.id,
    )

    return JsonResponse(
        {
            "success": True,
            "isAvailable": product.is_active,
        }
    )


@admin_required
@require_POST
def delete_product(request, product_id):
    """
    Delete a product.
    """

    product = get_object_or_404(
        Product,
        pk=product_id,
    )

    product_name = product.name
    product_id_value = product.id

    try:
        product.delete()

    except Exception:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "This product cannot be deleted "
                    "because it is associated with "
                    "existing records."
                ),
            },
            status=400,
        )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.DELETE,
        f"Deleted product: {product_name}",
        "Product",
        product_id_value,
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Product deleted.",
        }
    )


# ============================================================
# ORDERS
# ============================================================

@admin_required
def orders_api(request):
    """
    Return all orders for the admin dashboard.
    """

    orders = (
        Order.objects
        .select_related("user")
        .prefetch_related(
            "items__product",
            "payments",
        )
        .order_by("-order_date")
    )

    return JsonResponse(
        {
            "success": True,
            "orders": [
                order_to_dict(order)
                for order in orders
            ],
        }
    )

def send_order_processing_email(order):
    """
    Let the customer know their order is being processed and
    should be on its way soon.
    """

    if not order.user.email:
        return

    reference = f"FH-{order.id:05d}"

    customer_name = (
        order.user.full_name
        or order.user.get_full_name()
        or order.user.username
    )

    subject = f"Your order {reference} is on its way"

    message = (
        f"Hi {customer_name},\n\n"
        f"Good news — your order {reference} is now being "
        "processed and should arrive soon.\n\n"
        "We'll let you know once it's out for delivery.\n\n"
        "Thanks for shopping with us!"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )

    except Exception:
        # Don't let a mail-server hiccup break the status update
        # itself — log it so it's still visible/debuggable.
        logger.exception(
            "Failed to send processing email for order #%s",
            order.id,
        )


@admin_required
@require_POST
def update_order_status(request, order_id):
    """
    Change an order's status.
    """

    order = get_object_or_404(
        Order,
        pk=order_id,
    )

    new_status = request.POST.get("status")

    valid_statuses = {
        value
        for value, label in Order.Status.choices
    }

    if new_status not in valid_statuses:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid order status.",
            },
            status=400,
        )

    old_status = order.status

    order.status = new_status

    order.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    if (
        new_status == Order.Status.PROCESSING
        and old_status != Order.Status.PROCESSING
    ):
        send_order_processing_email(order)



    log_admin_action(
        request,
        AdminActivityLog.ActionType.STATUS_CHANGE,
        (
            f"Order #{order.id} changed from "
            f"{old_status} to {new_status}."
        ),
        "Order",
        order.id,
    )

    return JsonResponse(
        {
            "success": True,
            "order": order_to_dict(order),
        }
    )



@admin_required
@require_POST
def verify_payment(request, order_id):
    """
    Mark the latest payment for an order as successful.
    """

    order = get_object_or_404(
        Order,
        pk=order_id,
    )

    payment = (
        order.payments
        .order_by("-payment_date")
        .first()
    )

    if not payment:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "No payment record exists "
                    "for this order."
                ),
            },
            status=404,
        )

    payment.status = Payment.Status.SUCCESSFUL

    payment.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    if order.status == Order.Status.PENDING:
        order.status = Order.Status.PAID

        order.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.PAYMENT_UPDATE,
        f"Payment verified for Order #{order.id}.",
        "Payment",
        payment.id,
    )

    return JsonResponse(
        {
            "success": True,
            "paymentStatus": payment.status,
            "order": order_to_dict(order),
        }
    )


# ============================================================
# RIDERS
# ============================================================

@admin_required
def riders(request):
    """
    Return active riders.
    """

    rider_queryset = (
        Rider.objects
        .filter(is_active=True)
        .order_by("name")
    )

    return JsonResponse(
        {
            "success": True,
            "riders": [
                rider_to_dict(rider)
                for rider in rider_queryset
            ],
        }
    )


@admin_required
@require_POST
def update_rider_status(request, rider_id):
    """
    Update rider status.
    """

    rider = get_object_or_404(
        Rider,
        pk=rider_id,
    )

    status = request.POST.get("status")

    valid_statuses = {
        value
        for value, label in Rider.Status.choices
    }

    if status not in valid_statuses:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid rider status.",
            },
            status=400,
        )

    old_status = rider.status

    rider.status = status

    rider.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.STATUS_CHANGE,
        (
            f"Rider {rider.name} changed from "
            f"{old_status} to {status}."
        ),
        "Rider",
        rider.id,
    )

    return JsonResponse(
        {
            "success": True,
            "rider": rider_to_dict(rider),
        }
    )


# ============================================================
# CATEGORIES
# ============================================================

@admin_required
def categories(request):
    """
    Return all categories.
    """

    return JsonResponse(
        {
            "success": True,
            "categories": list(
                Category.objects
                .order_by("name")
                .values(
                    "id",
                    "name",
                    "description",
                )
            ),
        }
    )


@admin_required
@require_POST
def create_category(request):
    """
    Create a new category.
    """

    name = request.POST.get(
        "name",
        "",
    ).strip()

    description = request.POST.get(
        "description",
        "",
    ).strip()

    if not name:
        return JsonResponse(
            {
                "success": False,
                "error": "Category name is required.",
            },
            status=400,
        )

    category_exists = Category.objects.filter(
        name__iexact=name
    ).exists()

    if category_exists:
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "A category with this name "
                    "already exists."
                ),
            },
            status=400,
        )

    category = Category.objects.create(
        name=name,
        description=description,
    )

    log_admin_action(
        request,
        AdminActivityLog.ActionType.CREATE,
        f"Created category: {category.name}",
        "Category",
        category.id,
    )

    return JsonResponse(
        {
            "success": True,
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
            },
        }
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@admin_required
def notifications(request):
    """
    Return global and user-specific notifications.
    """

    notifications_queryset = (
        AdminNotification.objects
        .filter(
            user__isnull=True
        )
        | AdminNotification.objects.filter(
            user=request.user
        )
    )

    notifications_queryset = (
        notifications_queryset
        .order_by("-created_at")[:20]
    )

    return JsonResponse(
        {
            "success": True,
            "notifications": [
                {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.notification_type,
                    "isRead": notification.is_read,
                    "createdAt": (
                        notification.created_at.isoformat()
                    ),
                }
                for notification
                in notifications_queryset
            ],
        }
    )


@admin_required
@require_POST
def mark_notification_read(
    request,
    notification_id,
):
    """
    Mark a notification as read.
    """

    notification = get_object_or_404(
        AdminNotification,
        pk=notification_id,
    )

    if (
        notification.user
        and notification.user != request.user
    ):
        return JsonResponse(
            {
                "success": False,
                "error": "Not allowed.",
            },
            status=403,
        )

    notification.is_read = True

    notification.save(
        update_fields=["is_read"]
    )

    return JsonResponse(
        {
            "success": True,
        }
    )


# ============================================================
# EXPORTS
# ============================================================

@admin_required
def export_products(request):
    """
    Export products as CSV.
    """

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="freshharvest_products.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "ID",
        "Name",
        "Category",
        "Price",
        "Stock",
        "Unit",
        "Farm Origin",
        "Harvest Date",
        "Organic",
        "Active",
    ])

    products = (
        Product.objects
        .select_related("category")
        .order_by("id")
    )

    for product in products:
        writer.writerow([
            product.id,
            product.name,
            product.category.name,
            product.price,
            product.stock,
            product.unit,
            product.farm_origin,
            product.harvest_date,
            product.is_organic,
            product.is_active,
        ])

    return response


@admin_required
def export_orders(request):
    """
    Export orders as CSV.
    """

    response = HttpResponse(
        content_type="text/csv"
    )

    response["Content-Disposition"] = (
        'attachment; filename="freshharvest_orders.csv"'
    )

    writer = csv.writer(response)

    writer.writerow([
        "Order ID",
        "Reference",
        "Customer",
        "Total",
        "Status",
        "Payment Method",
        "Payment Status",
        "Order Date",
    ])

    orders = (
        Order.objects
        .select_related("user")
        .prefetch_related("payments")
        .order_by("-order_date")
    )

    for order in orders:
        payment = (
            order.payments
            .order_by("-payment_date")
            .first()
        )

        writer.writerow([
            order.id,
            f"FH-{order.id:05d}",
            (
                order.user.full_name
                or order.user.get_full_name()
                or order.user.username
            ),
            order.total_price,
            order.get_status_display(),
            (
                payment.get_payment_method_display()
                if payment
                else ""
            ),
            (
                payment.get_status_display()
                if payment
                else ""
            ),
            order.order_date,
        ])

    return response