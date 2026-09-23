from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "FreshHarvest Profile",
            {
                "fields": (
                    "full_name",
                    "phone_number",
                    "role",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "FreshHarvest Profile",
            {
                "fields": (
                    "full_name",
                    "phone_number",
                    "role",
                )
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "full_name",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "full_name", "phone_number")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock",
        "calories_per_100g",
        "fiber_g",
        "potassium_mg",
        "is_active",
    )
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    fieldsets = (
        (
            "Product Information",
            {
                "fields": (
                    "name",
                    "description",
                    "category",
                    "price",
                    "image",
                    "stock",
                    "is_active",
                )
            },
        ),
        (
            "Nutritional Information — Per 100g",
            {
                "description": (
                    "Enter the nutritional values that will appear in the "
                    "product quick-view modal."
                ),
                "fields": (
                    "calories_per_100g",
                    "fiber_g",
                    "potassium_mg",
                    "vitamin_c_mg",
                    "vitamin_e_mg",
                ),
            },
        ),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")



admin.site.register(Order)
admin.site.register(OrderItem)