from django.urls import path

from . import views


app_name = "app"


urlpatterns = [
    path("", views.home, name="home"),

    # Authentication
    path("auth/login/", views.login_view, name="login"),
    path("auth/signup/", views.signup_view, name="signup"),
    path("auth/logout/", views.logout_view, name="logout"),

    # Cart
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:product_id>/", views.update_cart, name="update_cart"),
    path("cart/remove/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),

    # Wishlist
    path(
        "wishlist/toggle/<int:product_id>/",
        views.toggle_wishlist,
        name="toggle_wishlist",
    ),

    # Checkout
    path(
        "checkout/place-order/",
        views.place_order,
        name="place_order",
    ),

    
]