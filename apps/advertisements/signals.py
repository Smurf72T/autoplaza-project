# apps/advertisements/signals.py
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CarAd

@receiver(pre_save, sender=CarAd)
def auto_generate_title(sender, instance, **kwargs):
    """Автоматически генерирует заголовок перед сохранением"""
    if not instance.title or instance.title.strip() == '':
        instance.title = instance.generate_title()