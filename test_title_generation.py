# test_title_generation.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplaza.settings')
django.setup()

from apps.advertisements.models import CarAd
from apps.catalog.models import CarBrand, CarModel


# Тестовая функция
def test_title_generation():
    print("Тестирование генерации заголовков...")

    # Создаем тестовые данные
    brand = CarBrand.objects.filter(is_active=True).first()
    if not brand:
        print("Нет активных марок в базе данных")
        return

    model = CarModel.objects.filter(brand=brand, is_active=True).first()
    if not model:
        print("Нет активных моделей для марки")
        return

    # Создаем тестовое объявление
    test_ad = CarAd(
        model=model,
        year=2020,
        price=1500000,
        description="Тестовое описание"
    )

    # Генерируем заголовок
    title = test_ad.generate_title()
    print(f"Сгенерированный заголовок: {title}")

    # Проверяем разные сценарии
    test_cases = [
        {"year": 2018, "price": 800000, "expected": f"{brand.name} {model.name} 2018 800 000 ₽"},
        {"year": 2022, "price": None, "expected": f"{brand.name} {model.name} 2022 г.в."},
        {"year": None, "price": 1200000, "expected": f"{brand.name} {model.name} 1 200 000 ₽"},
    ]

    print("\nТестовые сценарии:")
    for i, test_case in enumerate(test_cases, 1):
        test_ad.year = test_case["year"]
        test_ad.price = test_case["price"]
        result = test_ad.generate_title()
        print(f"{i}. Год: {test_case['year']}, Цена: {test_case['price']}")
        print(f"   Результат: {result}")
        print(f"   Ожидалось: {test_case.get('expected', 'N/A')}")
        print()


if __name__ == "__main__":
    test_title_generation()