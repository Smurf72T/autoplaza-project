import os
import re


def find_send_ad_message():
    project_dir = "G:/autoplaza-project"

    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Ищем send_ad_message с разными вариантами
                        if 'send_ad_message' in content or 'send_message' in content:
                            print(f"Найдено в: {file_path}")
                            # Показываем контекст
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if 'send_ad_message' in line or 'send_message' in line:
                                    print(f"  Строка {i + 1}: {line.strip()}")
                except:
                    continue


if __name__ == "__main__":
    find_send_ad_message()