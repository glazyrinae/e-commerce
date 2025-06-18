import os
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from PIL import Image
from django.apps import apps
from uuid import uuid4
from datetime import datetime
from io import BytesIO
from .models import Images
from django.core.files.base import ContentFile

#Images = apps.get_model("products", "Images")
import logging
logger = logging.getLogger(__name__)

def rename_image(filename):
    # instance - объект модели
    # filename - оригинальное имя файла
    ext = filename.split(".")[-1]  # получаем расширение файла
    new_name = f"{uuid4().hex}.{ext}"  # генерируем новое имя
    dirname = datetime.now().strftime("%Y/%m/%d")
    return os.path.join(dirname, new_name)  # возвращаем новый путь


@receiver(pre_save, sender=Images)
def generate_thumbnail(sender, instance, **kwargs):
    # При перезаписи
    if instance.pk:
        old_instance = sender.objects.get(pk=instance.pk)
        if (
            instance.image
            and old_instance.image
            and instance.image != old_instance.image
            and os.path.isfile(old_instance.image.path)
        ):
            os.remove(old_instance.image.path)
        if (
            instance.thumbnail
            and old_instance.thumbnail
            and instance.thumbnail != old_instance.thumbnail
            and os.path.isfile(old_instance.thumbnail.path)
        ):
            os.remove(old_instance.thumbnail.path)

    if instance.image:
        try:
            # Открываем изображение
            img = Image.open(instance.image)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((300, 300))
            ext = os.path.splitext(instance.image.name)[1].lower()
            format_mapping = {
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".png": "PNG",
                ".webp": "WEBP",
            }
            img_format = format_mapping.get(ext, "JPEG")  # По умолчанию JPEG
            thumb_io = BytesIO()
            img.save(thumb_io, format=img_format, quality=85)
            if instance.thumbnail and os.path.isfile(instance.thumbnail.path):
                os.remove(instance.thumbnail.path)
            instance.image.name = rename_image(instance.image.name)
            instance.thumbnail.save(
                f"{os.path.basename(instance.image.name)}",
                ContentFile(thumb_io.getvalue()),
                save=False,
            )
        except Exception as e:
            if instance.pk:
                instance.delete()
            raise ValueError(f"Ошибка обработки изображения: {str(e)}")


@receiver(post_delete, sender=Images)
def delete_thumbnail(sender, instance, **kwargs):
    if sender == Images:
        print(instance.image.name)
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)
