$ErrorActionPreference = "Stop"

Write-Host "Создание структуры проекта Autoplaza..." -ForegroundColor Green

# Массив директорий для создания
$directories = @(
    # Backend apps
    "backend\apps\core",
    "backend\apps\users",
    "backend\apps\advertisements",
    "backend\apps\catalog",
    "backend\apps\chat",
    "backend\apps\reviews",
    "backend\apps\analytics",
    "backend\apps\payments",

    # Backend static/media
    "backend\static\css",
    "backend\static\js",
    "backend\static\images",
    "backend\media\avatars",
    "backend\media\photos",
    "backend\media\documents",
    "backend\templates",

    # Frontend
    "frontend\public",
    "frontend\src\app\api",
    "frontend\src\components\ui",
    "frontend\src\components\layout",
    "frontend\src\components\forms",
    "frontend\src\lib",
    "frontend\src\hooks",
    "frontend\src\types",

    # Support
    "scripts\dev",
    "docs",
    "tests\unit",
    "tests\integration",
    "tests\e2e",
    "logs"
)

# Создаем директории
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Create: $dir" -ForegroundColor Yellow
    } else {
        Write-Host "  Already exists: $dir" -ForegroundColor Gray
    }
}

Write-Host "`nStructure created successfully!" -ForegroundColor Green