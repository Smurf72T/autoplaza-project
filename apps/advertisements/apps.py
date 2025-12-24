# apps/advertisements/apps.py
from django.apps import AppConfig

class AdvertisementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.advertisements'
    verbose_name = 'Объявления'