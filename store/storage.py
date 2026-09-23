from pathlib import Path

from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from vercel.blob import BlobClient


class VercelBlobStorage(Storage):
    """
    Django storage backend for Vercel Blob.

    Django stores paths such as:
        product_images/avocado.jpg

    Vercel Blob stores the actual files and provides
    the public URL.
    """

    def __init__(self):
        self.client = BlobClient()

    def _open(self, name, mode="rb"):
        result = self.client.get(name, access="public")
        return ContentFile(result.data)

    def _save(self, name, content):
        content_type = getattr(content, "content_type", None)

        if not content_type:
            suffix = Path(name).suffix.lower()

            content_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".svg": "image/svg+xml",
            }

            content_type = content_types.get(
                suffix,
                "application/octet-stream",
            )

        self.client.put(
            name,
            content,
            access="public",
            content_type=content_type,
            overwrite=True,
        )

        return name

    def delete(self, name):
        self.client.delete(name)

    def exists(self, name):
        try:
            self.client.head(name)
            return True
        except Exception:
            return False

    def url(self, name):
        result = self.client.head(name)
        return result.url

    def size(self, name):
        result = self.client.head(name)
        return result.size