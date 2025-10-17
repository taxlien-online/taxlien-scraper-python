#!/usr/bin/env python3
"""
Простой тест Beacon scraper для Mac OS (без Xvfb)
Результаты сохраняются в /Users/anton/taxlien.dataset/beacon/
"""

import os
import json
from datetime import datetime
from seleniumbase import SB
from bs4 import BeautifulSoup
import re

# Настройка путей
DATASET_DIR = "/Users/anton/taxlien.dataset/beacon"
os.makedirs(f"{DATASET_DIR}/html", exist_ok=True)
os.makedirs(f"{DATASET_DIR}/json", exist_ok=True)
os.makedirs(f"{DATASET_DIR}/csv", exist_ok=True)

def save_html(html: str, name: str) -> str:
    """Сохранить HTML"""
    file_path = f'{DATASET_DIR}/html/{name}.html'
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(html)
    print(f'✅ HTML сохранен: {file_path}')
    return file_path

def save_json(data: dict, name: str) -> str:
    """Сохранить JSON"""
    file_path = f'{DATASET_DIR}/json/{name}.json'
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    print(f'✅ JSON сохранен: {file_path}')
    return file_path

def save_csv_line(data: dict, name: str = "results") -> None:
    """Добавить строку в CSV"""
    import csv
    file_path = f'{DATASET_DIR}/csv/{name}.csv'
    
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)
    
    print(f'✅ CSV добавлена строка: {file_path}')

def parse_beacon_html(html: str) -> dict:
    """Парсинг HTML страницы Beacon"""
    doc = BeautifulSoup(html, "html.parser")
    
    data = {
        'scraped_at': datetime.now().isoformat(),
        'platform': 'beacon',
        'county': 'maricopa_az'
    }
    
    try:
        # Поиск основной информации
        text = doc.get_text()
        
        # Найти заголовок h1
        h1 = doc.find('h1')
        if h1:
            data['page_title'] = h1.text.strip()
        
        # Найти все ссылки
        links = doc.find_all('a', href=True)
        data['links_count'] = len(links)
        
        # Найти search form
        forms = doc.find_all('form')
        data['forms_count'] = len(forms)
        
        print(f"✅ Parsed: {data.get('page_title', 'N/A')}, {len(links)} links, {len(forms)} forms")
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        data['parse_error'] = str(e)
    
    return data

def test_simple():
    """
    Простой тест: открыть сайт и сохранить HTML
    """
    print("\n" + "="*60)
    print("ПРОСТОЙ ТЕСТ: Открытие сайта Maricopa")
    print("="*60 + "\n")
    
    test_url = "https://mcassessor.maricopa.gov/"
    
    print(f"🌐 URL: {test_url}")
    print(f"📁 Сохранение в: {DATASET_DIR}")
    print(f"⏳ Запуск браузера (headless)...")
    
    try:
        with SB(uc=True, headless=True) as sb:
            print("⏳ Загрузка страницы...")
            sb.open(test_url)
            sb.sleep(3)
            
            # Сохранить скриншот
            screenshot_path = f"{DATASET_DIR}/html/test_screenshot.png"
            sb.save_screenshot(screenshot_path)
            print(f"📸 Скриншот: {screenshot_path}")
            
            # Получить HTML
            html = sb.get_page_source()
            print(f"📄 HTML размер: {len(html)} bytes")
            
            # Сохранить HTML
            save_html(html, "maricopa_homepage")
            
            # Парсинг
            data = parse_beacon_html(html)
            
            # Сохранить JSON
            save_json(data, "maricopa_result")
            
            # Сохранить CSV
            save_csv_line(data, "results")
            
            print("\n✅ ТЕСТ ЗАВЕРШЕН!")
            print(f"📊 Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция"""
    print("\n" + "="*70)
    print(" 🚀 BEACON SCRAPER TEST - Maricopa County, AZ (Simple)")
    print("="*70)
    print(f"\n📁 Dataset directory: {DATASET_DIR}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        test_simple()
        
        print("\n" + "="*70)
        print(" ✅ ТЕСТ ЗАВЕРШЕН!")
        print("="*70)
        print(f"\n📊 Результаты сохранены в: {DATASET_DIR}")
        print(f"   - HTML: {DATASET_DIR}/html/")
        print(f"   - JSON: {DATASET_DIR}/json/")
        print(f"   - CSV:  {DATASET_DIR}/csv/")
        
        # Показать статистику
        import glob
        html_files = len(glob.glob(f"{DATASET_DIR}/html/*.html"))
        json_files = len(glob.glob(f"{DATASET_DIR}/json/*.json"))
        csv_files = len(glob.glob(f"{DATASET_DIR}/csv/*.csv"))
        
        print(f"\n📈 Статистика:")
        print(f"   - HTML файлов: {html_files}")
        print(f"   - JSON файлов: {json_files}")
        print(f"   - CSV файлов: {csv_files}")
        
        # Показать содержимое директории
        print(f"\n📂 Содержимое {DATASET_DIR}/:")
        for root, dirs, files in os.walk(DATASET_DIR):
            level = root.replace(DATASET_DIR, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                file_size = os.path.getsize(os.path.join(root, file))
                print(f'{subindent}{file} ({file_size} bytes)')
        
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

