"""
Bid4Assets scraper functions
Аукционная платформа для tax liens и tax deeds
URL: https://www.bid4assets.com
"""

import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
from sbvirtualdisplay import Display
from seleniumbase import SB

from celery_app import app
from functions import save_json

os.environ['DISPLAY'] = ':99'


@app.task
def bid4assets_get_auction_calendar(base_url: str = "https://www.bid4assets.com") -> dict:
    """
    Получить календарь предстоящих аукционов
    
    Returns:
        dict: {
            'state': {
                'county': {
                    'auction_date': '2025-10-20',
                    'auction_type': 'tax_lien',
                    'auction_url': 'https://...',
                    'properties_count': 150
                }
            }
        }
    """
    auction_calendar = {}

    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=False) as sb:
            # Открыть страницу с календарем
            calendar_url = f"{base_url}/SalesCalendar"
            sb.uc_open_with_reconnect(calendar_url, 2)
            sb.sleep(2)

            # Bid4Assets использует календарную структуру
            # Получить HTML
            html = sb.get_page_source()
            doc = BeautifulSoup(html, "html.parser")

            # Найти все предстоящие аукционы
            auction_items = doc.find_all(class_=re.compile("auction-item|sale-item", re.IGNORECASE))

            for item in auction_items:
                try:
                    # Извлечь информацию об аукционе
                    state = item.find(class_=re.compile("state"))
                    county = item.find(class_=re.compile("county|jurisdiction"))
                    date = item.find(class_=re.compile("date|sale-date"))
                    auction_type = item.find(class_=re.compile("type|sale-type"))
                    link = item.find('a', href=True)
                    count = item.find(class_=re.compile("count|properties"))

                    if state and county and date:
                        state_name = state.text.strip()
                        county_name = county.text.strip()
                        
                        if state_name not in auction_calendar:
                            auction_calendar[state_name] = {}
                        
                        auction_calendar[state_name][county_name] = {
                            'auction_date': date.text.strip(),
                            'auction_type': auction_type.text.strip() if auction_type else 'unknown',
                            'auction_url': link['href'] if link else '',
                            'properties_count': int(count.text.strip()) if count else 0
                        }
                        
                        print(f"Found: {state_name} - {county_name} on {date.text.strip()}")

                except Exception as e:
                    print(f"Error parsing auction item: {e}")
                    continue

    return auction_calendar


@app.task
def bid4assets_get_auction_properties(auction_url: str) -> list:
    """
    Получить список properties для конкретного аукциона
    
    Args:
        auction_url: URL страницы аукциона
    
    Returns:
        list: список URLs отдельных properties
    """
    property_urls = []

    with Display(visible=False, size=(1920, 1080)) as disp:
        with SB(uc=True, headless=False) as sb:
            sb.uc_open_with_reconnect(auction_url, 2)
            sb.sleep(2)

            # Bid4Assets может использовать пагинацию
            page = 1
            max_pages = 100  # Защита от бесконечного цикла

            while page <= max_pages:
                print(f"Processing page {page}")
                
                # Получить ссылки на properties
                property_links = sb.find_elements("a[href*='/Item/']", by="css selector")
                
                for link in property_links:
                    url = link.get_attribute("href")
                    if url and url not in property_urls:
                        property_urls.append(url)
                
                # Проверить наличие кнопки "Next"
                try:
                    next_button = sb.find_element("a[aria-label='Next']", by="css selector")
                    if next_button:
                        next_button.click()
                        sb.sleep(2)
                        page += 1
                    else:
                        break
                except:
                    break  # Больше нет страниц

    return property_urls


@app.task
def bid4assets_parse_single_property(html: str) -> dict:
    """
    Парсинг страницы отдельного property на Bid4Assets
    
    Bid4Assets показывает:
    - Property details
    - Current bid
    - Opening bid
    - Number of bidders
    - Auction end time
    - Tax information
    - Property images
    """
    doc = BeautifulSoup(html, "html.parser")
    
    data = {}
    
    try:
        # BASIC INFO
        title = doc.find('h1', class_=re.compile("title|property-name"))
        if title:
            data['property_title'] = title.text.strip()
        
        # ADDRESS
        address = doc.find(class_=re.compile("address|location"))
        if address:
            data['property_address'] = address.text.strip()
        
        # PARCEL ID
        parcel = doc.find(text=re.compile("Parcel|Tax ID", re.IGNORECASE))
        if parcel:
            parent = parcel.parent
            if parent:
                data['parcel_id'] = parent.text.replace(parcel, '').strip()
        
        # BIDDING INFO
        current_bid = doc.find(class_=re.compile("current-bid|high-bid"))
        if current_bid:
            data['current_bid'] = current_bid.text.strip()
        
        opening_bid = doc.find(class_=re.compile("opening-bid|starting-bid"))
        if opening_bid:
            data['opening_bid'] = opening_bid.text.strip()
        
        num_bids = doc.find(class_=re.compile("bid-count|number-of-bids"))
        if num_bids:
            data['number_of_bids'] = num_bids.text.strip()
        
        # AUCTION TIMING
        end_time = doc.find(class_=re.compile("end-time|closes"))
        if end_time:
            data['auction_end_time'] = end_time.text.strip()
        
        # PROPERTY TYPE
        prop_type = doc.find(text=re.compile("Property Type", re.IGNORECASE))
        if prop_type:
            parent = prop_type.parent
            if parent:
                data['property_type'] = parent.text.replace(prop_type, '').strip()
        
        # TAX INFORMATION
        # Bid4Assets обычно показывает налоговую информацию в таблице
        tax_section = doc.find('div', id=re.compile("tax|assessment", re.IGNORECASE))
        if tax_section:
            # Tax Amount
            tax_amount = tax_section.find(text=re.compile("Tax Amount|Taxes Due", re.IGNORECASE))
            if tax_amount:
                parent = tax_amount.parent
                if parent:
                    amount_text = parent.text.replace(tax_amount, '').strip()
                    data['tax_amount_due'] = amount_text
            
            # Tax Year
            tax_year = tax_section.find(text=re.compile("Tax Year", re.IGNORECASE))
            if tax_year:
                parent = tax_year.parent
                if parent:
                    year_text = parent.text.replace(tax_year, '').strip()
                    data['tax_year'] = year_text
        
        # ASSESSED VALUE
        assessed = doc.find(text=re.compile("Assessed Value", re.IGNORECASE))
        if assessed:
            parent = assessed.parent
            if parent:
                data['assessed_value'] = parent.text.replace(assessed, '').strip()
        
        # PROPERTY DETAILS
        details_table = doc.find('table', class_=re.compile("details|specifications"))
        if details_table:
            rows = details_table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    
                    if 'bedrooms' in label:
                        data['bedrooms'] = value
                    elif 'bathrooms' in label:
                        data['bathrooms'] = value
                    elif 'square feet' in label or 'sqft' in label:
                        data['building_sqft'] = value
                    elif 'lot size' in label or 'acres' in label:
                        data['lot_size'] = value
                    elif 'year built' in label:
                        data['year_built'] = value
                    elif 'zoning' in label:
                        data['zoning'] = value
        
        # LEGAL DESCRIPTION
        legal = doc.find(text=re.compile("Legal Description", re.IGNORECASE))
        if legal:
            # Обычно идет в следующем элементе
            parent = legal.parent
            if parent:
                next_elem = parent.find_next_sibling()
                if next_elem:
                    data['legal_description'] = next_elem.text.strip()
        
        # OWNER INFORMATION (если доступно)
        owner = doc.find(text=re.compile("Owner|Current Owner", re.IGNORECASE))
        if owner:
            parent = owner.parent
            if parent:
                data['owner'] = parent.text.replace(owner, '').strip()
        
        # REDEMPTION PERIOD
        redemption = doc.find(text=re.compile("Redemption Period", re.IGNORECASE))
        if redemption:
            parent = redemption.parent
            if parent:
                data['redemption_period'] = parent.text.replace(redemption, '').strip()
        
        # AUCTION TYPE
        auction_type = doc.find(text=re.compile("Sale Type|Auction Type", re.IGNORECASE))
        if auction_type:
            parent = auction_type.parent
            if parent:
                type_text = parent.text.replace(auction_type, '').strip()
                data['auction_type'] = type_text  # tax_lien, tax_deed, foreclosure
        
        # IMAGES
        image_gallery = doc.find('div', class_=re.compile("gallery|images"))
        if image_gallery:
            images = image_gallery.find_all('img', src=True)
            data['image_urls'] = [img['src'] for img in images]
        
        # DOCUMENTS
        documents = doc.find_all('a', href=re.compile(r'\.(pdf|doc|docx)$', re.IGNORECASE))
        if documents:
            data['document_urls'] = [doc['href'] for doc in documents]
        
        # SELLER/JURISDICTION
        seller = doc.find(text=re.compile("Seller|Jurisdiction", re.IGNORECASE))
        if seller:
            parent = seller.parent
            if parent:
                data['jurisdiction'] = parent.text.replace(seller, '').strip()
        
        # ADDITIONAL NOTES
        notes = doc.find('div', class_=re.compile("notes|comments|description"))
        if notes:
            data['notes'] = notes.text.strip()
        
        # METADATA
        data['scraped_at'] = datetime.now().isoformat()
        data['source'] = 'bid4assets'

    except Exception as e:
        print(f"Error parsing Bid4Assets property: {e}")
        data['parse_error'] = str(e)

    return data


@app.task
def bid4assets_scrape_full_auction(auction_url: str, county: str) -> dict:
    """
    Полный скрапинг аукциона: получить все properties и их детали
    
    Args:
        auction_url: URL страницы аукциона
        county: название округа для сохранения
    
    Returns:
        dict: сводная информация
    """
    print(f"Starting full auction scrape: {auction_url}")
    
    # 1. Получить список всех properties
    property_urls = bid4assets_get_auction_properties.apply_async(
        args=[auction_url]
    ).get()
    
    print(f"Found {len(property_urls)} properties")
    
    # 2. Сохранить список URLs
    save_json({'property_urls': property_urls}, "bid4assets", f"{county}_urls")
    
    # 3. Скрапить каждый property (можно распараллелить)
    all_properties = []
    
    for idx, prop_url in enumerate(property_urls):
        print(f"Scraping property {idx+1}/{len(property_urls)}: {prop_url}")
        
        with Display(visible=False, size=(1920, 1080)) as disp:
            with SB(uc=True, headless=False) as sb:
                sb.uc_open_with_reconnect(prop_url, 2)
                sb.sleep(1)
                html = sb.get_page_source()
                
                property_data = bid4assets_parse_single_property(html)
                property_data['property_url'] = prop_url
                all_properties.append(property_data)
        
        # Сохранять промежуточные результаты каждые 50 properties
        if (idx + 1) % 50 == 0:
            save_json({'properties': all_properties}, "bid4assets", f"{county}_partial_{idx+1}")
    
    # 4. Сохранить все данные
    save_json({'properties': all_properties}, "bid4assets", f"{county}_complete")
    
    return {
        'total_properties': len(all_properties),
        'auction_url': auction_url,
        'county': county
    }


# Пример использования
EXAMPLE_USAGE = """
# 1. Получить календарь аукционов
from tasks import bid4assets_get_auction_calendar
calendar = bid4assets_get_auction_calendar.apply_async().get()

# 2. Выбрать интересующий аукцион
auction_url = calendar['Florida']['Miami-Dade']['auction_url']

# 3. Скрапить весь аукцион
from tasks import bid4assets_scrape_full_auction
result = bid4assets_scrape_full_auction.apply_async(
    args=[auction_url, 'miami_dade_fl']
).get()
"""

