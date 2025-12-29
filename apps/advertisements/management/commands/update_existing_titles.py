# apps/advertisements/management/commands/update_existing_titles.py
import os
import sys
import django

from django.core.management.base import BaseCommand
from apps.advertisements.models import CarAd


class Command(BaseCommand):
    help = 'Обновляет заголовки существующих объявлений'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет изменено без сохранения',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Ограничить количество обрабатываемых объявлений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']

        # Получаем объявления
        queryset = CarAd.objects.all()
        if limit:
            queryset = queryset[:limit]

        updated_count = 0
        total_count = queryset.count()

        self.stdout.write(f"Найдено {total_count} объявлений для обработки")

        for ad in queryset:
            # Генерируем новый заголовок
            new_title = ad.generate_title()

            # Проверяем, нужно ли обновлять
            if not ad.title or ad.title.strip() == '' or ad.title != new_title:
                if dry_run:
                    self.stdout.write(f"[DRY RUN] Обновление #{ad.id}: '{ad.title}' -> '{new_title}'")
                else:
                    old_title = ad.title
                    ad.title = new_title
                    ad.save(update_fields=['title'])
                    self.stdout.write(f"Обновлено #{ad.id}: '{old_title}' -> '{new_title}'")

                updated_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Было бы обновлено {updated_count} из {total_count} объявлений"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Обновлено {updated_count} из {total_count} объявлений"
                )
            )