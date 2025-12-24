# apps/analytics/views.py
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import PageView, SearchAnalytics, UserActivity, DailyStats
from apps.advertisements.models import CarAd
from apps.users.models import User
from apps.catalog.models import CarBrand, CarModel


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Дашборд аналитики (только для администраторов и дилеров)"""
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Проверяем права
        if not (user.is_staff or hasattr(user, 'dealer')):
            context['no_access'] = True
            return context

        # Период для статистики (последние 30 дней)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Статистика по пользователям
        context['total_users'] = User.objects.count()
        context['new_users'] = User.objects.filter(
            date_joined__gte=start_date
        ).count()
        context['active_users'] = User.objects.filter(
            last_login__gte=start_date
        ).count()

        # Статистика по объявлениям
        context['total_ads'] = CarAd.objects.count()
        context['active_ads'] = CarAd.objects.filter(
            status='active',
            is_active=True
        ).count()
        context['new_ads'] = CarAd.objects.filter(
            created_at__gte=start_date
        ).count()

        # Просмотры
        context['total_views'] = CarAd.objects.aggregate(
            total=Sum('views_count')
        )['total'] or 0

        # Популярные марки
        context['popular_brands'] = CarBrand.objects.annotate(
            ad_count=Count('models__ads', filter=Q(models__ads__status='active'))
        ).order_by('-ad_count')[:10]

        # Ежедневная статистика для графика
        daily_stats = DailyStats.objects.filter(
            date__gte=start_date
        ).order_by('date')

        context['daily_stats'] = daily_stats

        return context


class AdStatsView(LoginRequiredMixin, View):
    """Статистика по объявлениям пользователя"""

    def get(self, request, *args, **kwargs):
        user = request.user
        period = request.GET.get('period', 'month')  # day, week, month, year

        # Определяем период
        end_date = timezone.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:  # month
            start_date = end_date - timedelta(days=30)

        # Получаем объявления пользователя
        user_ads = CarAd.objects.filter(
            owner=user,
            created_at__gte=start_date
        )

        # Статистика
        total_ads = user_ads.count()
        active_ads = user_ads.filter(status='active', is_active=True).count()
        sold_ads = user_ads.filter(status='sold').count()
        total_views = user_ads.aggregate(total=Sum('views_count'))['total'] or 0

        # Средние значения
        avg_price = user_ads.aggregate(avg=Avg('price'))['avg'] or 0
        avg_views = user_ads.aggregate(avg=Avg('views_count'))['avg'] or 0

        data = {
            'period': period,
            'total_ads': total_ads,
            'active_ads': active_ads,
            'sold_ads': sold_ads,
            'total_views': total_views,
            'avg_price': float(avg_price),
            'avg_views': float(avg_views),
            'period_days': (end_date - start_date).days,
        }

        return JsonResponse(data)


class TrafficStatsView(LoginRequiredMixin, View):
    """Статистика трафика"""

    def get(self, request, *args, **kwargs):
        # Для администраторов
        if not request.user.is_staff:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        period = request.GET.get('period', 'week')

        # Определяем период
        end_date = timezone.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
            interval = 'hour'
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
            interval = 'day'
        else:  # week
            start_date = end_date - timedelta(days=7)
            interval = 'day'

        # Получаем статистику
        page_views = PageView.objects.filter(
            viewed_at__gte=start_date
        ).extra(
            select={'interval': f"DATE_TRUNC('{interval}', viewed_at)"}
        ).values('interval').annotate(
            views=Count('id'),
            unique_visitors=Count('session_id', distinct=True)
        ).order_by('interval')

        # Форматируем данные для графика
        labels = []
        views_data = []
        visitors_data = []

        for stat in page_views:
            if interval == 'hour':
                labels.append(stat['interval'].strftime('%H:%M'))
            else:
                labels.append(stat['interval'].strftime('%d.%m'))

            views_data.append(stat['views'])
            visitors_data.append(stat['unique_visitors'])

        data = {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Просмотры',
                    'data': views_data,
                    'borderColor': 'rgb(75, 192, 192)',
                    'tension': 0.1
                },
                {
                    'label': 'Уникальные посетители',
                    'data': visitors_data,
                    'borderColor': 'rgb(255, 99, 132)',
                    'tension': 0.1
                }
            ]
        }

        return JsonResponse(data)


class PopularSearchesView(LoginRequiredMixin, View):
    """Популярные поисковые запросы"""

    def get(self, request, *args, **kwargs):
        # Для администраторов
        if not request.user.is_staff:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        period = request.GET.get('period', 'day')  # day, week, month
        limit = int(request.GET.get('limit', 20))

        # Определяем период
        end_date = timezone.now()
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=1)

        # Получаем популярные запросы
        popular_searches = SearchAnalytics.objects.filter(
            searched_at__gte=start_date
        ).values('query').annotate(
            count=Count('id'),
            with_results=Count('id', filter=Q(has_results=True)),
            with_clicks=Count('id', filter=Q(clicked_result__isnull=False))
        ).order_by('-count')[:limit]

        # Форматируем данные
        data = [
            {
                'query': item['query'],
                'count': item['count'],
                'with_results': item['with_results'],
                'with_clicks': item['with_clicks'],
                'success_rate': round((item['with_clicks'] / item['count']) * 100, 1) if item['count'] > 0 else 0
            }
            for item in popular_searches
        ]

        return JsonResponse({'searches': data})


class TopAdsView(LoginRequiredMixin, View):
    """Топ объявлений по просмотрам"""

    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', 'week')
        limit = int(request.GET.get('limit', 10))

        # Определяем период
        end_date = timezone.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:  # week
            start_date = end_date - timedelta(days=7)

        # Получаем топ объявлений
        top_ads = CarAd.objects.filter(
            created_at__gte=start_date,
            status='active'
        ).select_related('model__brand').order_by('-views_count')[:limit]

        data = [
            {
                'id': ad.id,
                'title': ad.title,
                'brand': ad.model.brand.name,
                'model': ad.model.name,
                'year': ad.year,
                'price': float(ad.price),
                'views': ad.views_count,
                'url': ad.get_absolute_url() if hasattr(ad, 'get_absolute_url') else f'/advertisements/{ad.id}/',
                'created_at': ad.created_at.strftime('%d.%m.%Y')
            }
            for ad in top_ads
        ]

        return JsonResponse({'advertisements': data})

class UserStatsView(LoginRequiredMixin, View):
    """Статистика по пользователям (только для администраторов)"""

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        period = request.GET.get('period', 'month')

        # Определяем период
        end_date = timezone.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:  # month
            start_date = end_date - timedelta(days=30)

        # Статистика пользователей
        total_users = User.objects.count()
        new_users = User.objects.filter(date_joined__gte=start_date).count()
        active_users = User.objects.filter(last_login__gte=start_date).count()

        # Распределение по типам пользователей
        user_types = User.objects.values('user_type').annotate(
            count=Count('id')
        )

        data = {
            'period': period,
            'total_users': total_users,
            'new_users': new_users,
            'active_users': active_users,
            'user_types': list(user_types),
            'period_days': (end_date - start_date).days,
        }

        return JsonResponse(data)


class DailyStatsAPIView(LoginRequiredMixin, View):
    """API для ежедневной статистики"""

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        stats = DailyStats.objects.filter(
            date__gte=start_date
        ).order_by('date')

        data = [
            {
                'date': stat.date.strftime('%Y-%m-%d'),
                'visitors': stat.visitors,
                'page_views': stat.page_views,
                'new_users': stat.new_users,
                'new_ads': stat.new_ads,
            }
            for stat in stats
        ]

        return JsonResponse({'stats': data})


class PopularSearchesAPIView(LoginRequiredMixin, View):
    """API для популярных поисков"""

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        # Просто используем существующий класс
        return PopularSearchesView.as_view()(request, *args, **kwargs)


class TopAdsAPIView(LoginRequiredMixin, View):
    """API для топ объявлений"""

    def get(self, request, *args, **kwargs):
        # Просто используем существующий класс
        return TopAdsView.as_view()(request, *args, **kwargs)


class ConversionStatsView(LoginRequiredMixin, View):
    """Статистика конверсий"""

    def get(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        period = request.GET.get('period', 'month')

        end_date = timezone.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        else:  # month
            start_date = end_date - timedelta(days=30)

        # Здесь должна быть логика расчета конверсий
        # Например, процент просмотров, которые привели к контакту

        data = {
            'period': period,
            'total_views': 0,
            'total_contacts': 0,
            'conversion_rate': 0.0,
        }

        return JsonResponse(data)