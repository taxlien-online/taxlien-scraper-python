#!/usr/bin/env python3
"""
Тест существующего QPublic scraper - он уже работает!
Результаты сохраняются в /Users/anton/taxlien.dataset/qpublic/
"""

import os
import json
from datetime import datetime
from seleniumbase import SB
from bs4 import BeautifulSoup
import re

# Настройка путей
DATASET_DIR = "/Users/anton/taxlien.dataset/qpublic"
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

def parse_qpublic_html(html: str) -> dict:
    """Парсинг HTML страницы QPublic (из существующего кода)"""
    doc = BeautifulSoup(html, "html.parser")
    
    data = {
        'scraped_at': datetime.now().isoformat(),
        'platform': 'qpublic',
        'county': 'test'
    }
    
    try:
        # Используем существующую логику из qpublic_functions.py
        info_table = doc.find(class_=re.compile("tabular-data-two-column"))
        
        if info_table:
            # PARCEL ID
            parcel = info_table.find(id=re.compile("_lblParcelID"))
            if parcel:
                data['parcel_id'] = parcel.text.strip()
            
            # OWNER
            owner = doc.find(id=re.compile("ctlBodyPane_ctl01_ctl00_lblName"))
            if owner:
                data['owner'] = owner.text.strip()
            
            # SITE ADDRESS
            site_address = doc.find(id=re.compile("InfoPane2_lnkWebsite"))
            if site_address and 'href' in site_address.attrs:
                data['site_address'] = site_address.attrs["href"]
            
            # LEGAL DESCRIPTION
            legal = info_table.find(id=re.compile("_lblLegalDescription"))
            if legal:
                data['legal_description'] = legal.text.strip()
            
            # PROPERTY TAX ACCOUNT
            tax_account = info_table.find(id=re.compile("_lblPropertyID"))
            if tax_account:
                data['property_tax_account'] = tax_account.text.strip()
        
        # TAX INFORMATION
        tax_table = doc.find(id=re.compile("_grdValuation"))
        if tax_table:
            total_values_rows = tax_table.find_all(class_=re.compile("double-total-line"))
            if len(total_values_rows) >= 3:
                total_due = total_values_rows[2].find_all(class_=re.compile("value-column"))
                if total_due:
                    data['total_due_amount'] = total_due[0].text.strip()
                
                last_year = total_values_rows[1].find_all(class_=re.compile("value-column"))
                if last_year:
                    data['last_year_due_amount'] = last_year[0].text.strip()
        
        print(f"✅ Parsed: {data.get('parcel_id', 'N/A')}")
        
    except Exception as e:
        print(f"⚠️  Parse error: {e}")
        data['parse_error'] = str(e)
    
    return data

def test_qpublic():
    """
    Тест QPublic - пример парсинга одной страницы
    """
    print("\n" + "="*60)
    print("ТЕСТ: QPublic scraper (работающий)")
    print("="*60 + "\n")
    
    # Используем URL из существующей конфигурации
    test_url = "https://qpublic.schneidercorp.com/Application.aspx?AppID=867&LayerID=16385&PageTypeID=4&PageID=7232&Q=1299906831&KeyValue=34-09-13-4496-0000-0040"
    
    print(f"🌐 URL: {test_url}")
    print(f"📁 Сохранение в: {DATASET_DIR}")
    print(f"⏳ Запуск браузера...")
    
    try:
        with SB(headless=True) as sb:
            print("⏳ Загрузка страницы...")
            sb.open(test_url)
            sb.sleep(5)  # Ждем загрузки
            
            # Пропустить modal если есть
            try:
                agree_button = sb.find_element('[class*="btn btn-primary button-1"]', by="css selector", timeout=3)
                if agree_button:
                    agree_button.click()
                    print("✅ Кликнули Agree")
                    sb.sleep(2)
            except:
                print("ℹ️  Нет modal окна")
            
            # Сохранить скриншот
            screenshot_path = f"{DATASET_DIR}/html/qpublic_test.png"
            sb.save_screenshot(screenshot_path)
            print(f"📸 Скриншот: {screenshot_path}")
            
            # Получить HTML
            html = sb.get_page_source()
            print(f"📄 HTML размер: {len(html)} bytes")
            
            # Сохранить HTML
            save_html(html, "qpublic_test_page")
            
            # Парсинг
            data = parse_qpublic_html(html)
            
            # Сохранить JSON
            save_json(data, "qpublic_test_result")
            
            # Сохранить CSV
            save_csv_line(data, "results")
            
            print("\n✅ ТЕСТ ЗАВЕРШЕН!")
            print(f"\n📊 Собранные данные:")
            for key, value in data.items():
                print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция"""
    print("\n" + "="*70)
    print(" 🚀 QPUBLIC SCRAPER TEST - Dixie County, FL")
    print("="*70)
    print(f"\n📁 Dataset directory: {DATASET_DIR}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        test_qpublic()
        
        print("\n" + "="*70)
        print(" ✅ ТЕСТ ЗАВЕРШЕН!")
        print("="*70)
        print(f"\n📊 Результаты сохранены в: {DATASET_DIR}")
        print(f"   - HTML: {DATASET_DIR}/html/")
        print(f"   - JSON: {DATASET_DIR}/json/")
        print(f"   - CSV:  {DATASET_DIR}/csv/")
        
        # Показать статистику
        import glob
        html_files = glob.glob(f"{DATASET_DIR}/html/*.html")
        json_files = glob.glob(f"{DATASET_DIR}/json/*.json")
        csv_files = glob.glob(f"{DATASET_DIR}/csv/*.csv")
        
        print(f"\n📈 Статистика:")
        print(f"   - HTML файлов: {len(html_files)}")
        print(f"   - JSON файлов: {len(json_files)}")
        print(f"   - CSV файлов: {len(csv_files)}")
        
        # Показать содержимое файлов
        if json_files:
            print(f"\n📄 Пример JSON ({json_files[0]}):")
            with open(json_files[0], 'r') as f:
                content = json.load(f)
                print(json.dumps(content, indent=2, ensure_ascii=False))
        
    except KeyboardInterrupt:
        print("\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

