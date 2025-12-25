# apps/catalog/management/commands/populate_cars_full.py
import os
import django
import requests
import random
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from apps.catalog.models import CarBrand, CarModel, CarFeature


class Command(BaseCommand):
    help = 'Полное заполнение базы автомобилями с техническими характеристиками'

    # Расширенный список марок
    CAR_BRANDS = [
        {
            'name': 'Toyota',
            'slug': 'toyota',
            'country': 'JP',
            'description': '''Toyota Motor Corporation — японский производитель автомобилей, 
                            один из крупнейших в мире. Основана в 1937 году Киитиро Тойодой. 
                            Известна надежностью, экономичностью и инновационными технологиями 
                            (гибридные системы, водородные автомобили).''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Toyota_carlogo.svg/300px-Toyota_carlogo.svg.png'
        },
        {
            'name': 'BMW',
            'slug': 'bmw',
            'country': 'DE',
            'description': '''Bayerische Motoren Werke AG — немецкий производитель автомобилей 
                            и мотоциклов премиум-класса. Основана в 1916 году. Девиз: "Freude am Fahren" 
                            (Удовольствие за рулем). Известна спортивным характером и инновациями.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/BMW.svg/300px-BMW.svg.png'
        },
        {
            'name': 'Mercedes-Benz',
            'slug': 'mercedes-benz',
            'country': 'DE',
            'description': '''Mercedes-Benz — немецкий производитель автомобилей премиум-класса, 
                            один из старейших автомобильных брендов (1886). Входит в концерн Daimler AG. 
                            Символ роскоши, безопасности и инженерного совершенства.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Mercedes-Logo.svg/300px-Mercedes-Logo.svg.png'
        },
        {
            'name': 'Audi',
            'slug': 'audi',
            'country': 'DE',
            'description': '''Audi AG — немецкий производитель автомобилей премиум-класса, 
                            входит в Volkswagen Group. Основана в 1909 году. Девиз: "Vorsprung durch Technik" 
                            (Прогресс через технологии). Лидер в области полного привода Quattro.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Audi-Logo_2016.svg/300px-Audi-Logo_2016.svg.png'
        },
        {
            'name': 'Volkswagen',
            'slug': 'volkswagen',
            'country': 'DE',
            'description': '''Volkswagen AG — немецкий автомобильный концерн, один из крупнейших 
                            производителей автомобилей в мире. Основан в 1937 году. Знаменит моделями 
                            Golf, Beetle и Passat.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Volkswagen_logo_2019.svg/300px-Volkswagen_logo_2019.svg.png'
        },
        {
            'name': 'Ford',
            'slug': 'ford',
            'country': 'US',
            'description': '''Ford Motor Company — американский производитель автомобилей, 
                            основанный Генри Фордом в 1903 году. Пионер массового автомобилестроения 
                            и конвейерного производства. Легендарные модели: Model T, Mustang, F-Series.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Ford_Motor_Company_Logo.svg/300px-Ford_Motor_Company_Logo.svg.png'
        },
        {
            'name': 'Chevrolet',
            'slug': 'chevrolet',
            'country': 'US',
            'description': '''Chevrolet — американская марка автомобилей, подразделение General Motors. 
                            Основана в 1911 году Луи Шевроле. Известна моделями Camaro, Corvette, Tahoe, 
                            Silverado. Девиз: "Find New Roads".''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Chevrolet_logo.svg/300px-Chevrolet_logo.svg.png'
        },
        {
            'name': 'Hyundai',
            'slug': 'hyundai',
            'country': 'KR',
            'description': '''Hyundai Motor Company — южнокрейский автомобильный концерн, 
                            основан в 1967 году. Один из крупнейших производителей в мире. 
                            Известен длинной гарантией, современным дизайном и хорошим оснащением.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Hyundai_Motor_Company_logo.svg/300px-Hyundai_Motor_Company_logo.svg.png'
        },
        {
            'name': 'Kia',
            'slug': 'kia',
            'country': 'KR',
            'description': '''Kia Motors — южнокрейский производитель автомобилей, 
                            входит в Hyundai Motor Group. Основана в 1944 году. 
                            Известна стильным дизайном, хорошим оснащением и доступными ценами.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Kia_logo3.svg/300px-Kia_logo3.svg.png'
        },
        {
            'name': 'Lada (ВАЗ)',
            'slug': 'lada',
            'country': 'RU',
            'description': '''Lada — российская марка автомобилей, производится АВТОВАЗом. 
                            Основана в 1966 году. Легендарная модель Lada 2101 ("Копейка") 
                            на базе Fiat 124. Популярна в России и странах СНГ.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Lada_logo.png/300px-Lada_logo.png'
        },
        {
            'name': 'Skoda',
            'slug': 'skoda',
            'country': 'CZ',
            'description': '''Škoda Auto — чешский производитель автомобилей, входит в Volkswagen Group. 
                            Основана в 1895 году. Известна соотношением цена/качество, 
                            просторными салонами и практичностью.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/Skoda_Auto_logo_%282016%29.svg/300px-Skoda_Auto_logo_%282016%29.svg.png'
        },
        {
            'name': 'Nissan',
            'slug': 'nissan',
            'country': 'JP',
            'description': '''Nissan Motor Company — японский производитель автомобилей, 
                            основан в 1933 году. Входит в альянс Renault-Nissan-Mitsubishi. 
                            Известен моделями GT-R, Qashqai, X-Trail.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Nissan_2020_logo.svg/300px-Nissan_2020_logo.svg.png'
        },
        {
            'name': 'Honda',
            'slug': 'honda',
            'country': 'JP',
            'description': '''Honda Motor Company — японский производитель автомобилей, 
                            мотоциклов и силовой техники. Основана в 1948 году. 
                            Лидер в области двигателестроения и гибридных технологий.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Honda_Logo.svg/300px-Honda_Logo.svg.png'
        },
        {
            'name': 'Mazda',
            'slug': 'mazda',
            'country': 'JP',
            'description': '''Mazda Motor Corporation — японский производитель автомобилей, 
                            основан в 1920 году. Известен технологией роторных двигателей, 
                            философией "Дзинба иттай" (единство всадника и коня) и дизайном KODO.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Mazda_logo_4.svg/300px-Mazda_logo_4.svg.png'
        },
        {
            'name': 'Subaru',
            'slug': 'subaru',
            'country': 'JP',
            'description': '''Subaru — японский производитель автомобилей, подразделение Subaru Corporation. 
                            Известен полным приводом на всех моделях, оппозитными двигателями 
                            и высоким уровнем безопасности.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/85/Subaru_brand_logo.svg/300px-Subaru_brand_logo.svg.png'
        },
        {
            'name': 'Lexus',
            'slug': 'lexus',
            'country': 'JP',
            'description': '''Lexus — люксовая марка японской компании Toyota Motor Corporation. 
                            Создана в 1989 году для конкуренции с немецкими премиум-брендами. 
                            Символизирует роскошь, качество и бесшумность.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Lexus_logo.svg/300px-Lexus_logo.svg.png'
        },
        {
            'name': 'Renault',
            'slug': 'renault',
            'country': 'FR',
            'description': '''Renault — французский производитель автомобилей, основан в 1899 году. 
                            Входит в альянс Renault-Nissan-Mitsubishi. Известен инновациями 
                            в области электромобилей и компактных автомобилей.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Renault_1992_logo.svg/300px-Renault_1992_logo.svg.png'
        },
        {
            'name': 'Peugeot',
            'slug': 'peugeot',
            'country': 'FR',
            'description': '''Peugeot — французский производитель автомобилей, основан в 1810 году 
                            (самый старый автомобильный бренд). Входит в концерн Stellantis. 
                            Известен дизайном, управляемостью и экономичностью.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f7/Peugeot_Logo.svg/300px-Peugeot_Logo.svg.png'
        },
        {
            'name': 'Citroën',
            'slug': 'citroen',
            'country': 'FR',
            'description': '''Citroën — французский производитель автомобилей, основан в 1919 году. 
                            Входит в концерн Stellantis. Известен инновациями: передний привод, 
                            гидропневматическая подвеска, необычный дизайн.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Citro%C3%ABn_logo.svg/300px-Citro%C3%ABn_logo.svg.png'
        },
        {
            'name': 'Opel',
            'slug': 'opel',
            'country': 'DE',
            'description': '''Opel — немецкий производитель автомобилей, основан в 1862 году. 
                            Принадлежит концерну Stellantis. Популярен в Европе благодаря 
                            практичности, надежности и доступным ценам.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Opel_logo.svg/300px-Opel_logo.svg.png'
        },
        {
            'name': 'Volvo',
            'slug': 'volvo',
            'country': 'SE',
            'description': '''Volvo Cars — шведский производитель автомобилей премиум-класса, 
                            основан в 1927 году. Принадлежит китайской Geely. Символ безопасности, 
                            качества и скандинавского дизайна.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Volvo_Cars_2021_Logo.svg/300px-Volvo_Cars_2021_Logo.svg.png'
        },
        {
            'name': 'Mitsubishi',
            'slug': 'mitsubishi',
            'country': 'JP',
            'description': '''Mitsubishi Motors — японский производитель автомобилей, 
                            основан в 1970 году. Входит в альянс Renault-Nissan-Mitsubishi. 
                            Известен внедорожниками, технологией полного привода и надежностью.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Mitsubishi_Motors_logo.svg/300px-Mitsubishi_Motors_logo.svg.png'
        },
        {
            'name': 'Jeep',
            'slug': 'jeep',
            'country': 'US',
            'description': '''Jeep — американский производитель внедорожников, подразделение Stellantis. 
                            Основан в 1941 году. Легендарный бренд внедорожников, символ свободы 
                            и приключений. Модели: Wrangler, Grand Cherokee, Cherokee.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Jeep_logo.svg/300px-Jeep_logo.svg.png'
        },
        {
            'name': 'Land Rover',
            'slug': 'land-rover',
            'country': 'GB',
            'description': '''Land Rover — британский производитель внедорожников премиум-класса, 
                            входит в Jaguar Land Rover (индийская Tata Motors). Основан в 1948 году. 
                            Символ роскоши и выдающейся проходимости.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Land_Rover_2021_logo.svg/300px-Land_Rover_2021_logo.svg.png'
        },
        {
            'name': 'Porsche',
            'slug': 'porsche',
            'country': 'DE',
            'description': '''Porsche AG — немецкий производитель спортивных автомобилей премиум-класса, 
                            основан в 1931 году Фердинандом Порше. Входит в Volkswagen Group. 
                            Символ скорости, роскоши и инженерного совершенства.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Porsche_logo.svg/300px-Porsche_logo.svg.png'
        },
        {
            'name': 'Tesla',
            'slug': 'tesla',
            'country': 'US',
            'description': '''Tesla, Inc. — американская компания, производитель электромобилей 
                            и решений для хранения энергии. Основана в 2003 году Илоном Маском. 
                            Лидер в области электромобилей и автономного вождения.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Tesla_Motors.svg/300px-Tesla_Motors.svg.png'
        },
        {
            'name': 'Geely',
            'slug': 'geely',
            'country': 'CN',
            'description': '''Geely Auto — китайский производитель автомобилей, основан в 1986 году. 
                            Владеет Volvo Cars, Lotus и доли в Mercedes-Benz Group. 
                            Быстро растущий бренд с современными технологиями.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Geely_Auto_logo_%282014%29.svg/300px-Geely_Auto_logo_%282014%29.svg.png'
        },
        {
            'name': 'Chery',
            'slug': 'chery',
            'country': 'CN',
            'description': '''Chery Automobile — китайский производитель автомобилей, основан в 1997 году. 
                            Один из крупнейших экспортеров автомобилей из Китая. 
                            Известен хорошим соотношением цена/качество.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Chery_Logo.svg/300px-Chery_Logo.svg.png'
        },
        {
            'name': 'Haval',
            'slug': 'haval',
            'country': 'CN',
            'description': '''Haval — китайская марка кроссоверов и внедорожников, 
                            подразделение Great Wall Motors. Основана в 2013 году. 
                            Крупнейший производитель внедорожников в Китае.''',
            'logo_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Haval_logo.svg/300px-Haval_logo.svg.png'
        },
    ]

    # Расширенный список моделей с техническими характеристиками
    CAR_MODELS = [
        # Toyota
        {
            'brand': 'Toyota', 'name': 'Camry', 'slug': 'camry',
            'body_type': 'sedan', 'year_start': 1982, 'year_end': 2024,
            'engine_types': ['2.0L (150 л.с.)', '2.5L (180 л.с.)', '2.5L Hybrid (218 л.с.)'],
            'transmission': ['6MT', '6AT', '8AT', 'CVT'],
            'description': '''Toyota Camry — среднеразмерный седан, один из самых продаваемых 
                            автомобилей в мире. Символ надежности, комфорта и экономичности. 
                            Восьмое поколение (с 2017) отличается спортивным дизайном и 
                            современными системами безопасности.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/2018_Toyota_Camry_%28ASV70R%29_Ascent_sedan_%282018-08-27%29_01.jpg/800px-2018_Toyota_Camry_%28ASV70R%29_Ascent_sedan_%282018-08-27%29_01.jpg'
        },
        {
            'brand': 'Toyota', 'name': 'RAV4', 'slug': 'rav4',
            'body_type': 'suv', 'year_start': 1994, 'year_end': 2024,
            'engine_types': ['2.0L (150 л.с.)', '2.5L (203 л.с.)', '2.5L Hybrid (219 л.с.)'],
            'transmission': ['CVT', '8AT'],
            'description': '''Toyota RAV4 — компактный кроссовер, пионер сегмента SUV. 
                            Пятое поколение (с 2018) построено на платформе TNGA. 
                            Доступен с гибридной и plug-in гибридной силовыми установками. 
                            Отличная проходимость и экономичность.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/2020_Toyota_RAV4_Excel_HEV_CVT_2.5.jpg/800px-2020_Toyota_RAV4_Excel_HEV_CVT_2.5.jpg'
        },
        {
            'brand': 'Toyota', 'name': 'Land Cruiser 300', 'slug': 'land-cruiser-300',
            'body_type': 'suv', 'year_start': 2021, 'year_end': 2024,
            'engine_types': ['3.5L V6 Twin-Turbo (415 л.с.)', '3.3L V6 Diesel (309 л.с.)'],
            'transmission': ['10AT'],
            'description': '''Toyota Land Cruiser 300 — полноразмерный внедорожник люкс-класса. 
                            Легендарная проходимость, роскошный интерьер и передовые технологии. 
                            Безрамная конструкция, постоянный полный привод, блокировки дифференциалов.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/2022_Toyota_Land_Cruiser_300_ZX_%28Republic_of_South_Africa%29_front_view.png/800px-2022_Toyota_Land_Cruiser_300_ZX_%28Republic_of_South_Africa%29_front_view.png'
        },
        {
            'brand': 'Toyota', 'name': 'Corolla', 'slug': 'corolla',
            'body_type': 'sedan', 'year_start': 1966, 'year_end': 2024,
            'engine_types': ['1.6L (122 л.с.)', '1.8L (140 л.с.)', '2.0L (150 л.с.)', '1.8L Hybrid (122 л.с.)'],
            'transmission': ['6MT', 'CVT'],
            'description': '''Toyota Corolla — самый продаваемый автомобиль в истории (более 50 млн). 
                            Компактный, надежный и экономичный. Двенадцатое поколение (с 2018) 
                            построено на платформе TNGA, предлагает современный дизайн и технологии.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/2019_Toyota_Corolla_%28ZWE211R%29_Ascent_sedan_%282019-10-09%29_01.jpg/800px-2019_Toyota_Corolla_%28ZWE211R%29_Ascent_sedan_%282019-10-09%29_01.jpg'
        },
        {
            'brand': 'Toyota', 'name': 'Prius', 'slug': 'prius',
            'body_type': 'hatchback', 'year_start': 1997, 'year_end': 2024,
            'engine_types': ['1.8L Hybrid (122 л.с.)', '1.8L Plug-in Hybrid (122 л.с.)'],
            'transmission': ['CVT'],
            'description': '''Toyota Prius — первый массовый гибридный автомобиль. 
                            Символ экологичности и инноваций. Четвертое поколение (с 2015) 
                            имеет КПД 40%, футуристичный дизайн и передовые системы помощи водителю.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/2016_Toyota_Prius_%28ZVW50R%29_%281%29.jpg/800px-2016_Toyota_Prius_%28ZVW50R%29_%281%29.jpg'
        },

        # BMW
        {
            'brand': 'BMW', 'name': '3 Series', 'slug': '3-series',
            'body_type': 'sedan', 'year_start': 1975, 'year_end': 2024,
            'engine_types': ['2.0L (184 л.с.)', '2.0L (258 л.с.)', '3.0L (374 л.с.)', '2.0L Hybrid (292 л.с.)'],
            'transmission': ['8AT', '6MT'],
            'description': '''BMW 3 Series — компактный премиум-седан, эталон управляемости в своем классе. 
                            Седьмое поколение G20 (с 2018) сочетает спортивный характер с роскошью. 
                            Доступен с задним или полным приводом xDrive.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/BMW_G20_IMG_0167.jpg/800px-BMW_G20_IMG_0167.jpg'
        },
        {
            'brand': 'BMW', 'name': 'X5', 'slug': 'x5',
            'body_type': 'suv', 'year_start': 1999, 'year_end': 2024,
            'engine_types': ['3.0L (340 л.с.)', '4.4L V8 (530 л.с.)', '3.0L Diesel (265 л.с.)',
                             '3.0L Plug-in Hybrid (394 л.с.)'],
            'transmission': ['8AT'],
            'description': '''BMW X5 — среднеразмерный кроссовер премиум-класса, первый SUV BMW. 
                            Четвертое поколение G05 (с 2018) предлагает роскошный интерьер, 
                            передовые технологии и отличную динамику. Плавная и мощная езда.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/2019_BMW_X5_xDrive40i_%28G05%29.jpg/800px-2019_BMW_X5_xDrive40i_%28G05%29.jpg'
        },
        {
            'brand': 'BMW', 'name': '5 Series', 'slug': '5-series',
            'body_type': 'sedan', 'year_start': 1972, 'year_end': 2024,
            'engine_types': ['2.0L (184 л.с.)', '3.0L (340 л.с.)', '2.0L Diesel (190 л.с.)',
                             '2.0L Plug-in Hybrid (292 л.с.)'],
            'transmission': ['8AT'],
            'description': '''BMW 5 Series — бизнес-седан премиум-класса. Идеальный баланс комфорта, 
                            роскоши и спортивной динамики. Седьмое поколение G30 (с 2016) 
                            предлагает полуавтономное вождение и цифровую панель приборов.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/BMW_5er_G30_sedan_IMG_0165.jpg/800px-BMW_5er_G30_sedan_IMG_0165.jpg'
        },
        {
            'brand': 'BMW', 'name': 'X3', 'slug': 'x3',
            'body_type': 'suv', 'year_start': 2003, 'year_end': 2024,
            'engine_types': ['2.0L (184 л.с.)', '2.0L (252 л.с.)', '3.0L (360 л.с.)'],
            'transmission': ['8AT'],
            'description': '''BMW X3 — компактный кроссовер премиум-класса. Третье поколение G01 (с 2017) 
                            построено на новой платформе, предлагает просторный салон, 
                            современные технологии и отличную управляемость.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/2018_BMW_X3_xDrive30d_%28G01%29_wagon_%282018-10-11%29_01.jpg/800px-2018_BMW_X3_xDrive30d_%28G01%29_wagon_%282018-10-11%29_01.jpg'
        },
        {
            'brand': 'BMW', 'name': '7 Series', 'slug': '7-series',
            'body_type': 'sedan', 'year_start': 1977, 'year_end': 2024,
            'engine_types': ['3.0L (286 л.с.)', '4.4L V8 (530 л.с.)', '6.6L V12 (585 л.с.)',
                             '2.0L Plug-in Hybrid (298 л.с.)'],
            'transmission': ['8AT'],
            'description': '''BMW 7 Series — флагманский седан люкс-класса. Шестое поколение G11 (с 2015) 
                            предлагает максимальный комфорт, роскошь и технологии. 
                            Gesture Control, керамические элементы управления, Executive Lounge.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/BMW_7er_G11_IMG_0158.jpg/800px-BMW_7er_G11_IMG_0158.jpg'
        },

        # Mercedes-Benz
        {
            'brand': 'Mercedes-Benz', 'name': 'C-Class', 'slug': 'c-class',
            'body_type': 'sedan', 'year_start': 1993, 'year_end': 2024,
            'engine_types': ['1.5L (170 л.с.)', '2.0L (204 л.с.)', '2.0L (258 л.с.)', '2.0L Diesel (194 л.с.)'],
            'transmission': ['9AT'],
            'description': '''Mercedes-Benz C-Class — компактный премиум-седан. Пятое поколение W206 (с 2021) 
                            заимствует дизайн у S-Class, предлагает цифровую панель, 
                            полуавтономное вождение и гибридные варианты. Элегантность и технологии.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Mercedes-Benz_C_300_4MATIC_Sedan_%28W206%29_IMG_5390.jpg/800px-Mercedes-Benz_C_300_4MATIC_Sedan_%28W206%29_IMG_5390.jpg'
        },
        {
            'brand': 'Mercedes-Benz', 'name': 'E-Class', 'slug': 'e-class',
            'body_type': 'sedan', 'year_start': 1993, 'year_end': 2024,
            'engine_types': ['2.0L (197 л.с.)', '3.0L (367 л.с.)', '2.0L Diesel (194 л.с.)',
                             '2.0L Plug-in Hybrid (313 л.с.)'],
            'transmission': ['9AT'],
            'description': '''Mercedes-Benz E-Class — бизнес-седан премиум-класса. Десятое поколение W213 (с 2016) 
                            сочетает роскошь, комфорт и технологии. Drive Pilot (уровень 3 автономности), 
                            два 12.3-дюймовых экрана, интеллектуальные системы помощи.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Mercedes-Benz_E_200_AMG_Line_%28W213%29_IMG_5316.jpg/800px-Mercedes-Benz_E_200_AMG_Line_%28W213%29_IMG_5316.jpg'
        },

        # Hyundai
        {'brand': 'Hyundai', 'name': 'Santa Fe', 'slug': 'santa-fe', 'body_type': 'suv', 'year_start': 2000,
         'year_end': 2024},
        {'brand': 'Hyundai', 'name': 'Sonata', 'slug': 'sonata', 'body_type': 'sedan', 'year_start': 1985,
         'year_end': 2024},

        # Kia
        {'brand': 'Kia', 'name': 'Sportage', 'slug': 'sportage', 'body_type': 'suv', 'year_start': 1993,
         'year_end': 2024},
        {'brand': 'Kia', 'name': 'Sorento', 'slug': 'sorento', 'body_type': 'suv', 'year_start': 2002,
         'year_end': 2024},

        # Volkswagen
        {'brand': 'Volkswagen', 'name': 'Tiguan', 'slug': 'tiguan', 'body_type': 'suv', 'year_start': 2007,
         'year_end': 2024},
        {'brand': 'Volkswagen', 'name': 'Polo', 'slug': 'polo', 'body_type': 'hatchback', 'year_start': 1975,
         'year_end': 2024},

        # Добавьте другие модели по аналогии...
        # Chevrolet
        {
            'brand': 'Chevrolet', 'name': 'Camaro', 'slug': 'camaro',
            'body_type': 'coupe', 'year_start': 1966, 'year_end': 2024,
            'engine_types': ['2.0L Turbo (275 л.с.)', '3.6L V6 (335 л.с.)', '6.2L V8 (455 л.с.)',
                             '6.2L V8 Supercharged (650 л.с.)'],
            'transmission': ['6MT', '8AT', '10AT'],
            'description': '''Chevrolet Camaro — американский спортивный автомобиль, икона muscle car. 
                            Шестое поколение (с 2015) предлагает современный дизайн, 
                            мощные двигатели и отличную управляемость. Доступен в кузовах купе и кабриолет.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/2018_Chevrolet_Camaro_2SS_%28United_States%29.jpg/800px-2018_Chevrolet_Camaro_2SS_%28United_States%29.jpg'
        },
        {
            'brand': 'Chevrolet', 'name': 'Tahoe', 'slug': 'tahoe',
            'body_type': 'suv', 'year_start': 1992, 'year_end': 2024,
            'engine_types': ['5.3L V8 (355 л.с.)', '6.2L V8 (420 л.с.)', '3.0L Diesel (277 л.с.)'],
            'transmission': ['10AT'],
            'description': '''Chevrolet Tahoe — полноразмерный SUV, популярный в США. 
                            Четвертое поколение (с 2020) предлагает просторный 8-местный салон, 
                            мощные двигатели и все возможности для путешествий с семьей.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/2021_Chevrolet_Tahoe_High_Country_4WD%2C_front_12.7.20.jpg/800px-2021_Chevrolet_Tahoe_High_Country_4WD%2C_front_12.7.20.jpg'
        },

        # Renault
        {
            'brand': 'Renault', 'name': 'Logan', 'slug': 'logan',
            'body_type': 'sedan', 'year_start': 2004, 'year_end': 2024,
            'engine_types': ['1.6L (82 л.с.)', '1.6L (102 л.с.)', '1.5L Diesel (90 л.с.)'],
            'transmission': ['5MT', '4AT'],
            'description': '''Renault Logan — бюджетный седан, очень популярный в России и странах СНГ. 
                            Второе поколение (с 2014) предлагает практичность, надежность 
                            и доступную цену. Идеальный автомобиль для города.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Renault_Logan_%28second_generation%29_%28front%29%2C_Salon_de_l%27auto_2014%2C_Paris.jpg/800px-Renault_Logan_%28second_generation%29_%28front%29%2C_Salon_de_l%27auto_2014%2C_Paris.jpg'
        },
        {
            'brand': 'Renault', 'name': 'Duster', 'slug': 'duster',
            'body_type': 'suv', 'year_start': 2010, 'year_end': 2024,
            'engine_types': ['1.6L (114 л.с.)', '2.0L (143 л.с.)', '1.5L Diesel (109 л.с.)'],
            'transmission': ['5MT', '6MT', 'CVT', '4AT'],
            'description': '''Renault Duster — компактный кроссовер, один из самых популярных в России. 
                            Второе поколение (с 2017) предлагает современный дизайн, 
                            хорошую проходимость и практичность. Доступен с полным приводом.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Renault_Duster_%28second_generation%29_IMG_4308.jpg/800px-Renault_Duster_%28second_generation%29_IMG_4308.jpg'
        },

        # Peugeot
        {
            'brand': 'Peugeot', 'name': '208', 'slug': '208',
            'body_type': 'hatchback', 'year_start': 2012, 'year_end': 2024,
            'engine_types': ['1.2L (75 л.с.)', '1.2L (100 л.с.)', '1.2L (130 л.с.)', '1.5L Diesel (100 л.с.)',
                             'Electric (136 л.с.)'],
            'transmission': ['5MT', '6AT', '8AT'],
            'description': '''Peugeot 208 — супермини, Европейский автомобиль года 2020. 
                            Второе поколение (с 2019) отличается футуристичным дизайном, 
                            3D-панелью приборов i-Cockpit и электрической версией e-208.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/2020_Peugeot_208_Allure_1.2_PureTech_%28cropped%29.jpg/800px-2020_Peugeot_208_Allure_1.2_PureTech_%28cropped%29.jpg'
        },
        {
            'brand': 'Peugeot', 'name': '3008', 'slug': '3008',
            'body_type': 'suv', 'year_start': 2008, 'year_end': 2024,
            'engine_types': ['1.2L (130 л.с.)', '1.6L (180 л.с.)', '2.0L Diesel (150 л.с.)',
                             '1.6L Plug-in Hybrid (225 л.с.)'],
            'transmission': ['6AT', '8AT'],
            'description': '''Peugeot 3008 — компактный кроссовер, Европейский автомобиль года 2017. 
                            Второе поколение (с 2016) предлагает инновационный интерьер i-Cockpit, 
                            передовой дизайн и гибридные силовые установки.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Peugeot_3008_II_%28facelift%29_IMG_4248.jpg/800px-Peugeot_3008_II_%28facelift%29_IMG_4248.jpg'
        },

        # Lada (дополнение)
        {
            'brand': 'Lada (ВАЗ)', 'name': 'Vesta', 'slug': 'vesta',
            'body_type': 'sedan', 'year_start': 2015, 'year_end': 2024,
            'engine_types': ['1.6L (106 л.с.)', '1.6L (113 л.с.)', '1.8L (122 л.с.)'],
            'transmission': ['5MT', '5AMT'],
            'description': '''Lada Vesta — компактный седан, флагман АВТОВАЗа. Разработан с участием 
                            Renault-Nissan. Современный дизайн, хорошая оснащенность для своего класса, 
                            адаптирован к российским дорогам. Доступен в кузовах седан, универсал и кросс.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Lada_Vesta_SW_Cross_IMG_4243.jpg/800px-Lada_Vesta_SW_Cross_IMG_4243.jpg'
        },
        {
            'brand': 'Lada (ВАЗ)', 'name': 'Niva Legend', 'slug': 'niva-legend',
            'body_type': 'suv', 'year_start': 1977, 'year_end': 2024,
            'engine_types': ['1.7L (80 л.с.)', '1.7L (83 л.с.)'],
            'transmission': ['5MT'],
            'description': '''Lada Niva (ныне Niva Legend) — легендарный российский внедорожник. 
                            Производство начато в 1977 году. Постоянный полный привод, блокировка 
                            межосевого дифференциала, рамная конструкция. Идеален для бездорожья.''',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Lada_Niva_%282019%29_IMG_4071.jpg/800px-Lada_Niva_%282019%29_IMG_4071.jpg'
        },

        # Добавьте другие модели по аналогии...
    ]

    # Характеристики автомобилей для заполнения CarFeature
    CAR_FEATURES = [
        # Безопасность
        {'name': 'ABS', 'category': 'safety', 'icon': 'fas fa-car-crash', 'is_filterable': True, 'position': 1},
        {'name': 'ESP', 'category': 'safety', 'icon': 'fas fa-exclamation-triangle', 'is_filterable': True,
         'position': 2},
        {'name': 'Подушки безопасности', 'category': 'safety', 'icon': 'fas fa-shield-alt', 'is_filterable': True,
         'position': 3},
        {'name': 'Круиз-контроль', 'category': 'safety', 'icon': 'fas fa-tachometer-alt', 'is_filterable': True,
         'position': 4},
        {'name': 'Парктроник', 'category': 'safety', 'icon': 'fas fa-car-side', 'is_filterable': True, 'position': 5},
        {'name': 'Камера заднего вида', 'category': 'safety', 'icon': 'fas fa-video', 'is_filterable': True,
         'position': 6},

        # Комфорт
        {'name': 'Кондиционер', 'category': 'comfort', 'icon': 'fas fa-wind', 'is_filterable': True, 'position': 1},
        {'name': 'Климат-контроль', 'category': 'comfort', 'icon': 'fas fa-thermometer-half', 'is_filterable': True,
         'position': 2},
        {'name': 'Электростеклоподъемники', 'category': 'comfort', 'icon': 'fas fa-window-maximize',
         'is_filterable': False, 'position': 3},
        {'name': 'Кожаный салон', 'category': 'comfort', 'icon': 'fas fa-couch', 'is_filterable': True, 'position': 4},
        {'name': 'Электропривод сидений', 'category': 'comfort', 'icon': 'fas fa-chair', 'is_filterable': True,
         'position': 5},
        {'name': 'Подогрев сидений', 'category': 'comfort', 'icon': 'fas fa-temperature-high', 'is_filterable': True,
         'position': 6},
        {'name': 'Подогрев руля', 'category': 'comfort', 'icon': 'fas fa-circle', 'is_filterable': True, 'position': 7},

        # Мультимедиа
        {'name': 'Мультимедийная система', 'category': 'multimedia', 'icon': 'fas fa-music', 'is_filterable': True,
         'position': 1},
        {'name': 'Навигация', 'category': 'multimedia', 'icon': 'fas fa-map-marked-alt', 'is_filterable': True,
         'position': 2},
        {'name': 'Apple CarPlay', 'category': 'multimedia', 'icon': 'fab fa-apple', 'is_filterable': True,
         'position': 3},
        {'name': 'Android Auto', 'category': 'multimedia', 'icon': 'fab fa-android', 'is_filterable': True,
         'position': 4},
        {'name': 'Bluetooth', 'category': 'multimedia', 'icon': 'fas fa-bluetooth', 'is_filterable': False,
         'position': 5},
        {'name': 'Круговой обзор', 'category': 'multimedia', 'icon': 'fas fa-camera-retro', 'is_filterable': True,
         'position': 6},

        # Экстерьер
        {'name': 'Легкосплавные диски', 'category': 'exterior', 'icon': 'fas fa-cog', 'is_filterable': True,
         'position': 1},
        {'name': 'Ксеноновые фары', 'category': 'exterior', 'icon': 'fas fa-lightbulb', 'is_filterable': True,
         'position': 2},
        {'name': 'Светодиодные фары', 'category': 'exterior', 'icon': 'fas fa-lightbulb', 'is_filterable': True,
         'position': 3},
        {'name': 'Люк', 'category': 'exterior', 'icon': 'fas fa-sun', 'is_filterable': True, 'position': 4},
        {'name': 'Панорамная крыша', 'category': 'exterior', 'icon': 'fas fa-sun', 'is_filterable': True,
         'position': 5},

        # Интерьер
        {'name': 'Многофункциональный руль', 'category': 'interior', 'icon': 'fas fa-steering-wheel',
         'is_filterable': False, 'position': 1},
        {'name': 'Цифровая приборная панель', 'category': 'interior', 'icon': 'fas fa-tachometer-alt',
         'is_filterable': True, 'position': 2},
        {'name': 'Бесключевой доступ', 'category': 'interior', 'icon': 'fas fa-key', 'is_filterable': True,
         'position': 3},
        {'name': 'Запуск двигателя кнопкой', 'category': 'interior', 'icon': 'fas fa-power-off', 'is_filterable': True,
         'position': 4},
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Пропустить загрузку изображений'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные'
        )
        parser.add_argument(
            '--models-only',
            action='store_true',
            help='Только модели (без марок и характеристик)'
        )

    def handle(self, *args, **options):
        """Основная логика команды"""

        if options['clear']:
            self.clear_database()

        if not options['models_only']:
            # Создаем марки
            brands_dict = self.create_brands(options)

            # Создаем характеристики
            self.create_features()
        else:
            # Загружаем существующие марки
            brands_dict = {brand.name: brand for brand in CarBrand.objects.all()}

        # Создаем модели
        self.create_models(brands_dict, options)

        self.stdout.write(self.style.SUCCESS(
            f'✅ База успешно заполнена!'
        ))

    def clear_database(self):
        """Очистка базы данных"""
        self.stdout.write(self.style.WARNING('Очистка базы данных...'))
        CarModel.objects.all().delete()
        CarFeature.objects.all().delete()
        CarBrand.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('База очищена'))

    def create_brands(self, options):
        """Создание марок автомобилей"""
        brands_dict = {}

        for brand_data in self.CAR_BRANDS:
            try:
                brand, created = CarBrand.objects.get_or_create(
                    slug=brand_data['slug'],
                    defaults={
                        'name': brand_data['name'],
                        'country': brand_data['country'],
                        'description': brand_data['description'],
                        'is_active': True
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Создана марка: {brand.name}'))

                    # Загружаем логотип
                    if not options['skip_images'] and brand_data.get('logo_url'):
                        self.download_image(brand, 'logo', brand_data['logo_url'])
                else:
                    self.stdout.write(self.style.WARNING(f'↻ Марка уже существует: {brand.name}'))

                brands_dict[brand_data['name']] = brand

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Ошибка создания марки {brand_data["name"]}: {e}'))

        return brands_dict

    def create_features(self):
        """Создание характеристик автомобилей"""
        features_created = 0

        for feature_data in self.CAR_FEATURES:
            try:
                feature, created = CarFeature.objects.get_or_create(
                    name=feature_data['name'],
                    category=feature_data['category'],
                    defaults={
                        'icon': feature_data['icon'],
                        'is_filterable': feature_data['is_filterable'],
                        'position': feature_data['position']
                    }
                )

                if created:
                    features_created += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'✗ Ошибка создания характеристики {feature_data["name"]}: {e}'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'✓ Создано характеристик: {features_created}'
        ))

    def create_models(self, brands_dict, options):
        """Создание моделей автомобилей с техническими характеристиками"""
        models_created = 0

        for model_data in self.CAR_MODELS:
            try:
                brand = brands_dict.get(model_data['brand'])
                if not brand:
                    self.stdout.write(self.style.WARNING(
                        f'⚠ Марка {model_data["brand"]} не найдена для модели {model_data["name"]}'
                    ))
                    continue

                # Формируем полное описание с техническими характеристиками
                full_description = self.get_full_description(model_data)

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
                        'description': full_description
                    }
                )

                if created:
                    models_created += 1

                    # Загружаем изображение модели
                    if not options['skip_images'] and model_data.get('image_url'):
                        self.download_image(model, 'image', model_data['image_url'])

                    # Выводим прогресс
                    if models_created % 5 == 0:
                        self.stdout.write(f'Создано моделей: {models_created}')

                    # Выводим информацию о созданной модели
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Создана модель: {brand.name} {model.name}'
                    ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'✗ Ошибка создания модели {model_data["name"]}: {e}'
                ))

        self.stdout.write(self.style.SUCCESS(
            f'✅ Итого создано моделей: {models_created}'
        ))

    def get_full_description(self, model_data):
        """Генерирует полное описание модели с техническими характеристиками"""
        base_desc = model_data.get('description', '')

        # Добавляем технические характеристики
        tech_info = "\n\n📊 **Технические характеристики:**\n"

        if model_data.get('engine_types'):
            engines = ', '.join(model_data['engine_types'])
            tech_info += f"- Двигатели: {engines}\n"

        if model_data.get('transmission'):
            transmissions = ', '.join(model_data['transmission'])
            tech_info += f"- Коробка передач: {transmissions}\n"

        if model_data.get('body_type'):
            body_types = {
                'sedan': 'Седан',
                'suv': 'Внедорожник (SUV)',
                'hatchback': 'Хэтчбек',
                'coupe': 'Купе',
                'crossover': 'Кроссовер',
                'station_wagon': 'Универсал',
                'minivan': 'Минивэн',
                'pickup': 'Пикап',
                'convertible': 'Кабриолет'
            }
            body_type_ru = body_types.get(model_data['body_type'], model_data['body_type'])
            tech_info += f"- Тип кузова: {body_type_ru}\n"

        if model_data.get('year_start'):
            years = f"{model_data['year_start']}"
            if model_data.get('year_end'):
                if model_data['year_end'] >= datetime.now().year:
                    years += f"-по настоящее время"
                else:
                    years += f"-{model_data['year_end']}"
            tech_info += f"- Годы производства: {years}\n"

        return base_desc + tech_info

    def download_image(self, obj, field_name, image_url):
        """Загружает изображение из интернета"""
        try:
            response = requests.get(image_url, timeout=15)
            if response.status_code == 200:
                filename = image_url.split('/')[-1]

                # Сохраняем изображение
                getattr(obj, field_name).save(
                    filename,
                    ContentFile(response.content),
                    save=True
                )
                return True
            else:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠ Не удалось загрузить изображение (HTTP {response.status_code})'
                ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'  ⚠ Ошибка загрузки изображения: {e}'
            ))
        return False