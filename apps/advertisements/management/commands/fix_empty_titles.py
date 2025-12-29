# apps/advertisements/management/commands/fix_empty_titles.py
from django.core.management.base import BaseCommand
from apps.advertisements.models import CarAd


class Command(BaseCommand):
    help = 'Исправляет пустые заголовки'

    def handle(self, *args, **options):
        count = 0
        for ad in CarAd.objects.filter(title__isnull=True) | CarAd.objects.filter(title=''):
            ad.title = ad.generate_title()
            ad.save(update_fields=['title'])
            count += 1
            self.stdout.write(f"Обновлено #{ad.id}: {ad.title}")

        self.stdout.write(self.style.SUCCESS(f'Обновлено {count} объявлений'))