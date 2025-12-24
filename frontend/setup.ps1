# setup.ps1
Write-Host "🚀 Настройка AutoPlaza Frontend..." -ForegroundColor Cyan

# Проверка Node.js
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js установлен: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js не установлен!" -ForegroundColor Red
    Write-Host "Установите Node.js с https://nodejs.org/" -ForegroundColor Yellow
    Write-Host "Затем перезапустите PowerShell и запустите скрипт снова" -ForegroundColor Yellow
    exit 1
}

# Проверка npm
try {
    $npmVersion = npm --version
    Write-Host "✅ npm установлен: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm не установлен!" -ForegroundColor Red
    exit 1
}

# Очистка проекта
Write-Host "🧹 Очистка проекта..." -ForegroundColor Yellow
$itemsToRemove = @(
    "node_modules",
    ".next",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml"
)

foreach ($item in $itemsToRemove) {
    if (Test-Path $item) {
        Write-Host "Удаляю $item..." -ForegroundColor Gray
        Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
    }
}

# Создание package.json
Write-Host "📝 Создание package.json..." -ForegroundColor Green
if (!(Test-Path "package.json")) {
    @'
{
  "name": "autoplaza-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
'@ | Out-File -FilePath "package.json" -Encoding UTF8
}

# Установка зависимостей
Write-Host "📦 Установка Next.js и React..." -ForegroundColor Green
npm install next@14.2.5 react@18.2.0 react-dom@18.2.0 --save-exact

Write-Host "📦 Установка TypeScript..." -ForegroundColor Green
npm install --save-dev typescript@5.3.3 @types/node@20.11.24 @types/react@18.2.61 @types/react-dom@18.2.19

Write-Host "🎨 Установка Tailwind CSS..." -ForegroundColor Green
npm install --save-dev tailwindcss@3.4.0 postcss@8.4.38 autoprefixer@10.4.19

# Инициализация конфигураций
Write-Host "⚙️ Инициализация конфигураций..." -ForegroundColor Green
npx tailwindcss init -p
npx tsc --init

Write-Host "✅ Настройка завершена!" -ForegroundColor Green
Write-Host "`nКоманды для запуска:" -ForegroundColor Cyan
Write-Host "1. npm run dev    - Запуск сервера разработки" -ForegroundColor Yellow
Write-Host "2. Откройте браузер: http://localhost:3000" -ForegroundColor Yellow