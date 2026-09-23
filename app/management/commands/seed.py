from decimal import Decimal
from io import BytesIO

import requests

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from app.models import (
    Category,
    Product,
    Review,
    User,
)


class Command(BaseCommand):
    help = "Seed FreshHarvest with demo categories, products, images, users and reviews."

    # =========================================================
    # CATEGORIES
    # =========================================================

    CATEGORIES = [
        {
            "name": "Exotic",
            "description": "Unique and exotic fruits sourced from around the world.",
        },
        {
            "name": "Orchard",
            "description": "Fresh, naturally sweet fruits from orchards.",
        },
        {
            "name": "Berries",
            "description": "Fresh and nutritious berries packed with antioxidants.",
        },
        {
            "name": "Citrus",
            "description": "Fresh citrus fruits rich in vitamin C.",
        },
        {
            "name": "Tropical",
            "description": "Fresh tropical fruits full of flavor and nutrients.",
        },
    ]

    # =========================================================
    # PRODUCTS
    # =========================================================

    PRODUCTS = [
        {
            "name": "Fresh Mango",
            "category": "Tropical",
            "description": (
                "Sweet, juicy and naturally delicious mangoes. "
                "Perfect for smoothies, desserts or eating fresh."
            ),
            "price": "8.99",
            "stock": 42,
            "calories": "60",
            "fiber": "1.60",
            "potassium": "168",
            "vitamin_c": "36.40",
            "vitamin_e": "0.90",
            "image": (
                "https://images.unsplash.com/"
                "photo-1553279768-865429fa0078"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Red Apples",
            "category": "Orchard",
            "description": (
                "Crisp, refreshing red apples with a naturally sweet flavor. "
                "Great for snacks, salads and lunch boxes."
            ),
            "price": "5.49",
            "stock": 65,
            "calories": "52",
            "fiber": "2.40",
            "potassium": "107",
            "vitamin_c": "4.60",
            "vitamin_e": "0.18",
            "image": (
                "https://images.unsplash.com/"
                "photo-1560806887-1e4cd0b6cbd6"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Fresh Bananas",
            "category": "Tropical",
            "description": (
                "Naturally sweet bananas with a soft texture. "
                "An excellent everyday snack and smoothie ingredient."
            ),
            "price": "4.25",
            "stock": 80,
            "calories": "89",
            "fiber": "2.60",
            "potassium": "358",
            "vitamin_c": "8.70",
            "vitamin_e": "0.10",
            "image": (
                "https://images.unsplash.com/"
                "photo-1571771894821-ce9b6c11b08e"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Sweet Strawberries",
            "category": "Berries",
            "description": (
                "Bright red strawberries with a sweet and slightly tangy flavor. "
                "Perfect for desserts, breakfast bowls and smoothies."
            ),
            "price": "9.50",
            "stock": 30,
            "calories": "32",
            "fiber": "2.00",
            "potassium": "153",
            "vitamin_c": "58.80",
            "vitamin_e": "0.29",
            "image": (
                "https://images.unsplash.com/"
                "photo-1464965911861-746a04b4bca6"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Blueberries",
            "category": "Berries",
            "description": (
                "Fresh blueberries packed with antioxidants and natural sweetness. "
                "Ideal for breakfast bowls and smoothies."
            ),
            "price": "11.99",
            "stock": 25,
            "calories": "57",
            "fiber": "2.40",
            "potassium": "77",
            "vitamin_c": "9.70",
            "vitamin_e": "0.57",
            "image": (
                "https://images.unsplash.com/"
                "photo-1498557850523-fd3d118b962e"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Fresh Oranges",
            "category": "Citrus",
            "description": (
                "Juicy oranges with a bright citrus flavor and plenty of vitamin C. "
                "Perfect for fresh juice or a healthy snack."
            ),
            "price": "6.25",
            "stock": 55,
            "calories": "47",
            "fiber": "2.40",
            "potassium": "181",
            "vitamin_c": "53.20",
            "vitamin_e": "0.18",
            "image": (
                "https://images.unsplash.com/"
                "photo-1547514701-42782101795e"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Pineapple",
            "category": "Tropical",
            "description": (
                "Sweet and tangy tropical pineapple with a refreshing flavor. "
                "Great on its own or blended into smoothies."
            ),
            "price": "7.75",
            "stock": 34,
            "calories": "50",
            "fiber": "1.40",
            "potassium": "109",
            "vitamin_c": "47.80",
            "vitamin_e": "0.02",
            "image": (
                "https://images.unsplash.com/"
                "photo-1550258987-190a2d41a8ba"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Green Grapes",
            "category": "Orchard",
            "description": (
                "Crisp and juicy green grapes with a naturally refreshing sweetness."
            ),
            "price": "7.25",
            "stock": 48,
            "calories": "69",
            "fiber": "0.90",
            "potassium": "191",
            "vitamin_c": "3.20",
            "vitamin_e": "0.19",
            "image": (
                "https://images.unsplash.com/"
                "photo-1537640538966-79f369143f8f"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Avocado",
            "category": "Exotic",
            "description": (
                "Creamy, nutrient-rich avocado with a smooth texture. "
                "Perfect for toast, salads and smoothies."
            ),
            "price": "6.99",
            "stock": 38,
            "calories": "160",
            "fiber": "6.70",
            "potassium": "485",
            "vitamin_c": "10.00",
            "vitamin_e": "2.07",
            "image": (
                "https://images.unsplash.com/"
                "photo-1519162808019-7de1683fa2ad"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Papaya",
            "category": "Exotic",
            "description": (
                "Soft, sweet papaya with vibrant orange flesh. "
                "A refreshing tropical fruit rich in vitamin C."
            ),
            "price": "8.50",
            "stock": 27,
            "calories": "43",
            "fiber": "1.70",
            "potassium": "182",
            "vitamin_c": "60.90",
            "vitamin_e": "0.30",
            "image": (
                "https://images.unsplash.com/"
                "photo-1526318472351-c75fcf070305"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Dragon Fruit",
            "category": "Exotic",
            "description": (
                "Beautiful dragon fruit with a mildly sweet flavor and "
                "refreshing texture."
            ),
            "price": "12.50",
            "stock": 18,
            "calories": "57",
            "fiber": "3.10",
            "potassium": "268",
            "vitamin_c": "9.00",
            "vitamin_e": "0.08",
            "image": (
                "https://images.unsplash.com/"
                "photo-1527325678964-54921661f888"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Kiwi",
            "category": "Exotic",
            "description": (
                "Fresh kiwi with a bright green center and a delicious "
                "sweet-tart flavor."
            ),
            "price": "8.25",
            "stock": 35,
            "calories": "61",
            "fiber": "3.00",
            "potassium": "312",
            "vitamin_c": "92.70",
            "vitamin_e": "1.30",
            "image": (
                "https://images.unsplash.com/"
                "photo-1585059895524-72359e06133a"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Lemons",
            "category": "Citrus",
            "description": (
                "Fresh, vibrant lemons with a sharp citrus flavor. "
                "Ideal for drinks, cooking and dressings."
            ),
            "price": "4.99",
            "stock": 60,
            "calories": "29",
            "fiber": "2.80",
            "potassium": "138",
            "vitamin_c": "53.00",
            "vitamin_e": "0.15",
            "image": (
                "https://images.unsplash.com/"
                "photo-1590502593747-42a996133562"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Raspberries",
            "category": "Berries",
            "description": (
                "Delicate raspberries with a naturally sweet and tart flavor. "
                "Excellent for breakfast and desserts."
            ),
            "price": "10.75",
            "stock": 22,
            "calories": "52",
            "fiber": "6.50",
            "potassium": "151",
            "vitamin_c": "26.20",
            "vitamin_e": "0.87",
            "image": (
                "https://images.unsplash.com/"
                "photo-1577069861033-55d04cec4ef5"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Watermelon",
            "category": "Tropical",
            "description": (
                "Fresh, juicy watermelon with a naturally refreshing sweetness. "
                "Perfect for hot days."
            ),
            "price": "9.25",
            "stock": 20,
            "calories": "30",
            "fiber": "0.40",
            "potassium": "112",
            "vitamin_c": "8.10",
            "vitamin_e": "0.05",
            "image": (
                "https://images.unsplash.com/"
                "photo-1563114773-84221bd62daa"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Peaches",
            "category": "Orchard",
            "description": (
                "Soft and juicy peaches with a fragrant aroma and "
                "naturally sweet flavor."
            ),
            "price": "8.75",
            "stock": 29,
            "calories": "39",
            "fiber": "1.50",
            "potassium": "190",
            "vitamin_c": "6.60",
            "vitamin_e": "0.73",
            "image": (
                "https://images.unsplash.com/"
                "photo-1629828874514-2d9ea7f4c5e8"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Pomegranate",
            "category": "Exotic",
            "description": (
                "Beautiful pomegranate filled with juicy ruby-red seeds "
                "and a sweet-tart flavor."
            ),
            "price": "10.99",
            "stock": 24,
            "calories": "83",
            "fiber": "4.00",
            "potassium": "236",
            "vitamin_c": "10.20",
            "vitamin_e": "0.60",
            "image": (
                "https://images.unsplash.com/"
                "photo-1541344999736-83eca272f6fc"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
        {
            "name": "Coconut",
            "category": "Tropical",
            "description": (
                "Fresh tropical coconut with naturally refreshing water "
                "and creamy coconut flesh."
            ),
            "price": "7.99",
            "stock": 32,
            "calories": "354",
            "fiber": "9.00",
            "potassium": "356",
            "vitamin_c": "3.30",
            "vitamin_e": "0.24",
            "image": (
                "https://images.unsplash.com/"
                "photo-1444492417251-9c84a5fa18e0"
                "?auto=format&fit=crop&w=900&q=85"
            ),
        },
    ]

    # =========================================================
    # DEMO USERS
    # =========================================================

    USERS = [
        {
            "username": "demo_customer",
            "email": "customer@freshharvest.test",
            "password": "FreshHarvest123!",
            "full_name": "Demo Customer",
            "phone_number": "08012345678",
            "role": User.Role.CUSTOMER,
        },
        {
            "username": "freshharvest_admin",
            "email": "admin@freshharvest.test",
            "password": "FreshHarvestAdmin123!",
            "full_name": "FreshHarvest Admin",
            "phone_number": "08098765432",
            "role": User.Role.ADMIN,
            "is_staff": True,
            "is_superuser": True,
        },
    ]

    # =========================================================
    # REVIEWS
    # =========================================================

    REVIEW_COMMENTS = [
        "Absolutely fresh and delicious!",
        "Great quality. Will definitely order again.",
        "The fruit arrived fresh and well packaged.",
        "Very tasty and exactly as described.",
        "Excellent quality for the price.",
        "Fresh, juicy and delicious.",
        "Really happy with my purchase.",
    ]

    # =========================================================
    # IMAGE DOWNLOADER
    # =========================================================

    def download_image(self, url, product_name):
        """
        Download product image from Unsplash and return a Django
        ContentFile.
        """

        try:
            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "FreshHarvest/1.0"
                },
            )

            response.raise_for_status()

            return ContentFile(
                response.content,
                name=f"{product_name.lower().replace(' ', '_')}.jpg",
            )

        except requests.RequestException as error:

            self.stdout.write(
                self.style.WARNING(
                    f"Could not download image for "
                    f"{product_name}: {error}"
                )
            )

            return None

    # =========================================================
    # HANDLE
    # =========================================================

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "🌱 Starting FreshHarvest seed..."
            )
        )
        self.stdout.write("")

        # -----------------------------------------------------
        # CATEGORIES
        # -----------------------------------------------------

        categories = {}

        for category_data in self.CATEGORIES:

            category, created = Category.objects.update_or_create(
                name=category_data["name"],
                defaults={
                    "description": category_data["description"],
                },
            )

            categories[category.name] = category

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created category: {category.name}"
                    )
                )
            else:
                self.stdout.write(
                    f"• Category already exists: {category.name}"
                )

        # -----------------------------------------------------
        # PRODUCTS
        # -----------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "🍎 Creating products..."
            )
        )

        products = {}

        for product_data in self.PRODUCTS:

            category = categories[
                product_data["category"]
            ]

            product, created = Product.objects.update_or_create(
                name=product_data["name"],
                defaults={
                    "description": product_data["description"],
                    "price": Decimal(product_data["price"]),
                    "category": category,
                    "stock": product_data["stock"],
                    "is_active": True,
                    "calories_per_100g": Decimal(
                        product_data["calories"]
                    ),
                    "fiber_g": Decimal(
                        product_data["fiber"]
                    ),
                    "potassium_mg": Decimal(
                        product_data["potassium"]
                    ),
                    "vitamin_c_mg": Decimal(
                        product_data["vitamin_c"]
                    ),
                    "vitamin_e_mg": Decimal(
                        product_data["vitamin_e"]
                    ),
                },
            )

            products[product.name] = product

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created product: {product.name}"
                    )
                )
            else:
                self.stdout.write(
                    f"• Updated product: {product.name}"
                )

            # -------------------------------------------------
            # IMAGE
            # -------------------------------------------------

            if not product.image:

                image_file = self.download_image(
                    product_data["image"],
                    product.name,
                )

                if image_file:

                    product.image.save(
                        image_file.name,
                        image_file,
                        save=True,
                    )

                    self.stdout.write(
                        f"  ↳ Image downloaded"
                    )

        # -----------------------------------------------------
        # USERS
        # -----------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "👤 Creating demo users..."
            )
        )

        users = {}

        for user_data in self.USERS:

            username = user_data["username"]

            password = user_data["password"]

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": user_data["email"],
                    "full_name": user_data["full_name"],
                    "phone_number": user_data["phone_number"],
                    "role": user_data["role"],
                    "is_staff": user_data.get(
                        "is_staff",
                        False,
                    ),
                    "is_superuser": user_data.get(
                        "is_superuser",
                        False,
                    ),
                },
            )

            if created:

                user.set_password(password)
                user.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Created user: {username}"
                    )
                )

            else:

                self.stdout.write(
                    f"• User already exists: {username}"
                )

            users[username] = user

        # -----------------------------------------------------
        # REVIEWS
        # -----------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "⭐ Creating product reviews..."
            )
        )

        customer = users["demo_customer"]

        review_count = 0

        for index, product in enumerate(
            products.values()
        ):

            rating = [
                5,
                5,
                4,
                5,
                4,
                5,
                4,
                5,
            ][index % 8]

            comment = self.REVIEW_COMMENTS[
                index % len(self.REVIEW_COMMENTS)
            ]

            Review.objects.update_or_create(
                user=customer,
                product=product,
                defaults={
                    "rating": rating,
                    "comment": comment,
                },
            )

            review_count += 1

        # -----------------------------------------------------
        # SUMMARY
        # -----------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "🌱 FreshHarvest seed completed!"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "========================================"
            )
        )

        self.stdout.write("")

        self.stdout.write(
            f"Categories: {Category.objects.count()}"
        )

        self.stdout.write(
            f"Products:   {Product.objects.count()}"
        )

        self.stdout.write(
            f"Reviews:    {Review.objects.count()}"
        )

        self.stdout.write(
            f"Users:      {User.objects.count()}"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Demo customer:"
            )
        )

        self.stdout.write(
            "  Username: Test1"
        )

        self.stdout.write(
            "  Password: Test1234!"
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Admin account:"
            )
        )

        self.stdout.write(
            "  Username: Admin"
        )

        self.stdout.write(
            "  Password: Admin123!"
        )

        self.stdout.write("")