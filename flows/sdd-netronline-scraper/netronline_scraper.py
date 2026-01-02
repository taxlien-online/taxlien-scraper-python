#!/usr/bin/env python3
"""
NetrOnline County Data Scraper

Scrapes county office URLs from publicrecords.netronline.com for all 50 US states.

Usage:
    python3 netronline_scraper.py                          # Scrape all 50 states
    python3 netronline_scraper.py --states FL NJ CO        # Scrape specific states
    python3 netronline_scraper.py --states FL --limit 3    # Scrape 3 counties only (testing)
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import argparse
from datetime import datetime
from typing import List, Dict

# Task 1.1: State Code Mapping
# Maps 2-letter state codes to sources.csv format
STATE_MAPPING = {
    'AL': 'alabama',
    'AK': 'alaska',
    'AZ': 'arizona',
    'AR': 'arkansas',
    'CA': 'california',
    'CO': 'colorado',
    'CT': 'connecticut',
    'DE': 'delaware',
    'FL': 'fl_',
    'GA': 'georgia',
    'HI': 'hawaii',
    'ID': 'idaho',
    'IL': 'illinois',
    'IN': 'indiana',
    'IA': 'iowa',
    'KS': 'kansas',
    'KY': 'kentucky',
    'LA': 'louisiana',
    'ME': 'maine',
    'MD': 'maryland',
    'MA': 'massachusetts',
    'MI': 'michigan',
    'MN': 'minnesota',
    'MS': 'mississippi',
    'MO': 'missouri',
    'MT': 'montana',
    'NE': 'nebraska',
    'NV': 'nevada',
    'NH': 'new_hampshire',
    'NJ': 'new_jersey',
    'NM': 'new_mexico',
    'NY': 'new_york',
    'NC': 'north_carolina',
    'ND': 'north_dakota',
    'OH': 'ohio',
    'OK': 'oklahoma',
    'OR': 'oregon',
    'PA': 'pennsylvania',
    'RI': 'rhode_island',
    'SC': 'south_carolina',
    'SD': 'south_dakota',
    'TN': 'tennessee',
    'TX': 'texas',
    'UT': 'utah',
    'VT': 'vermont',
    'VA': 'virginia',
    'WA': 'washington',
    'WV': 'west_virginia',
    'WI': 'wisconsin',
    'WY': 'wyoming'
}


# Task 1.2: Office Categorization
def categorize_office(office_name: str) -> str:
    """
    Categorize office by name keywords.

    Args:
        office_name: Office name from NetrOnline (e.g., "Property Appraiser")

    Returns:
        Category: assessor, tax, gis, recorder, taxation, or other
    """
    name_lower = office_name.lower()

    # Check for assessor/appraiser
    if any(kw in name_lower for kw in ['property appraiser', 'assessor', 'apprais']):
        return 'assessor'

    # Check for tax collector
    elif any(kw in name_lower for kw in ['tax collector', 'treasurer', 'tax']):
        return 'tax'

    # Check for GIS/mapping
    elif any(kw in name_lower for kw in ['gis', 'mapping', 'map']):
        return 'gis'

    # Check for clerk/recorder
    elif any(kw in name_lower for kw in ['clerk', 'recorder', 'deed', 'register']):
        return 'recorder'

    # Check for board of taxation
    elif any(kw in name_lower for kw in ['board of taxation']):
        return 'taxation'

    else:
        return 'other'


# Task 1.3: State County List Scraper
def get_counties_for_state(state_code: str) -> List[str]:
    """
    Get list of counties for a state from NetrOnline.

    Args:
        state_code: 2-letter state code (e.g., "FL")

    Returns:
        List of county names (lowercase, URL format)
    """
    url = f'https://publicrecords.netronline.com/state/{state_code}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all county links
        county_links = soup.find_all('a', href=lambda x: x and '/county/' in x)
        counties = []

        for link in county_links:
            # Extract county name from URL: /state/FL/county/alachua → alachua
            href = link['href']
            county_name = href.split('/county/')[-1]
            counties.append(county_name)

        return counties

    except Exception as e:
        print(f"  ERROR getting counties: {e}")
        return []


# Task 1.4: County Data Scraper
def scrape_county(state_code: str, county: str) -> Dict:
    """
    Scrape office data for a county from NetrOnline.

    Args:
        state_code: 2-letter state code (e.g., "FL")
        county: County name in URL format (e.g., "alachua")

    Returns:
        Dictionary with state, county, and offices data
    """
    url = f'https://publicrecords.netronline.com/state/{state_code}/county/{county}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find office table (div-table structure)
        table = soup.find('div', class_='div-table')
        if not table:
            return {
                'state': STATE_MAPPING.get(state_code, f'{state_code.lower()}_'),
                'county': county.lower(),
                'offices': {}
            }

        offices = {}
        rows = table.find_all('div', class_='div-table-row')

        for row in rows:
            cols = row.find_all('div', class_='div-table-col')
            if len(cols) >= 2:
                office_name = cols[0].text.strip()

                # Skip header row
                if office_name in ['Name', 'Products available']:
                    continue

                # Extract URL
                link = row.find('a', href=lambda x: x and x.startswith('http'))
                if link:
                    office_url = link['href']
                    office_type = categorize_office(office_name)

                    # Store by type (keep first occurrence)
                    if office_type not in offices:
                        offices[office_type] = office_url

        return {
            'state': STATE_MAPPING.get(state_code, f'{state_code.lower()}_'),
            'county': county.lower(),
            'offices': offices
        }

    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'state': STATE_MAPPING.get(state_code, f'{state_code.lower()}_'),
            'county': county.lower(),
            'offices': {}
        }


# Task 2.1: CSV Row Formatter
def county_to_csv_row(county_data: Dict) -> Dict:
    """
    Convert county data to CSV row format matching sources.csv.

    Args:
        county_data: Dictionary from scrape_county()

    Returns:
        Dictionary with CSV column names as keys
    """
    offices = county_data['offices']

    return {
        'state': county_data['state'],
        'county': county_data['county'],
        'Assessor / Appraser': offices.get('assessor', ''),
        'Treasurer / Tax / Tax collector': offices.get('tax', ''),
        'Mapping / Gis': offices.get('gis', ''),
        'Recorder / County clerk': offices.get('recorder', ''),
        'Board of taxation': offices.get('taxation', ''),
        'Register of Deeds / Historic Aerials': '',
        'N': '',
        'RA': '',
        'AP': '',
        'TX': '',
        'R': '',
        'example': ''
    }


# Task 2.2: CSV Writer
def write_to_csv(counties_data: List[Dict], output_file: str) -> str:
    """
    Write scraped data to CSV file.

    Args:
        counties_data: List of county dictionaries
        output_file: Output CSV filename

    Returns:
        Actual filename with timestamp
    """
    # Add timestamp to filename
    timestamp = datetime.now().strftime('%Y-%m-%d')
    output_file = output_file.replace('.csv', f'_{timestamp}.csv')

    fieldnames = [
        'state', 'county', 'Assessor / Appraser',
        'Treasurer / Tax / Tax collector', 'Mapping / Gis',
        'Recorder / County clerk', 'Board of taxation',
        'Register of Deeds / Historic Aerials',
        'N', 'RA', 'AP', 'TX', 'R', 'example'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for county_data in counties_data:
            row = county_to_csv_row(county_data)
            writer.writerow(row)

    print(f'\n✓ Saved to {output_file}')
    return output_file


# Task 3.1: Main Scraper Function
def scrape_all_states(state_filter=None, limit_per_state=None):
    """
    Scrape all states or filtered list.

    Args:
        state_filter: Optional list of state codes to scrape
        limit_per_state: Optional limit on counties per state (for testing)

    Returns:
        Tuple of (counties_data, stats)
    """
    states = state_filter or list(STATE_MAPPING.keys())
    all_counties = []
    stats = {
        'total_counties': 0,
        'successful': 0,
        'failed': 0,
        'total_urls': 0
    }

    for i, state_code in enumerate(states, 1):
        print(f'\n[{i}/{len(states)}] Scraping {state_code}...')

        try:
            # Get county list
            counties = get_counties_for_state(state_code)
            print(f'  Found {len(counties)} counties')

            # Apply limit if specified
            if limit_per_state:
                counties = counties[:limit_per_state]

            # Scrape each county
            for j, county_name in enumerate(counties, 1):
                print(f'    [{j}/{len(counties)}] {county_name}...', end=' ')

                try:
                    county_data = scrape_county(state_code, county_name)
                    all_counties.append(county_data)

                    url_count = len(county_data['offices'])
                    stats['successful'] += 1
                    stats['total_urls'] += url_count
                    print(f'{url_count} URLs')

                    # Polite delay
                    time.sleep(random.uniform(1, 2))

                except Exception as e:
                    stats['failed'] += 1
                    print(f'ERROR: {e}')

            stats['total_counties'] += len(counties)

        except Exception as e:
            print(f'  ERROR: Failed to get counties: {e}')

    # Print summary
    print(f'\n{"="*80}')
    print(f'SCRAPE SUMMARY')
    print(f'{"="*80}')
    print(f'Total counties: {stats["total_counties"]}')
    print(f'Successful: {stats["successful"]}')
    print(f'Failed: {stats["failed"]}')
    print(f'Total URLs extracted: {stats["total_urls"]}')
    if stats["total_counties"] > 0:
        success_rate = stats["successful"] / stats["total_counties"] * 100
        print(f'Success rate: {success_rate:.1f}%')

    return all_counties, stats


# Task 3.2: CLI Interface
def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Scrape county data from publicrecords.netronline.com'
    )
    parser.add_argument(
        '--states',
        nargs='+',
        help='Specific states to scrape (e.g., FL NJ CO). Default: all 50 states'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit counties per state (for testing)'
    )
    parser.add_argument(
        '--output',
        default='flows/sdd-netronline-scraper/netronline_counties.csv',
        help='Output CSV filename'
    )

    args = parser.parse_args()

    print('NetrOnline County Scraper')
    print('=' * 80)

    # Run scraper
    counties_data, stats = scrape_all_states(
        state_filter=args.states,
        limit_per_state=args.limit
    )

    # Write to CSV
    if counties_data:
        output_file = write_to_csv(counties_data, args.output)
        print(f'\nDone! Scraped {len(counties_data)} counties')
    else:
        print('\nNo data collected')


if __name__ == '__main__':
    main()
