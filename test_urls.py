# test_urls.py (временный файл в корне проекта)
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autoplaza.settings.development')
django.setup()

from django.urls import reverse, NoReverseMatch

urls_to_test = [
    ('advertisements:my_ads', {}),
    ('advertisements:favorites', {}),
    ('advertisements:ad_create', {}),
    ('advertisements:ad_list', {}),
    ('cars:brand_list', {}),
    ('cars:brand_detail', {'slug': 'test'}),
    ('cars:model_list', {}),
    ('cars:model_detail', {'slug': 'test'}),
]

for url_name, kwargs in urls_to_test:
    try:
        result = reverse(url_name, kwargs=kwargs if kwargs else None)
        print(f"✓ {url_name}: {result}")
    except NoReverseMatch as e:
        print(f"✗ {url_name}: {e}")
    except Exception as e:
        print(f"✗ {url_name}: {type(e).__name__} - {e}")