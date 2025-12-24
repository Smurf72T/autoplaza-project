# api/docs/urls.py
from django.urls import path
from rest_framework.schemas import get_schema_view
from drf_yasg.views import get_schema_view as yasg_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = yasg_schema_view(
    openapi.Info(
        title="Autoplaza API",
        default_version='v1',
        description="API documentation for Autoplaza",
        contact=openapi.Contact(email="support@autoplaza.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('openapi/', get_schema_view(
        title="Autoplaza API",
        description="API for car marketplace",
        version="1.0.0"
    ), name='openapi-schema'),
]