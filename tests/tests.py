# tests\test.py
from django.test import TestCase
from django.urls import reverse


class CarAdListViewTest(TestCase):
    def setUp(self):
        # Создание тестовых данных
        self.brand = CarBrand.objects.create(name="Test Brand")
        self.model = CarModel.objects.create(brand=self.brand, name="Test Model")
        self.ad = CarAd.objects.create(
            title="Test Ad",
            model=self.model,
            price=1000000,
            year=2020,
            status='active'
        )

    def test_view_url_exists(self):
        response = self.client.get(reverse('core:ad_list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('core:ad_list'))
        self.assertTemplateUsed(response, 'advertisements/ad_list.html')

    def test_filter_by_brand(self):
        response = self.client.get(f'{reverse("core:ad_list")}?brand={self.brand.id}')
        self.assertContains(response, self.ad.title)

    def test_pagination(self):
        # Создаем много объявлений для проверки пагинации
        for i in range(25):
            CarAd.objects.create(
                title=f"Test Ad {i}",
                model=self.model,
                price=1000000 + i * 100000,
                year=2020,
                status='active'
            )

        response = self.client.get(reverse('core:ad_list'))
        self.assertTrue('is_paginated' in response.context)
        self.assertTrue(response.context['is_paginated'])