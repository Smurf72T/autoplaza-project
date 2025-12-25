# apps/catalog/management/commands/populate_cars.py
import os
import django
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from apps.catalog.models import CarBrand, CarModel


class Command(BaseCommand):
    help = 'Заполняет базу данных популярными марками и моделями автомобилей'

    # Данные для заполнения (базовый набор)
    CAR_BRANDS = [
        {
            'name': 'Toyota',
            'slug': 'toyota',
            'country': 'JP',
            'description': 'Японский автопроизводитель, один из крупнейших в мире. Известен надежностью, экономичностью и передовыми технологиями.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Toyota_carlogo.svg/300px-Toyota_carlogo.svg.png'
        },
        {
            'name': 'BMW',
            'slug': 'bmw',
            'country': 'DE',
            'description': 'Немецкий производитель автомобилей и мотоциклов премиум-класса. Девиз компании: "Удовольствие за рулем".',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/BMW.svg/300px-BMW.svg.png'
        },
        {
            'name': 'Mercedes-Benz',
            'slug': 'mercedes-benz',
            'country': 'DE',
            'description': 'Немецкий производитель автомобилей премиум-класса, один из старейших автомобильных брендов в мире.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Mercedes-Logo.svg/300px-Mercedes-Logo.svg.png'
        },
        {
            'name': 'Audi',
            'slug': 'audi',
            'country': 'DE',
            'description': 'Немецкий производитель автомобилей премиум-класса, входящий в состав концерна Volkswagen Group.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Audi-Logo_2016.svg/300px-Audi-Logo_2016.svg.png'
        },
        {
            'name': 'Volkswagen',
            'slug': 'volkswagen',
            'country': 'DE',
            'description': 'Немецкий автомобильный концерн, один из крупнейших производителей автомобилей в мире.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Volkswagen_logo_2019.svg/300px-Volkswagen_logo_2019.svg.png'
        },
        {
            'name': 'Ford',
            'slug': 'ford',
            'country': 'US',
            'description': 'Американский производитель автомобилей, основанный Генри Фордом. Пионер массового автомобилестроения.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Ford_Motor_Company_Logo.svg/300px-Ford_Motor_Company_Logo.svg.png'
        },
        {
            'name': 'Hyundai',
            'slug': 'hyundai',
            'country': 'KR',
            'description': 'Южнокорейский автомобильный концерн, один из крупнейших производителей автомобилей в мире.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Hyundai_Motor_Company_logo.svg/300px-Hyundai_Motor_Company_logo.svg.png'
        },
        {
            'name': 'Kia',
            'slug': 'kia',
            'country': 'KR',
            'description': 'Южнокорейский производитель автомобилей, входящий в Hyundai Motor Group.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Kia_logo3.svg/300px-Kia_logo3.svg.png'
        },
        {
            'name': 'Lada (ВАЗ)',
            'slug': 'lada',
            'country': 'RU',
            'description': 'Российский производитель автомобилей, выпускающий автомобили под маркой Lada.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Lada_logo.png/300px-Lada_logo.png'
        },
        {
            'name': 'Skoda',
            'slug': 'skoda',
            'country': 'CZ',
            'description': 'Чешский производитель автомобилей, входящий в состав концерна Volkswagen Group.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Skoda_Auto_logo_%282016%29.svg/300px-Skoda_Auto_logo_%282016%29.svg.png'
        },
        {
            'name': 'Nissan',
            'slug': 'nissan',
            'country': 'JP',
            'description': 'Японский производитель автомобилей, один из крупнейших в мире. Входит в альянс Renault-Nissan-Mitsubishi.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Nissan_2020_logo.svg/300px-Nissan_2020_logo.svg.png'
        },
        {
            'name': 'Honda',
            'slug': 'honda',
            'country': 'JP',
            'description': 'Японский производитель автомобилей, мотоциклов и силовой техники.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Honda_Logo.svg/300px-Honda_Logo.svg.png'
        },
        {
            'name': 'Mazda',
            'slug': 'mazda',
            'country': 'JP',
            'description': 'Японский производитель автомобилей, известный технологией роторных двигателей и философией "Дзинба иттай".',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Mazda_logo_4.svg/300px-Mazda_logo_4.svg.png'
        },
        {
            'name': 'Subaru',
            'slug': 'subaru',
            'country': 'JP',
            'description': 'Японский производитель автомобилей, известный полным приводом на всех моделях и оппозитными двигателями.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Subaru_brand_logo.svg/300px-Subaru_brand_logo.svg.png'
        },
        {
            'name': 'Lexus',
            'slug': 'lexus',
            'country': 'JP',
            'description': 'Люксовая марка японской компании Toyota Motor Corporation.',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Lexus_logo.svg/300px-Lexus_logo.svg.png'
        },
    ]

    CAR_MODELS = [
        # Toyota
        {'brand': 'Toyota', 'name': 'Camry', 'slug': 'camry', 'body_type': 'sedan', 'year_start': 1982,
         'year_end': 2024},
        {'brand': 'Toyota', 'name': 'Corolla', 'slug': 'corolla', 'body_type': 'sedan', 'year_start': 1966,
         'year_end': 2024},
        {'brand': 'Toyota', 'name': 'RAV4', 'slug': 'rav4', 'body_type': 'suv', 'year_start': 1994, 'year_end': 2024},
        {'brand': 'Toyota', 'name': 'Land Cruiser', 'slug': 'land-cruiser', 'body_type': 'suv', 'year_start': 1951,
         'year_end': 2024},
        {'brand': 'Toyota', 'name': 'Prius', 'slug': 'prius', 'body_type': 'hatchback', 'year_start': 1997,
         'year_end': 2024},

        # BMW
        {'brand': 'BMW', 'name': '3 Series', 'slug': '3-series', 'body_type': 'sedan', 'year_start': 1975,
         'year_end': 2024},
        {'brand': 'BMW', 'name': '5 Series', 'slug': '5-series', 'body_type': 'sedan', 'year_start': 1972,
         'year_end': 2024},
        {'brand': 'BMW', 'name': 'X5', 'slug': 'x5', 'body_type': 'suv', 'year_start': 1999, 'year_end': 2024},
        {'brand': 'BMW', 'name': 'X3', 'slug': 'x3', 'body_type': 'suv', 'year_start': 2003, 'year_end': 2024},
        {'brand': 'BMW', 'name': '7 Series', 'slug': '7-series', 'body_type': 'sedan', 'year_start': 1977,
         'year_end': 2024},

        # Mercedes-Benz
        {'brand': 'Mercedes-Benz', 'name': 'C-Class', 'slug': 'c-class', 'body_type': 'sedan', 'year_start': 1993,
         'year_end': 2024},
        {'brand': 'Mercedes-Benz', 'name': 'E-Class', 'slug': 'e-class', 'body_type': 'sedan', 'year_start': 1993,
         'year_end': 2024},
        {'brand': 'Mercedes-Benz', 'name': 'S-Class', 'slug': 's-class', 'body_type': 'sedan', 'year_start': 1972,
         'year_end': 2024},
        {'brand': 'Mercedes-Benz', 'name': 'GLC', 'slug': 'glc', 'body_type': 'suv', 'year_start': 2015,
         'year_end': 2024},
        {'brand': 'Mercedes-Benz', 'name': 'GLE', 'slug': 'gle', 'body_type': 'suv', 'year_start': 2015,
         'year_end': 2024},

        # Audi
        {'brand': 'Audi', 'name': 'A4', 'slug': 'a4', 'body_type': 'sedan', 'year_start': 1994, 'year_end': 2024},
        {'brand': 'Audi', 'name': 'A6', 'slug': 'a6', 'body_type': 'sedan', 'year_start': 1994, 'year_end': 2024},
        {'brand': 'Audi', 'name': 'Q5', 'slug': 'q5', 'body_type': 'suv', 'year_start': 2008, 'year_end': 2024},
        {'brand': 'Audi', 'name': 'Q7', 'slug': 'q7', 'body_type': 'suv', 'year_start': 2005, 'year_end': 2024},
        {'brand': 'Audi', 'name': 'A3', 'slug': 'a3', 'body_type': 'hatchback', 'year_start': 1996, 'year_end': 2024},

        # Volkswagen
        {'brand': 'Volkswagen', 'name': 'Golf', 'slug': 'golf', 'body_type': 'hatchback', 'year_start': 1974,
         'year_end': 2024},
        {'brand': 'Volkswagen', 'name': 'Passat', 'slug': 'passat', 'body_type': 'sedan', 'year_start': 1973,
         'year_end': 2024},
        {'brand': 'Volkswagen', 'name': 'Tiguan', 'slug': 'tiguan', 'body_type': 'suv', 'year_start': 2007,
         'year_end': 2024},
        {'brand': 'Volkswagen', 'name': 'Polo', 'slug': 'polo', 'body_type': 'hatchback', 'year_start': 1975,
         'year_end': 2024},
        {'brand': 'Volkswagen', 'name': 'Touareg', 'slug': 'touareg', 'body_type': 'suv', 'year_start': 2002,
         'year_end': 2024},

        # Lada (ВАЗ)
        {'brand': 'Lada (ВАЗ)', 'name': 'Granta', 'slug': 'granta', 'body_type': 'sedan', 'year_start': 2011,
         'year_end': 2024},
        {'brand': 'Lada (ВАЗ)', 'name': 'Vesta', 'slug': 'vesta', 'body_type': 'sedan', 'year_start': 2015,
         'year_end': 2024},
        {'brand': 'Lada (ВАЗ)', 'name': 'Niva', 'slug': 'niva', 'body_type': 'suv', 'year_start': 1977,
         'year_end': 2024},
        {'brand': 'Lada (ВАЗ)', 'name': 'Largus', 'slug': 'largus', 'body_type': 'station_wagon', 'year_start': 2012,
         'year_end': 2024},
        {'brand': 'Lada (ВАЗ)', 'name': 'XRAY', 'slug': 'xray', 'body_type': 'crossover', 'year_start': 2015,
         'year_end': 2024},

        # Hyundai
        {'brand': 'Hyundai', 'name': 'Solaris', 'slug': 'solaris', 'body_type': 'sedan', 'year_start': 2010,
         'year_end': 2024},
        {'brand': 'Hyundai', 'name': 'Creta', 'slug': 'creta', 'body_type': 'suv', 'year_start': 2014,
         'year_end': 2024},
        {'brand': 'Hyundai', 'name': 'Tucson', 'slug': 'tucson', 'body_type': 'suv', 'year_start': 2004,
         'year_end': 2024},
        {'brand': 'Hyundai', 'name': 'Santa Fe', 'slug': 'santa-fe', 'body_type': 'suv', 'year_start': 2000,
         'year_end': 2024},
        {'brand': 'Hyundai', 'name': 'Sonata', 'slug': 'sonata', 'body_type': 'sedan', 'year_start': 1985,
         'year_end': 2024},

        # Kia
        {'brand': 'Kia', 'name': 'Rio', 'slug': 'rio', 'body_type': 'sedan', 'year_start': 1999, 'year_end': 2024},
        {'brand': 'Kia', 'name': 'Sportage', 'slug': 'sportage', 'body_type': 'suv', 'year_start': 1993,
         'year_end': 2024},
        {'brand': 'Kia', 'name': 'Sorento', 'slug': 'sorento', 'body_type': 'suv', 'year_start': 2002,
         'year_end': 2024},
        {'brand': 'Kia', 'name': 'Optima', 'slug': 'optima', 'body_type': 'sedan', 'year_start': 2000,
         'year_end': 2024},
        {'brand': 'Kia', 'name': 'Cerato', 'slug': 'cerato', 'body_type': 'sedan', 'year_start': 2003,
         'year_end': 2024},

        # Добавьте другие модели по аналогии...
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Пропустить загрузку изображений (только текстовые данные)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед заполнением'
        )

    def handle(self, *args, **options):
        """Основная логика команды"""

        if options['clear']:
            self.stdout.write(self.style.WARNING('Очистка существующих данных...'))
            CarModel.objects.all().delete()
            CarBrand.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Данные очищены'))

        # Создаем марки
        brands_dict = self.create_brands(options)

        # Создаем модели
        self.create_models(brands_dict, options)

        self.stdout.write(self.style.SUCCESS(
            f'✅ Успешно добавлено {len(brands_dict)} марок и {len(self.CAR_MODELS)} моделей автомобилей!'
        ))

    def create_brands(self, options):
        """Создание марок автомобилей"""
        brands_dict = {}

        for brand_data in self.CAR_BRANDS:
            try:
                # Проверяем, существует ли уже марка
                brand, created = CarBrand.objects.get_or_create(
                    slug=brand_data['slug'],
                    defaults={
                        'name': brand_data['name'],
                        'country': brand_data['country'],
                        'description': brand_data.get('description', ''),
                        'is_active': True
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Создана марка: {brand.name}'))

                    # Загружаем логотип
                    if not options['skip_images'] and brand_data.get('logo_url'):
                        self.download_logo(brand, brand_data['logo_url'])
                else:
                    self.stdout.write(self.style.WARNING(f'Марка уже существует: {brand.name}'))

                brands_dict[brand_data['name']] = brand

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка создания марки {brand_data["name"]}: {e}'))

        return brands_dict

    def create_models(self, brands_dict, options):
        """Создание моделей автомобилей"""
        models_created = 0

        for model_data in self.CAR_MODELS:
            try:
                brand = brands_dict.get(model_data['brand'])
                if not brand:
                    self.stdout.write(self.style.WARNING(
                        f'Марка {model_data["brand"]} не найдена для модели {model_data["name"]}'
                    ))
                    continue

                # Создаем или получаем модель
                model, created = CarModel.objects.get_or_create(
                    slug=model_data['slug'],
                    defaults={
                        'brand': brand,
                        'name': model_data['name'],
                        'body_type': model_data.get('body_type', ''),
                        'year_start': model_data.get('year_start'),
                        'year_end': model_data.get('year_end'),
                        'is_active': True,
                        'description': self.get_model_description(model_data)
                    }
                )

                if created:
                    models_created += 1
                    if models_created % 10 == 0:
                        self.stdout.write(f'Создано моделей: {models_created}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Ошибка создания модели {model_data["name"]}: {e}'
                ))

        self.stdout.write(self.style.SUCCESS(f'Создано моделей: {models_created}'))

    def download_logo(self, brand, logo_url):
        """Загружает логотип из интернета"""
        try:
            response = requests.get(logo_url, timeout=10)
            if response.status_code == 200:
                # Получаем расширение файла из URL
                filename = logo_url.split('/')[-1]

                # Сохраняем изображение
                brand.logo.save(
                    filename,
                    ContentFile(response.content),
                    save=True
                )
                self.stdout.write(f'  Логотип загружен для {brand.name}')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Не удалось загрузить логотип для {brand.name} (HTTP {response.status_code})'
                ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'  Ошибка загрузки логотипа для {brand.name}: {e}'
            ))

    def get_model_description(self, model_data):
        """Генерирует описание для модели"""
        descriptions = {
            'sedan': 'Классический четырехдверный седан с просторным салоном и багажником.',
            'suv': 'Внедорожник с повышенной проходимостью и просторным салоном.',
            'hatchback': 'Компактный автомобиль с пятидверным кузовом и практичным багажником.',
            'crossover': 'Городской кроссовер, сочетающий комфорт седана и проходимость внедорожника.',
            'station_wagon': 'Универсал с увеличенным багажным отделением.',
            'coupe': 'Спортивное купе с динамичным дизайном.',
        }

        body_type = model_data.get('body_type', '')
        base_desc = descriptions.get(body_type, 'Популярная модель автомобиля.')

        return f"{model_data['name']} - {base_desc} Годы производства: {model_data.get('year_start', 'N/A')}-{model_data.get('year_end', 'по н.в.')}."