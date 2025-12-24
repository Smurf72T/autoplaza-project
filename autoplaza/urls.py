# autoplaza/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Главная страница через core app
    path('', include('apps.core.urls', namespace='core')),

    # Приложения
    path('users/', include('apps.users.urls', namespace='users')),

    # СНАЧАЛА catalog, так как advertisements зависит от него
    path('catalog/', include('apps.catalog.urls', namespace='cars')),

    # ПОТОМ advertisements
    path('advertisements/', include('apps.advertisements.urls', namespace='advertisements')),

    # API версия 1
    path('api/v1/', include('api.urls', namespace='api')),

    # Остальные приложения
    path('reviews/', include('apps.reviews.urls', namespace='reviews')),
    path('analytics/', include('apps.analytics.urls', namespace='analytics')),
    path('chat/', include('apps.chat.urls', namespace='chat')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
]

# Статические файлы
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Django Debug Toolbar
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]


handler400 = 'apps.core.views.handler400'
handler403 = 'apps.core.views.handler403'
handler404 = 'apps.core.views.handler404'
handler500 = 'apps.core.views.handler500'