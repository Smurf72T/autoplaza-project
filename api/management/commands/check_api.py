# management/commands/check_api.py
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
import json


class Command(BaseCommand):
    help = 'Проверка работоспособности API endpoints'

    def handle(self, *args, **options):
        client = Client()

        # Проверка API endpoints
        endpoints = [
            ('advertisements:api_models_by_brand', {'brand_id': 1}),
        ]

        for endpoint_name, params in endpoints:
            try:
                url = reverse(endpoint_name)
                response = client.get(url, params)

                self.stdout.write(f"\nПроверка {endpoint_name}:")
                self.stdout.write(f"  URL: {url}")
                self.stdout.write(f"  Статус: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = json.loads(response.content)
                        self.stdout.write(f"  Ответ: {json.dumps(data, ensure_ascii=False)[:100]}...")
                        self.stdout.write(self.style.SUCCESS("  ✓ Работает"))
                    except json.JSONDecodeError:
                        self.stdout.write(self.style.ERROR("  ✗ Неверный JSON"))
                else:
                    self.stdout.write(self.style.ERROR(f"  ✗ Ошибка HTTP {response.status_code}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Исключение: {str(e)}"))