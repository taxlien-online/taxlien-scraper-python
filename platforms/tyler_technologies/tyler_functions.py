"""
Tyler Technologies (iasWorld) scraper functions
Поддержка: Harris County TX, Wake County NC, Pima County AZ и др.
"""

import os
import re
from bs4 import BeautifulSoup
from sbvirtualdisplay import Display
from seleniumbase import SB

from celery_app import app
from functions import scraper_pass_modal, save_json, scraper_pass_challenge

os.environ['DISPLAY'] = ':99'


@app.task
def tyler_scrape_counties_urls_task(base_url: str) -> dict:
    """
    Получить список доступных округов на Tyler Technologies портале
    """
    counties_urls = {}

    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=False) as sb:
            sb.uc_open_with_reconnect(base_url, 2)
            
            # Tyler обычно использует dropdown или список ссылок
            county_links = sb.find_elements("a[href*='County']", by="css selector")
            
            for link in county_links:
                county_name = link.text
                county_url = link.get_attribute("href")
                if county_name and county_url:
                    counties_urls[county_name] = county_url
                    print(f"Found: {county_name} -> {county_url}")

    return counties_urls


@app.task
def tyler_get_parcel_search_url(county_url: str) -> str:
    """
    Найти URL для поиска parcels в Tyler iasWorld системе
    """
    with Display(visible=False, size=(1920, 1080)) as disp:
        with SB(uc=True, headless=False) as sb:
            sb.uc_open_with_reconnect(county_url, 2)
            
            # Tyler обычно имеет "Property Search" или "Parcel Search" ссылку
            search_selectors = [
                "a[href*='PropertySearch']",
                "a[href*='ParcelSearch']",
                "a:contains('Property Search')",
                "a:contains('Search')"
            ]
            
            for selector in search_selectors:
                try:
                    link = sb.find_element(selector, by="css selector")
                    if link:
                        return link.get_attribute("href")
                except:
                    continue
    
    return county_url


@app.task
def tyler_search_by_criteria(search_url: str, criteria: dict) -> list:
    """
    Поиск parcels по критериям (owner name, address, parcel number)
    
    Args:
        search_url: URL страницы поиска
        criteria: словарь с критериями поиска
            {
                'parcel_number': '123-456-789',
                'owner_name': 'Smith',
                'street_address': 'Main St'
            }
    
    Returns:
        list: список URLs найденных parcels
    """
    parcel_urls = []
    
    with Display(visible=False, size=(1920, 1080)) as disp:
        with SB(uc=True, headless=False) as sb:
            sb.uc_open_with_reconnect(search_url, 2)
            
            # Заполнить форму поиска
            if 'parcel_number' in criteria:
                try:
                    sb.type("input[name*='ParcelID']", criteria['parcel_number'])
                except:
                    pass
            
            if 'owner_name' in criteria:
                try:
                    sb.type("input[name*='Owner']", criteria['owner_name'])
                except:
                    pass
            
            if 'street_address' in criteria:
                try:
                    sb.type("input[name*='Street']", criteria['street_address'])
                except:
                    pass
            
            # Нажать кнопку поиска
            search_buttons = [
                "input[type='submit'][value*='Search']",
                "button:contains('Search')",
                "input[id*='btnSearch']"
            ]
            
            for btn_selector in search_buttons:
                try:
                    sb.click(btn_selector)
                    break
                except:
                    continue
            
            sb.sleep(2)
            
            # Получить результаты
            # Tyler часто показывает таблицу с результатами
            result_links = sb.find_elements("a[href*='ParcelID']", by="css selector")
            
            for link in result_links:
                url = link.get_attribute("href")
                if url and url not in parcel_urls:
                    parcel_urls.append(url)
    
    return parcel_urls


@app.task
def tyler_parse_single_html_task(html: str) -> dict:
    """
    Парсинг HTML страницы Tyler Technologies
    
    Типичная структура:
    - ASP.NET ViewState (игнорируем)
    - Таблицы с данными: Owner, Property, Tax, Sales
    - Иногда используют div с id/class patterns
    """
    doc = BeautifulSoup(html, "html.parser")
    
    data = {}
    
    try:
        # PARCEL INFO
        # Tyler использует разные ID patterns, пробуем несколько
        parcel_patterns = [
            "lblParcelID",
            "ParcelNumber",
            "PropertyID",
            "ctlBodyPane.*ParcelID"
        ]
        
        for pattern in parcel_patterns:
            parcel = doc.find(id=re.compile(pattern, re.IGNORECASE))
            if parcel:
                data['parcel_id'] = parcel.text.strip()
                break
        
        # OWNER INFO
        owner_patterns = [
            "lblOwner",
            "OwnerName",
            "ctlBodyPane.*Owner"
        ]
        
        for pattern in owner_patterns:
            owner = doc.find(id=re.compile(pattern, re.IGNORECASE))
            if owner:
                data['owner'] = owner.text.strip()
                break
        
        # SITE ADDRESS
        address_patterns = [
            "lblSiteAddress",
            "PropertyAddress",
            "SitusAddress"
        ]
        
        for pattern in address_patterns:
            address = doc.find(id=re.compile(pattern, re.IGNORECASE))
            if address:
                data['site_address'] = address.text.strip()
                break
        
        # MAILING ADDRESS
        mailing_patterns = [
            "lblMailingAddress",
            "MailingAddress"
        ]
        
        for pattern in mailing_patterns:
            mailing = doc.find(id=re.compile(pattern, re.IGNORECASE))
            if mailing:
                data['mailing_address'] = mailing.text.strip()
                break
        
        # PROPERTY TYPE
        type_patterns = [
            "lblPropertyType",
            "PropertyClass",
            "LandUse"
        ]
        
        for pattern in type_patterns:
            prop_type = doc.find(id=re.compile(pattern, re.IGNORECASE))
            if prop_type:
                data['property_type'] = prop_type.text.strip()
                break
        
        # ASSESSED VALUES
        # Tyler обычно показывает Land Value, Improvement Value, Total Value
        land_value = doc.find(id=re.compile("LandValue|AssessedLand", re.IGNORECASE))
        if land_value:
            data['land_value'] = land_value.text.strip()
        
        improvement_value = doc.find(id=re.compile("ImprovementValue|AssessedImprovement", re.IGNORECASE))
        if improvement_value:
            data['improvement_value'] = improvement_value.text.strip()
        
        total_value = doc.find(id=re.compile("TotalValue|AssessedTotal|MarketValue", re.IGNORECASE))
        if total_value:
            data['assessed_value'] = total_value.text.strip()
        
        # LEGAL DESCRIPTION
        legal = doc.find(id=re.compile("LegalDescription|Legal", re.IGNORECASE))
        if legal:
            data['legal_description'] = legal.text.strip()
        
        # BUILDING INFO
        sqft = doc.find(id=re.compile("SquareFeet|LivingArea|BuildingArea", re.IGNORECASE))
        if sqft:
            data['building_sqft'] = sqft.text.strip()
        
        year_built = doc.find(id=re.compile("YearBuilt|ConstructionYear", re.IGNORECASE))
        if year_built:
            data['year_built'] = year_built.text.strip()
        
        bedrooms = doc.find(id=re.compile("Bedrooms|BedCount", re.IGNORECASE))
        if bedrooms:
            data['bedrooms'] = bedrooms.text.strip()
        
        bathrooms = doc.find(id=re.compile("Bathrooms|BathCount", re.IGNORECASE))
        if bathrooms:
            data['bathrooms'] = bathrooms.text.strip()
        
        # LOT INFO
        lot_size = doc.find(id=re.compile("LotSize|Acreage|LotAcres", re.IGNORECASE))
        if lot_size:
            data['lot_size'] = lot_size.text.strip()
        
        # TAX INFO
        # Ищем таблицу с tax history
        tax_table = doc.find('table', id=re.compile("Tax|Assessment", re.IGNORECASE))
        if tax_table:
            # Обычно первая строка - текущий год
            rows = tax_table.find_all('tr')
            if len(rows) > 1:
                # Предполагаем формат: Year | Assessed Value | Tax Amount | Status
                cells = rows[1].find_all('td')
                if len(cells) >= 3:
                    data['tax_year'] = cells[0].text.strip()
                    data['tax_amount'] = cells[2].text.strip()
                    if len(cells) >= 4:
                        data['tax_status'] = cells[3].text.strip()
        
        # SALES HISTORY
        sales_table = doc.find('table', id=re.compile("Sales|Transfer", re.IGNORECASE))
        if sales_table:
            rows = sales_table.find_all('tr')
            if len(rows) > 1:
                # Последняя продажа
                cells = rows[1].find_all('td')
                if len(cells) >= 2:
                    data['last_sale_date'] = cells[0].text.strip()
                    data['last_sale_price'] = cells[1].text.strip()
        
        # DELINQUENCY INFO
        delinquent = doc.find(text=re.compile("delinquent|past due", re.IGNORECASE))
        if delinquent:
            data['has_delinquency'] = True
            # Попробовать найти сумму долга рядом
            parent = delinquent.parent
            if parent:
                amount = parent.find(text=re.compile(r'\$[\d,]+\.\d{2}'))
                if amount:
                    data['delinquent_amount'] = amount.strip()
        
        # EXEMPTIONS
        exemption = doc.find(id=re.compile("Exemption|Homestead", re.IGNORECASE))
        if exemption:
            data['exemptions'] = exemption.text.strip()
        
    except Exception as e:
        print(f"Error parsing Tyler HTML: {e}")
        data['parse_error'] = str(e)
    
    return data


@app.task
def tyler_scrape_all_parcels_by_letter(search_url: str, county: str) -> list:
    """
    Получить все parcels путем поиска по первой букве фамилии владельца (A-Z)
    Эффективный способ для Tyler систем
    """
    all_parcel_urls = []
    
    # Поиск по каждой букве алфавита
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        print(f"Searching for owners starting with '{letter}'")
        
        criteria = {'owner_name': f"{letter}*"}
        parcels = tyler_search_by_criteria.apply_async(
            args=[search_url, criteria]
        ).get()
        
        all_parcel_urls.extend(parcels)
        
        # Сохранить промежуточные результаты
        if len(all_parcel_urls) % 1000 == 0:
            save_json({'parcels': all_parcel_urls}, "tyler", f"{county}_progress")
    
    # Удалить дубликаты
    all_parcel_urls = list(set(all_parcel_urls))
    
    return all_parcel_urls


# Пример конфигурации для разных Tyler округов
TYLER_CONFIGS = {
    'harris_county_tx': {
        'base_url': 'https://hcad.org',
        'search_url': 'https://hcad.org/property-search/',
        'county': 'harris_tx',
        'state': 'TX',
        'type': 'iasWorld'
    },
    'wake_county_nc': {
        'base_url': 'https://wake.sdatappraisers.com',
        'search_url': 'https://wake.sdatappraisers.com/search.aspx',
        'county': 'wake_nc',
        'state': 'NC',
        'type': 'iasWorld'
    },
    'pima_county_az': {
        'base_url': 'https://asr.pima.gov',
        'search_url': 'https://asr.pima.gov/propertySearch',
        'county': 'pima_az',
        'state': 'AZ',
        'type': 'iasWorld'
    }
}

