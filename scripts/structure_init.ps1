# Создаем __init__.py файлы
"", "backend\apps\__init__.py", "backend\apps\core\__init__.py", "backend\apps\users\__init__.py", "backend\apps\advertisements\__init__.py", "backend\apps\catalog\__init__.py", "backend\apps\chat\__init__.py", "backend\apps\reviews\__init__.py", "backend\apps\analytics\__init__.py", "backend\apps\payments\__init__.py" | ForEach-Object {
    if ($_ -ne "") {
        New-Item -ItemType File -Path $_ -Force
    }
}