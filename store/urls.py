from django.contrib import admin
from django.urls import path, include
from django.conf import settings             # Imports your settings.py variables
from django.conf.urls.static import static   # Helper function to route static/media paths


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin-dashboard/", include("admin_app.urls")),
    path("", include("app.urls")),
]
# Serve media and static files locally during development (when DEBUG is True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
