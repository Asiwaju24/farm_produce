from django.urls import path
from . import views

app_name = "admin_app"

urlpatterns = [
    # Dashboard
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "api/dashboard/",
        views.dashboard_data,
        name="dashboard_data",
    ),

    # Products
    path(
        "api/products/",
        views.products_api,
        name="products_api",
    ),
    path(
        "api/products/create/",
        views.create_product,
        name="product_create",
    ),
    path(
        "api/products/<int:product_id>/update/",
        views.update_product,
        name="product_update",
    ),
    path(
        "api/products/<int:product_id>/delete/",
        views.delete_product,
        name="product_delete",
    ),
    path(
        "api/products/<int:product_id>/stock/",
        views.update_product_stock,
        name="product_stock",
    ),
    path(
        "api/products/<int:product_id>/toggle/",
        views.toggle_product,
        name="product_toggle",
    ),

    # Orders
    path(
        "api/orders/",
        views.orders_api,
        name="orders_api",
    ),
    path(
        "api/orders/<int:order_id>/status/",
        views.update_order_status,
        name="order_status",
    ),
    path(
        "api/orders/<int:order_id>/payment/",
        views.verify_payment,
        name="payment_update",
    ),

    # Riders
    path(
        "api/riders/",
        views.riders,
        name="riders_api",
    ),
    path(
        "api/riders/<int:rider_id>/status/",
        views.update_rider_status,
        name="rider_status",
    ),

    # Notifications
    path(
        "api/notifications/",
        views.notifications,
        name="notifications_api",
    ),
    path(
        "api/notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="notification_read",
    ),

    # Categories
    path(
        "api/categories/",
        views.categories,
        name="categories_api",
    ),
    path(
        "api/categories/create/",
        views.create_category,
        name="category_create",
    ),

    # Exports
    path(
    "export/products/",
    views.export_products,
    name="products_export",
    ),
    path(
        "export/orders/",
        views.export_orders,
        name="orders_export",
    ),
]