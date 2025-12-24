# migrate-structure-simple.ps1

Write-Host "=== Миграция структуры проекта ===" -ForegroundColor Green

# 1. Проверяем существование директории autoplaza
if (-not (Test-Path "autoplaza")) {
    Write-Host "ОШИБКА: Директория 'autoplaza' не найдена!" -ForegroundColor Red
    Write-Host "Текущая директория: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

Write-Host "1. Создание новой структуры..." -ForegroundColor Cyan

# Создаем директории apps
$apps = "core", "users", "advertisements", "catalog", "chat", "reviews", "analytics", "payments"
foreach ($app in $apps) {
    $dir = "backend\apps\$app"
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "   Создано: $dir" -ForegroundColor Gray
    }
}

# Создаем __init__.py файлы
foreach ($app in $apps) {
    $initFile = "backend\apps\$app\__init__.py"
    if (-not (Test-Path $initFile)) {
        "" | Out-File -FilePath $initFile -Encoding UTF8
    }
}

# Создаем apps __init__.py
if (-not (Test-Path "backend\apps\__init__.py")) {
    "" | Out-File -FilePath "backend\apps\__init__.py" -Encoding UTF8
}

Write-Host "2. Перемещение файлов из autoplaza/ в backend/apps/core/..." -ForegroundColor Cyan

# Список файлов для перемещения
$filesToMove = @(
    "models.py",
    "admin.py",
    "apps.py",
    "views.py",
    "urls.py",
    "tests.py",
    "signals.py",
    "celery.py",
    "__init__.py"
)

$movedCount = 0
foreach ($file in $filesToMove) {
    $source = "autoplaza\$file"
    $destination = "backend\apps\core\$file"

    if (Test-Path $source) {
        Move-Item $source $destination -Force
        $movedCount++
        Write-Host "   Перемещено: $file" -ForegroundColor Green
    }
}

Write-Host "   Всего перемещено файлов: $movedCount" -ForegroundColor Green

# Перемещаем миграции если есть
Write-Host "3. Обработка миграций..." -ForegroundColor Cyan
if (Test-Path "autoplaza\migrations") {
    $migrationFiles = Get-ChildItem "autoplaza\migrations" -File
    if ($migrationFiles.Count -gt 0) {
        New-Item -ItemType Directory -Path "backend\apps\core\migrations" -Force | Out-Null
        foreach ($file in $migrationFiles) {
            Copy-Item $file.FullName "backend\apps\core\migrations\$($file.Name)" -Force
        }
        Write-Host "   Миграции скопированы: $($migrationFiles.Count) файлов" -ForegroundColor Green
    }
}

# Переименовываем старую директорию
Write-Host "4. Резервное копирование старой структуры..." -ForegroundColor Cyan
if (Test-Path "autoplaza") {
    Rename-Item "autoplaza" "autoplaza_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Force
    Write-Host "   Старая директория переименована" -ForegroundColor Yellow
}

# Создаем базовый Django проект если нужно
Write-Host "5. Создание базовой структуры Django проекта..." -ForegroundColor Cyan

# Создаем директорию проекта если её нет
if (-not (Test-Path "backend\autoplaza")) {
    New-Item -ItemType Directory -Path "backend\autoplaza" -Force | Out-Null
    New-Item -ItemType Directory -Path "backend\autoplaza\settings" -Force | Out-Null

    # Создаем __init__.py
    "" | Out-File -FilePath "backend\autoplaza\__init__.py" -Encoding UTF8
    "" | Out-File -FilePath "backend\autoplaza\settings\__init__.py" -Encoding UTF8

    Write-Host "   Создана директория проекта" -ForegroundColor Green
}

# Создаем минимальный settings.py если его нет
if (-not (Test-Path "backend\autoplaza\settings.py")) {
    $settingsContent = @'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = 'django-insecure-temp-key-change-in-production'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'backend.apps.core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.autoplaza.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.autoplaza.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
'@

    $settingsContent | Out-File -FilePath "backend\autoplaza\settings.py" -Encoding UTF8
    Write-Host "   Создан settings.py" -ForegroundColor Green
}

# Создаем urls.py
if (-not (Test-Path "backend\autoplaza\urls.py")) {
    $urlsContent = @'
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
'@

    $urlsContent | Out-File -FilePath "backend\autoplaza\urls.py" -Encoding UTF8
    Write-Host "   Создан urls.py" -ForegroundColor Green
}

# Создаем wsgi.py и asgi.py
if (-not (Test-Path "backend\autoplaza\wsgi.py")) {
    $wsgiContent = @'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.autoplaza.settings')

application = get_wsgi_application()
'@

    $wsgiContent | Out-File -FilePath "backend\autoplaza\wsgi.py" -Encoding UTF8
    Write-Host "   Создан wsgi.py" -ForegroundColor Green
}

if (-not (Test-Path "backend\autoplaza\asgi.py")) {
    $asgiContent = @'
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.autoplaza.settings')

application = get_asgi_application()
'@

    $asgiContent | Out-File -FilePath "backend\autoplaza\asgi.py" -Encoding UTF8
    Write-Host "   Создан asgi.py" -ForegroundColor Green
}

# Обновляем manage.py
Write-Host "6. Обновление manage.py..." -ForegroundColor Cyan
if (Test-Path "manage.py") {
    $manageContent = Get-Content "manage.py" -Raw
    # Заменяем настройки по умолчанию
    $newContent = $manageContent -replace "os\.environ\.setdefault\('DJANGO_SETTINGS_MODULE', '.*?'\)", "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.autoplaza.settings')"
    $newContent | Out-File -FilePath "manage.py" -Encoding UTF8
    Write-Host "   manage.py обновлен" -ForegroundColor Green
}

Write-Host "`n=== МИГРАЦИЯ ЗАВЕРШЕНА ===" -ForegroundColor Green
Write-Host "`nСледующие шаги:" -ForegroundColor Yellow
Write-Host "1. Обновите ваш основной settings.py файл:" -ForegroundColor White
Write-Host "   Измените BASE_DIR: Path(__file__).resolve().parent.parent -> Path(__file__).resolve().parent.parent.parent" -ForegroundColor Gray
Write-Host "   Измените INSTALLED_APPS: 'autoplaza' -> 'backend.apps.core'" -ForegroundColor Gray
Write-Host "`n2. Обновите импорты в коде:" -ForegroundColor White
Write-Host "   from autoplaza.models import ... -> from backend.apps.core.models import ..." -ForegroundColor Gray
Write-Host "`n3. Запустите проверку:" -ForegroundColor White
Write-Host "   python manage.py check" -ForegroundColor Gray
Write-Host "`n4. Если все хорошо, запустите сервер:" -ForegroundColor White
Write-Host "   python manage.py runserver" -ForegroundColor Gray
Write-Host "`nРезервная копия сохранена в: autoplaza_backup_*" -ForegroundColor Cyan