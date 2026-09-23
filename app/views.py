from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import (
    Address,
    Cart,
    Category,
    Order,
    OrderItem,
    Payment,
    Product,
    User,
    Wishlist,
)


DELIVERY_FEE = Decimal("3.99")
FREE_DELIVERY_THRESHOLD = Decimal("35.00")


CATEGORY_ICONS = {
    "exotic": "fa-seedling",
    "orchard": "fa-apple-whole",
    "berries": "fa-stroopwafel",
    "citrus": "fa-lemon",
    "tropical": "fa-sun",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _product_data(products):
    """
    Convert Product objects into JSON-friendly dictionaries
    consumed by the JavaScript inside index.html.
    """

    data = []

    for product in products:

        image_url = ""

        if product.image:
            image_url = product.image.url

        data.append(
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": str(product.price),
                "image": image_url,

                "category_id": product.category_id,
                "category_name": product.category.name,

                "stock": product.stock,
                "is_active": product.is_active,

                "rating": float(
                    product.average_rating or 0
                ),

                "review_count": (
                    product.review_count or 0
                ),

                "unit": "per item",

                # Nutritional information
                "calories": (
                    str(product.calories_per_100g)
                    if product.calories_per_100g is not None
                    else "—"
                ),

                "fiber": (
                    str(product.fiber_g)
                    if product.fiber_g is not None
                    else "—"
                ),

                "potassium": (
                    str(product.potassium_mg)
                    if product.potassium_mg is not None
                    else "—"
                ),

                "vitamin_c": (
                    str(product.vitamin_c_mg)
                    if product.vitamin_c_mg is not None
                    else "—"
                ),

                "vitamin_e": (
                    str(product.vitamin_e_mg)
                    if product.vitamin_e_mg is not None
                    else "—"
                ),
            }
        )

    return data


def _cart_data(user):
    """
    Convert the user's cart into JSON-friendly data
    consumed by the frontend.
    """

    items = (
        Cart.objects
        .filter(user=user)
        .select_related("product")
        .order_by("created_at")
    )

    data = []

    for item in items:

        image_url = ""

        if item.product.image:
            image_url = item.product.image.url

        data.append(
            {
                "product": {
                    "id": item.product.id,
                    "name": item.product.name,
                    "price": str(item.product.price),
                    "image": image_url,
                    "unit": "per item",
                    "stock": item.product.stock,
                },
                "quantity": item.quantity,
            }
        )

    return data


def _wishlist_data(user):
    """
    Return the user's wishlist product IDs.
    """

    return list(
        Wishlist.objects
        .filter(user=user)
        .values_list("product_id", flat=True)
    )


def _user_data(user):
    """
    Return basic user information for the frontend.
    """

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "phone_number": user.phone_number,
        "role": user.role,
    }


def _category_data():
    categories = (
        Category.objects
        .all()
        .order_by("name")
    )

    data = [
        {
            "id": "all",
            "label": "All Produce",
            "icon": "fa-border-all",
        }
    ]

    for category in categories:

        key = category.name.lower()

        data.append(
            {
                "id": category.id,
                "label": category.name,
                "icon": CATEGORY_ICONS.get(
                    key,
                    "fa-leaf",
                ),
            }
        )

    return data


# ============================================================
# HOME
# ============================================================

def home(request):

    products = (
        Product.objects
        .filter(is_active=True)
        .select_related("category")
        .annotate(
            average_rating=Avg(
                "reviews__rating"
            ),
            review_count=Count(
                "reviews",
                distinct=True,
            ),
        )
        .order_by("-created_at")
    )

    product_data = _product_data(products)

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = _wishlist_data(
            request.user
        )

    order_placed = False
    order_reference = ""

    if request.user.is_authenticated:

        order_id = request.GET.get("order")

        if order_id:

            order = (
                Order.objects
                .filter(
                    id=order_id,
                    user=request.user,
                )
                .first()
            )

            if order:

                order_placed = True

                order_reference = (
                    f"FH-{order.id:05d}"
                )

    context = {
        "is_authenticated":
            request.user.is_authenticated,

        "login_url":
            reverse("app:login"),

        "signup_url":
            reverse("app:signup"),

        "logout_url":
            reverse("app:logout"),

        "products":
            products,

        "product_data":
            product_data,

        "category_data":
            _category_data(),

        "cart_data":
            _cart_data(request.user)
            if request.user.is_authenticated
            else [],

        "wishlist_product_ids":
            wishlist_product_ids,

        "order_placed":
            order_placed,

        "order_reference":
            order_reference,
    }

    return render(
        request,
        "index.html",
        context,
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method.",
            },
            status=405,
        )


    if request.user.is_authenticated:

        return JsonResponse(
            {
                "success": True,
                "message": "You are already logged in.",
                "user": _user_data(
                    request.user
                ),
                "cart":
                    _cart_data(
                        request.user
                    ),
                "wishlist":
                    _wishlist_data(
                        request.user
                    ),
            }
        )


    username = (
        request.POST
        .get("username", "")
        .strip()
    )

    password = request.POST.get(
        "password",
        "",
    )


    if not username or not password:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please enter your username and password.",
            },
            status=400,
        )


    user = authenticate(
        request,
        username=username,
        password=password,
    )


    if user is None:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid username or password.",
            },
            status=401,
        )


    login(
        request,
        user,
    )


    return JsonResponse(
        {
            "success": True,
            "message":
                f"Welcome back, {user.full_name or user.username}!",

            "user":
                _user_data(user),

            "cart":
                _cart_data(user),

            "wishlist":
                _wishlist_data(user),
        }
    )


# ============================================================
# SIGNUP
# ============================================================

def signup_view(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message": "Invalid request method.",
            },
            status=405,
        )


    if request.user.is_authenticated:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "You are already logged in.",
            },
            status=400,
        )


    full_name = (
        request.POST
        .get("full_name", "")
        .strip()
    )

    username = (
        request.POST
        .get("username", "")
        .strip()
    )

    email = (
        request.POST
        .get("email", "")
        .strip()
    )

    phone_number = (
        request.POST
        .get("phone_number", "")
        .strip()
    )

    password = request.POST.get(
        "password",
        "",
    )

    password_confirmation = (
        request.POST
        .get(
            "password_confirmation",
            "",
        )
    )


    if not all(
        [
            full_name,
            username,
            email,
            phone_number,
            password,
            password_confirmation,
        ]
    ):

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please fill in all required fields.",
            },
            status=400,
        )


    if password != password_confirmation:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Passwords do not match.",
            },
            status=400,
        )


    if User.objects.filter(
        username=username
    ).exists():

        return JsonResponse(
            {
                "success": False,
                "message":
                    "That username is already in use.",
            },
            status=400,
        )


    if User.objects.filter(
        email__iexact=email
    ).exists():

        return JsonResponse(
            {
                "success": False,
                "message":
                    "An account with that email already exists.",
            },
            status=400,
        )


    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        full_name=full_name,
        phone_number=phone_number,
        role=User.Role.CUSTOMER,
    )


    login(
        request,
        user,
    )


    return JsonResponse(
        {
            "success": True,
            "message":
                "Your account has been created successfully!",

            "user":
                _user_data(user),

            "cart":
                _cart_data(user),

            "wishlist":
                _wishlist_data(user),
        }
    )


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid request method.",
            },
            status=405,
        )


    logout(request)


    return JsonResponse(
        {
            "success": True,
            "message":
                "You have been logged out successfully.",
        }
    )


# ============================================================
# ADD TO CART
# ============================================================

@login_required
def add_to_cart(request, product_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid request method.",
            },
            status=405,
        )


    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )


    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        quantity = 1


    if quantity < 1:
        quantity = 1


    if product.stock < quantity:

        return JsonResponse(
            {
                "success": False,
                "message":
                    f"Only {product.stock} item(s) of "
                    f"{product.name} are available.",
            },
            status=400,
        )


    cart_item, created = (
        Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={
                "quantity": quantity
            },
        )
    )


    if not created:

        new_quantity = (
            cart_item.quantity +
            quantity
        )


        if new_quantity > product.stock:

            return JsonResponse(
                {
                    "success": False,
                    "message":
                        f"You cannot add more than "
                        f"{product.stock} of "
                        f"{product.name}.",
                },
                status=400,
            )


        cart_item.quantity = new_quantity

        cart_item.save(
            update_fields=[
                "quantity",
                "updated_at",
            ]
        )


    return JsonResponse(
        {
            "success": True,
            "message":
                f"{product.name} added to your basket.",

            "cart":
                _cart_data(
                    request.user
                ),
        }
    )


# ============================================================
# UPDATE CART
# ============================================================

@login_required
def update_cart(request, product_id):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid request method.",
            },
            status=405,
        )


    cart_item = get_object_or_404(
        Cart,
        user=request.user,
        product_id=product_id,
    )


    try:

        quantity = int(
            request.POST.get(
                "quantity",
                1,
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        quantity = 1


    # Quantity of zero removes the item.
    if quantity <= 0:

        cart_item.delete()

        return JsonResponse(
            {
                "success": True,
                "message":
                    "Item removed from your basket.",

                "cart":
                    _cart_data(
                        request.user
                    ),
            }
        )


    if quantity > cart_item.product.stock:

        return JsonResponse(
            {
                "success": False,
                "message":
                    f"Only {cart_item.product.stock} "
                    f"item(s) are available.",
            },
            status=400,
        )


    cart_item.quantity = quantity

    cart_item.save(
        update_fields=[
            "quantity",
            "updated_at",
        ]
    )


    return JsonResponse(
        {
            "success": True,
            "message":
                "Basket updated.",

            "cart":
                _cart_data(
                    request.user
                ),
        }
    )


# ============================================================
# REMOVE FROM CART
# ============================================================

@login_required
def remove_from_cart(
    request,
    product_id,
):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid request method.",
            },
            status=405,
        )


    deleted_count, _ = (
        Cart.objects
        .filter(
            user=request.user,
            product_id=product_id,
        )
        .delete()
    )


    if deleted_count == 0:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "This item is not in your basket.",
            },
            status=404,
        )


    return JsonResponse(
        {
            "success": True,
            "message":
                "Item removed from your basket.",

            "cart":
                _cart_data(
                    request.user
                ),
        }
    )


# ============================================================
# WISHLIST
# ============================================================

@login_required
def toggle_wishlist(
    request,
    product_id,
):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid request method.",
            },
            status=405,
        )


    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True,
    )


    wishlist_item = (
        Wishlist.objects
        .filter(
            user=request.user,
            product=product,
        )
        .first()
    )


    if wishlist_item:

        wishlist_item.delete()

        message = (
            f"{product.name} removed "
            "from your favorites."
        )

        action = "removed"

    else:

        Wishlist.objects.create(
            user=request.user,
            product=product,
        )

        message = (
            f"{product.name} added "
            "to your favorites!"
        )

        action = "added"


    return JsonResponse(
        {
            "success": True,
            "message": message,
            "action": action,

            "wishlist":
                _wishlist_data(
                    request.user
                ),
        }
    )


# ============================================================
# PLACE ORDER
# ============================================================

@login_required
@transaction.atomic
def place_order(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid request method.",
            },
            status=405,
        )


    cart_items = list(
        Cart.objects
        .filter(
            user=request.user
        )
        .select_related("product")
    )


    if not cart_items:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Your basket is empty.",
            },
            status=400,
        )


    # ========================================================
    # GET CHECKOUT DATA
    # ========================================================

    full_name = (
        request.POST
        .get("full_name", "")
        .strip()
    )

    phone_number = (
        request.POST
        .get("phone_number", "")
        .strip()
    )

    street = (
        request.POST
        .get("street", "")
        .strip()
    )

    city = (
        request.POST
        .get("city", "")
        .strip()
    )

    state = (
        request.POST
        .get("state", "")
        .strip()
    )

    postal_code = (
        request.POST
        .get("postal_code", "")
        .strip()
    )

    country = (
        request.POST
        .get(
            "country",
            "Nigeria",
        )
        .strip()
    )

    payment_method = (
        request.POST
        .get(
            "pod_method",
            "cash",
        )
        .strip()
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    if not full_name:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please enter your full name.",
            },
            status=400,
        )


    if not phone_number:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please enter your phone number.",
            },
            status=400,
        )


    if not street:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please enter your delivery address.",
            },
            status=400,
        )


    if not city:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please enter your city.",
            },
            status=400,
        )


    if not state:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please enter your state.",
            },
            status=400,
        )


    # ========================================================
    # PAYMENT METHOD
    # ========================================================

    payment_method_map = {
        "cash":
            Payment.PaymentMethod.CASH,

        "pos":
            Payment.PaymentMethod.CARD,

        "transfer":
            Payment.PaymentMethod.BANK_TRANSFER,
    }


    selected_payment_method = (
        payment_method_map.get(
            payment_method
        )
    )


    if not selected_payment_method:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid payment method.",
            },
            status=400,
        )


    # ========================================================
    # UPDATE USER PROFILE
    # ========================================================

    request.user.full_name = full_name

    request.user.phone_number = (
        phone_number
    )

    request.user.save(
        update_fields=[
            "full_name",
            "phone_number",
        ]
    )


    # ========================================================
    # LOCK PRODUCTS
    # ========================================================

    locked_products = {}


    for item in cart_items:

        product = (
            Product.objects
            .select_for_update()
            .get(
                id=item.product_id
            )
        )


        if not product.is_active:

            return JsonResponse(
                {
                    "success": False,
                    "message":
                        f"{product.name} "
                        "is no longer available.",
                },
                status=400,
            )


        if product.stock < item.quantity:

            return JsonResponse(
                {
                    "success": False,
                    "message":
                        f"Sorry, only "
                        f"{product.stock} "
                        f"{product.name} "
                        "is available.",
                },
                status=400,
            )


        locked_products[
            product.id
        ] = product


    # ========================================================
    # CALCULATE TOTAL
    # ========================================================

    subtotal = Decimal("0.00")


    for item in cart_items:

        product = locked_products[
            item.product_id
        ]

        subtotal += (
            product.price *
            item.quantity
        )


    delivery_fee = (
        Decimal("0.00")
        if subtotal >= FREE_DELIVERY_THRESHOLD
        else DELIVERY_FEE
    )


    total = (
        subtotal +
        delivery_fee
    )


    # ========================================================
    # CREATE ORDER
    # ========================================================

    order = Order.objects.create(
        user=request.user,
        total_price=total,
        status=Order.Status.PENDING,
    )


    # ========================================================
    # CREATE ORDER ITEMS + REDUCE STOCK
    # ========================================================

    for item in cart_items:

        product = locked_products[
            item.product_id
        ]


        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price=product.price,
        )


        product.stock -= (
            item.quantity
        )


        product.save(
            update_fields=[
                "stock",
                "updated_at",
            ]
        )


    # ========================================================
    # SAVE DELIVERY ADDRESS
    # ========================================================

    Address.objects.create(
        user=request.user,
        street=street,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country,
    )


    # ========================================================
    # CREATE PAYMENT
    # ========================================================

    Payment.objects.create(
        user=request.user,
        order=order,
        amount=total,
        payment_method=selected_payment_method,
        transaction_reference=(
            f"POD-{uuid4().hex[:20].upper()}"
        ),
        status=Payment.Status.PENDING,
    )


    # ========================================================
    # EMPTY CART
    # ========================================================

    Cart.objects.filter(
        user=request.user
    ).delete()


    # ========================================================
    # AJAX RESPONSE
    # ========================================================

    return JsonResponse(
        {
            "success": True,

            "message":
                "Your order has been placed successfully!",

            "order_id":
                order.id,

            "order_reference":
                f"FH-{order.id:05d}",

            "subtotal":
                str(subtotal),

            "delivery_fee":
                str(delivery_fee),

            "total":
                str(total),

            "cart": [],
        }
    )