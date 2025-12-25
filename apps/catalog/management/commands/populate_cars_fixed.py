# apps/catalog/management/commands/populate_cars_fixed.py
import os
import django
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.catalog.models import CarBrand, CarModel, CarFeature


class Command(BaseCommand):
    help = 'Заполнение базы автомобилями с исправленной загрузкой изображений'

    # User-Agent для обхода блокировок
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # Альтернативные источники изображений (меньшего размера, но доступные)
    IMAGE_SOURCES = {
        'toyota': 'https://www.carlogos.org/car-logos/toyota-logo-2019-3700x1200.png',
        'bmw': 'https://www.carlogos.org/car-logos/bmw-logo-2020-blue-white.png',
        'mercedes-benz': 'https://www.carlogos.org/car-logos/mercedes-benz-logo-2011-1920x1080.png',
        # ... добавьте другие марки
    }

    def handle(self, *args, **options):
        """Основная логика - обновление логотипов"""
        self.update_brand_logos()
        self.stdout.write(self.style.SUCCESS('✅ Логотипы обновлены!'))

    def update_brand_logos(self):
        """Обновление логотипов марок"""
        updated = 0

        for brand in CarBrand.objects.all():
            # Пропускаем марки с уже загруженными логотипами
            if brand.logo:
                continue

            # Пробуем альтернативный источник
            logo_url = self.IMAGE_SOURCES.get(brand.slug.lower())
            if logo_url:
                if self.download_image(brand, 'logo', logo_url):
                    updated += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Логотип загружен для {brand.name}'))
                else:
                    self.stdout.write(self.style.WARNING(f'⚠ Не удалось загрузить логотип для {brand.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'ℹ Нет URL для {brand.name}'))

        self.stdout.write(self.style.SUCCESS(f'✅ Обновлено логотипов: {updated}'))

    def download_image(self, obj, field_name, image_url):
        """Загружает изображение с User-Agent"""
        try:
            response = requests.get(image_url, headers=self.HEADERS, timeout=10)
            if response.status_code == 200:
                filename = f"{obj.slug}_logo.png"

                # Сохраняем изображение
                getattr(obj, field_name).save(
                    filename,
                    ContentFile(response.content),
                    save=True
                )
                return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Ошибка: {e}'))
        return False