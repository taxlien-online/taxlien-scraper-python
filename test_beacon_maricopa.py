#!/usr/bin/env python3
"""
Тестовый запуск Beacon scraper для Maricopa County, AZ
Результаты сохраняются в /Users/anton/taxlien.dataset/beacon/
"""

import os
import json
from datetime import datetime
from sbvirtualdisplay import Display
from seleniumbase import SB
from bs4 import BeautifulSoup

# Настройка путей
DATASET_DIR = "/Users/anton/taxlien.dataset/beacon"
os.makedirs(f"{DATASET_DIR}/html", exist_ok=True)
os.makedirs(f"{DATASET_DIR}/json", exist_ok=True)
os.makedirs(f"{DATASET_DIR}/csv", exist_ok=True)

os.environ['DISPLAY'] = ':99'

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
    
    # Проверить, существует ли файл
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())
        
        # Записать заголовки, если файл новый
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(data)
    
    print(f'✅ CSV добавлена строка: {file_path}')

def parse_beacon_html(html: str) -> dict:
    """Парсинг HTML страницы Beacon"""
    import re
    doc = BeautifulSoup(html, "html.parser")
    
    data = {
        'scraped_at': datetime.now().isoformat(),
        'platform': 'beacon',
        'county': 'maricopa_az'
    }
    
    try:
        # Попробовать найти основную информацию
        # Beacon часто использует таблицы с классом tabular-data
        info_table = doc.find(class_=re.compile("tabular-data|property-info", re.IGNORECASE))
        
        if info_table:
            # PARCEL ID
            parcel = info_table.find(id=re.compile("parcel|PropertyID", re.IGNORECASE))
            if parcel:
                data['parcel_id'] = parcel.text.strip()
            
            # OWNER
            owner = doc.find(id=re.compile("owner|name", re.IGNORECASE))
            if owner:
                data['owner'] = owner.text.strip()
            
            # ADDRESS
            address = doc.find(id=re.compile("address|situs", re.IGNORECASE))
            if address:
                data['site_address'] = address.text.strip()
            
            # VALUE
            value = doc.find(id=re.compile("value|assessed", re.IGNORECASE))
            if value:
                data['assessed_value'] = value.text.strip()
        
        # Если не нашли через таблицу, попробовать через текст
        if 'parcel_id' not in data:
            # Поиск по паттернам
            text = doc.get_text()
            
            # Maricopa обычно использует формат: 123-45-678
            parcel_match = re.search(r'\b\d{3}-\d{2}-\d{3,4}\b', text)
            if parcel_match:
                data['parcel_id'] = parcel_match.group()
        
        print(f"✅ Parsed: {data.get('parcel_id', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        data['parse_error'] = str(e)
    
    return data

def test_single_url():
    """
    Тест 1: Скрапинг одной страницы
    """
    print("\n" + "="*60)
    print("ТЕСТ 1: Скрапинг одной страницы Beacon")
    print("="*60 + "\n")
    
    # URL для тестирования (нужно найти реальный)
    # Пример URL для Maricopa County
    test_url = "https://mcassessor.maricopa.gov/"
    
    print(f"🌐 URL: {test_url}")
    print(f"📁 Сохранение в: {DATASET_DIR}")
    print(f"⏳ Запуск браузера...")
    
    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'✅ Virtual Display: {disp.is_alive()}')
        
        with SB(uc=True, headless=False) as sb:
            print("⏳ Загрузка страницы...")
            sb.uc_open_with_reconnect(test_url, 2)
            sb.sleep(3)
            
            # Сохранить скриншот
            screenshot_path = f"{DATASET_DIR}/html/test_screenshot.png"
            sb.save_screenshot(screenshot_path)
            print(f"📸 Скриншот: {screenshot_path}")
            
            # Получить HTML
            html = sb.get_page_source()
            print(f"📄 HTML размер: {len(html)} bytes")
            
            # Сохранить HTML
            save_html(html, "test_page")
            
            # Парсинг
            data = parse_beacon_html(html)
            
            # Сохранить JSON
            save_json(data, "test_result")
            
            # Сохранить CSV
            save_csv_line(data, "test_results")
            
            print("\n✅ ТЕСТ 1 ЗАВЕРШЕН!")
            print(f"📊 Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")

def test_search_functionality():
    """
    Тест 2: Проверка функции поиска
    """
    print("\n" + "="*60)
    print("ТЕСТ 2: Проверка поиска Beacon")
    print("="*60 + "\n")
    
    base_url = "https://mcassessor.maricopa.gov/"
    
    with Display(visible=False, size=(1920, 1080)) as disp:
        with SB(uc=True, headless=False) as sb:
            print("⏳ Открытие главной страницы...")
            sb.uc_open_with_reconnect(base_url, 2)
            sb.sleep(2)
            
            # Попробовать найти поле поиска
            search_selectors = [
                "input[type='text'][name*='search']",
                "input[type='text'][name*='parcel']",
                "input[id*='search']",
                "input[placeholder*='Search']"
            ]
            
            found_search = False
            for selector in search_selectors:
                try:
                    search_input = sb.find_element(selector, by="css selector")
                    if search_input:
                        print(f"✅ Найдено поле поиска: {selector}")
                        found_search = True
                        
                        # Попробовать ввести тестовый parcel
                        test_parcel = "100-00-001"
                        sb.type(selector, test_parcel)
                        print(f"✅ Введен parcel: {test_parcel}")
                        
                        # Найти кнопку поиска
                        search_button_selectors = [
                            "button[type='submit']",
                            "input[type='submit']",
                            "button:contains('Search')"
                        ]
                        
                        for btn_selector in search_button_selectors:
                            try:
                                sb.click(btn_selector)
                                print(f"✅ Нажата кнопка поиска")
                                sb.sleep(3)
                                break
                            except:
                                continue
                        
                        break
                except:
                    continue
            
            if not found_search:
                print("⚠️  Поле поиска не найдено")
                print("💡 Сохраняем скриншот для анализа...")
                sb.save_screenshot(f"{DATASET_DIR}/html/search_not_found.png")
            
            # Сохранить текущую страницу
            html = sb.get_page_source()
            save_html(html, "search_result")
            
            print("\n✅ ТЕСТ 2 ЗАВЕРШЕН!")

def test_navigation():
    """
    Тест 3: Проверка навигации (кнопки Next/Prev)
    """
    print("\n" + "="*60)
    print("ТЕСТ 3: Проверка навигации")
    print("="*60 + "\n")
    
    # Этот тест требует URL конкретного parcel
    print("⚠️  Требуется URL конкретного parcel для теста")
    print("💡 Пропускаем пока...")

def main():
    """Главная функция"""
    print("\n" + "="*70)
    print(" 🚀 BEACON SCRAPER TEST - Maricopa County, AZ")
    print("="*70)
    print(f"\n📁 Dataset directory: {DATASET_DIR}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Запуск тестов
        test_single_url()
        test_search_functionality()
        # test_navigation()  # Пока закомментировано
        
        print("\n" + "="*70)
        print(" ✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ!")
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
        
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

