"""
Beacon by Schneider Corp scraper functions
Расширение QPublic для дополнительных округов
Поддержка: Maricopa County AZ, King County WA, Hillsborough County FL и др.
"""

import os
import re
from bs4 import BeautifulSoup
from sbvirtualdisplay import Display
from seleniumbase import SB

from celery_app import app
from functions import scraper_pass_modal, save_json, scraper_pass_challenge, make_sites_visited_history

os.environ['DISPLAY'] = ':99'


@app.task
def beacon_scrape_counties_urls_task(base_url: str) -> dict:
    """
    Beacon имеет похожую структуру на QPublic
    """
    counties_urls = {}

    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=False) as sb:
            make_sites_visited_history(sb)
            sb.uc_open_with_reconnect(base_url, 2)
            scraper_pass_challenge(sb)
            scraper_pass_modal(sb)

            # Beacon использует похожий dropdown
            try:
                area_menu_input = sb.find_element("areaMenuButton", by="id")
                state_groups = sb.find_elements("state-group", by="class name")

                for state_group in state_groups:
                    if state_group.get_attribute('aria-labelledby') == "mru-group":
                        continue

                    counties = state_group.find_elements(value="dropdown-option", by="class name")

                    for county in counties:
                        if county.get_attribute("id") == "mru-group":
                            continue

                        area_menu_input.click()
                        county.click()
                        county_name = sb.get_text("areaMenuButton", by="id")
                        county_url = sb.find_element("track-mru", by="class name").get_attribute("href")
                        print(f"County URL: {county_url}")
                        counties_urls[county_name] = county_url
            except Exception as e:
                print(f"Error getting counties: {e}")
                # Если нет dropdown, возможно прямой URL
                counties_urls[base_url] = base_url

    return counties_urls


@app.task
def beacon_get_all_parcels_urls_task(counties_urls: dict) -> list:
    """
    Получить все parcel URLs для Beacon округов
    """
    all_counties_parcels_urls = []

    with Display(visible=False, size=(1920, 1080)) as disp:
        print(f'Display is alive: {disp.is_alive()}')

        with SB(uc=True, headless=False) as sb:
            for name, url in counties_urls.items():
                county_parcels_urls = beacon_get_county_parcels_urls_task(sb, url)
                all_counties_parcels_urls.extend(county_parcels_urls)

    return all_counties_parcels_urls


def beacon_get_county_parcels_urls_task(sb: SB, url: str) -> list:
    """
    Получить URLs всех parcels для одного Beacon округа
    """
    county_parcels_urls = []

    try:
        sb.uc_open_with_reconnect(url, 2)
        scraper_pass_challenge(sb)
        scraper_pass_modal(sb)

        # Beacon может иметь разные селекторы для поиска
        search_selectors = [
            "[class*='tt-upm-address-search-btn']",
            "[id*='btnAddressSearch']",
            "[class*='search-button']"
        ]
        
        for selector in search_selectors:
            try:
                sb.js_click_if_visible(selector=selector, by="css selector", timeout=3)
                break
            except:
                continue

        # Нажать кнопку поиска (получить все результаты)
        sb.js_click_if_visible(selector="[id*='_ctl01_btnSearch']", by="css selector", timeout=3)
        scraper_pass_modal(sb)

        # Получить ссылки на parcels
        parcel_selectors = [
            "[id*='_lnkParcelID']",
            "[class*='parcel-link']",
            "a[href*='parcel']"
        ]
        
        urls = []
        for selector in parcel_selectors:
            try:
                urls = sb.find_elements(selector=selector, by="css selector")
                if len(urls) > 0:
                    break
            except:
                continue

        if not len(urls) > 0:
            raise Exception("Не удалось получить список parcels")

        for parcel_url in urls:
            county_parcels_urls.append(parcel_url.get_attribute("href"))

    except Exception as e:
        print(f"{url} -> Error")
        print(e)

    return county_parcels_urls


@app.task
def beacon_parse_single_html_task(html: str) -> dict:
    """
    Парсинг HTML страницы Beacon (расширенная версия QPublic)
    
    Beacon часто имеет больше данных, чем базовый QPublic
    """
    doc = BeautifulSoup(html, "html.parser")
    
    data = {}
    
    try:
        # Основная информация (как в QPublic)
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
            
            # MAILING ADDRESS (Beacon часто показывает)
            mailing = info_table.find(id=re.compile("_lblMailingAddress"))
            if mailing:
                data['mailing_address'] = mailing.text.strip()
            
            # PROPERTY TYPE
            prop_type = info_table.find(id=re.compile("_lblPropertyType|_lblUseCode"))
            if prop_type:
                data['property_type'] = prop_type.text.strip()
            
            # BUILDING DETAILS
            sqft = info_table.find(id=re.compile("_lblSquareFeet|_lblLivingArea"))
            if sqft:
                data['building_sqft'] = sqft.text.strip()
            
            year_built = info_table.find(id=re.compile("_lblYearBuilt"))
            if year_built:
                data['year_built'] = year_built.text.strip()
            
            bedrooms = info_table.find(id=re.compile("_lblBedrooms"))
            if bedrooms:
                data['bedrooms'] = bedrooms.text.strip()
            
            bathrooms = info_table.find(id=re.compile("_lblBathrooms"))
            if bathrooms:
                data['bathrooms'] = bathrooms.text.strip()
            
            # LOT SIZE
            lot_size = info_table.find(id=re.compile("_lblLotSize|_lblAcres"))
            if lot_size:
                data['lot_size'] = lot_size.text.strip()
            
            # ZONING
            zoning = info_table.find(id=re.compile("_lblZoning"))
            if zoning:
                data['zoning'] = zoning.text.strip()

        # TAX INFORMATION
        tax_table = doc.find(id=re.compile("_grdValuation|_grdTax"))
        if tax_table:
            total_values_rows = tax_table.find_all(class_=re.compile("double-total-line|total-row"))
            
            if len(total_values_rows) >= 3:
                # Beacon обычно показывает: Current Year, Last Year, Total
                total_due_row = total_values_rows[2].find_all(class_=re.compile("value-column"))
                if total_due_row:
                    data['total_due_amount'] = total_due_row[0].text.strip()
                
                last_year_row = total_values_rows[1].find_all(class_=re.compile("value-column"))
                if last_year_row:
                    data['last_year_due_amount'] = last_year_row[0].text.strip()
            
            # ASSESSED VALUES
            # Beacon показывает Land, Building, Total values
            assessed_rows = tax_table.find_all('tr')
            for row in assessed_rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].text.strip().lower()
                    value = cells[1].text.strip()
                    
                    if 'land' in label:
                        data['land_value'] = value
                    elif 'building' in label or 'improvement' in label:
                        data['improvement_value'] = value
                    elif 'total' in label or 'market' in label:
                        data['market_value'] = value
                    elif 'assessed' in label:
                        data['assessed_value'] = value

        # SALES HISTORY
        sales_table = doc.find(id=re.compile("_grdSales|_grdTransfer"))
        if sales_table:
            # Последняя продажа - обычно первая строка после заголовка
            rows = sales_table.find_all('tr')
            if len(rows) > 1:
                cells = rows[1].find_all('td')
                if len(cells) >= 3:
                    data['last_sale_date'] = cells[0].text.strip()
                    data['last_sale_price'] = cells[1].text.strip()
                    if len(cells) >= 4:
                        data['deed_book'] = cells[2].text.strip()
                        data['deed_page'] = cells[3].text.strip()

        # EXEMPTIONS
        exemption_table = doc.find(id=re.compile("_grdExemption"))
        if exemption_table:
            exemptions = []
            rows = exemption_table.find_all('tr')
            for row in rows[1:]:  # Skip header
                cells = row.find_all('td')
                if cells:
                    exemptions.append(cells[0].text.strip())
            if exemptions:
                data['exemptions'] = ', '.join(exemptions)

        # IMAGE URLS
        image_links = doc.find_all('img', src=re.compile("property|parcel|building", re.IGNORECASE))
        if image_links:
            data['image_urls'] = [img['src'] for img in image_links if 'src' in img.attrs]

        # MAP URL
        map_link = doc.find('a', href=re.compile("map|gis", re.IGNORECASE))
        if map_link and 'href' in map_link.attrs:
            data['map_url'] = map_link['href']

    except Exception as e:
        print(f"Error parsing Beacon HTML: {e}")
        data['parse_error'] = str(e)

    return data


# Конфигурации для популярных Beacon округов
BEACON_CONFIGS = {
    'maricopa_county_az': {
        'base_url': 'https://mcassessor.maricopa.gov',
        'county': 'maricopa_az',
        'state': 'AZ',
        'app_id': 'TBD'  # Нужно определить из URL
    },
    'king_county_wa': {
        'base_url': 'https://blue.kingcounty.com',
        'county': 'king_wa',
        'state': 'WA',
        'app_id': 'TBD'
    },
    'hillsborough_county_fl': {
        'base_url': 'https://www.hcpafl.org',
        'county': 'hillsborough_fl',
        'state': 'FL',
        'app_id': 'TBD'
    },
    'pinellas_county_fl': {
        'base_url': 'https://www.pcpao.org',
        'county': 'pinellas_fl',
        'state': 'FL',
        'app_id': 'TBD'
    }
}

