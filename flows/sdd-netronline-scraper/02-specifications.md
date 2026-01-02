# Specifications: NetrOnline County Data Scraper

**Date:** 2026-01-01
**Phase:** SPECIFICATIONS
**Status:** DRAFT

---

## 1. System Overview

### 1.1 Architecture

```
NetrOnline Scraper
│
├── State Iterator
│   └── For each state code (FL, NJ, CO, ...)
│
├── County List Scraper
│   ├── GET https://publicrecords.netronline.com/state/{STATE}
│   └── Extract county links
│
├── County Data Scraper
│   ├── GET https://publicrecords.netronline.com/state/{STATE}/county/{COUNTY}
│   ├── Parse div-table structure
│   └── Extract office URLs
│
├── Data Normalizer
│   ├── Categorize offices (Assessor, Tax, GIS, Recorder)
│   ├── Normalize state codes (FL → fl_)
│   └── Validate URLs
│
└── CSV Writer
    ├── Write to netronline_counties.csv
    └── Generate summary report
```

### 1.2 Data Flow

```
[State List] → [State Scraper] → [County List]
                                       ↓
                            [County Scraper] → [Office URLs]
                                                     ↓
                                        [Normalizer] → [Categorized Data]
                                                            ↓
                                                    [CSV Writer]
                                                            ↓
                                            [netronline_counties.csv]
```

---

## 2. HTML Structure Analysis

### 2.1 State Page Structure

**URL Pattern:** `https://publicrecords.netronline.com/state/{STATE}`

**HTML Structure:**
```html
<a href="/state/FL/county/alachua">Alachua</a>
<a href="/state/FL/county/baker">Baker</a>
<a href="/state/FL/county/bay">Bay</a>
...
```

**Extraction Logic:**
```python
soup.find_all('a', href=lambda x: x and '/county/' in x)
```

**Expected Output:**
```python
[
    {'state': 'FL', 'county': 'alachua'},
    {'state': 'FL', 'county': 'baker'},
    ...
]
```

---

### 2.2 County Page Structure

**URL Pattern:** `https://publicrecords.netronline.com/state/{STATE}/county/{COUNTY}`

**HTML Structure:**
```html
<div class="div-table">
  <div class="div-table-row head responsive">
    <div class="div-table-col column-4 large">Name</div>
    <div class="div-table-col column-4">Phone</div>
    <div class="div-table-col column-4">Online</div>
    <div class="div-table-col column-4">Report</div>
  </div>

  <div class="div-table-row responsive">
    <div class="div-table-col column-4 large">Alachua Clerk / Recorder</div>
    <div class="div-table-col column-4">(352) 374-3625</div>
    <div class="div-table-col column-4">
      <a href="https://www.alachuacounty.us/depts/clerk/...">Go to Data Online</a>
    </div>
    <div class="div-table-col column-4">Fix</div>
  </div>

  <div class="div-table-row responsive">
    <div class="div-table-col column-4 large">Alachua Property Appraiser</div>
    <div class="div-table-col column-4">(352) 374-5230</div>
    <div class="div-table-col column-4">
      <a href="https://qpublic.schneidercorp.com/...">Go to Data Online</a>
    </div>
    <div class="div-table-col column-4">Fix</div>
  </div>

  <div class="div-table-row responsive">
    <div class="div-table-col column-4 large">Alachua Tax Collector</div>
    <div class="div-table-col column-4">(352) 374-5236</div>
    <div class="div-table-col column-4">
      <a href="https://alachua.county-taxes.com/...">Go to Data Online</a>
    </div>
    <div class="div-table-col column-4">Fix</div>
  </div>

  <div class="div-table-row responsive">
    <div class="div-table-col column-4 large">Alachua NETR Mapping and GIS</div>
    <div class="div-table-col column-4"></div>
    <div class="div-table-col column-4">
      <a href="https://map.netronline.com/florida-alachua/12001">Map</a>
    </div>
    <div class="div-table-col column-4"></div>
  </div>
</div>
```

**Extraction Logic:**
```python
table = soup.find('div', class_='div-table')
rows = table.find_all('div', class_='div-table-row')

for row in rows:
    cols = row.find_all('div', class_='div-table-col')
    if len(cols) >= 2:
        office_name = cols[0].text.strip()
        link = row.find('a', href=lambda x: x and x.startswith('http'))
        if link:
            office_url = link['href']
```

---

## 3. Data Models

### 3.1 County Model

```python
@dataclass
class County:
    """Represents a county with its public offices"""
    state: str              # 2-letter code: "FL", "NJ"
    county: str             # Lowercase: "alachua", "bergen"
    offices: List[Office]   # List of public offices

    def to_csv_row(self) -> dict:
        """Convert to sources.csv format"""
        return {
            'state': self.normalize_state(),
            'county': self.county,
            'Assessor / Appraser': self.get_office_url('assessor'),
            'Treasurer / Tax / Tax collector': self.get_office_url('tax'),
            'Mapping / Gis': self.get_office_url('gis'),
            'Recorder / County clerk': self.get_office_url('recorder'),
            'Board of taxation': self.get_office_url('taxation'),
            'Register of Deeds / Historic Aerials': '',
            'N': '',
            'RA': '',
            'AP': '',
            'TX': '',
            'R': '',
            'example': ''
        }

    def normalize_state(self) -> str:
        """Convert state code to sources.csv format"""
        # FL → fl_
        # NJ → new_jersey
        # ...
```

### 3.2 Office Model

```python
@dataclass
class Office:
    """Represents a public office with its URL"""
    name: str          # Raw name from website: "Alachua Property Appraiser"
    url: str           # Office website URL
    phone: str = ""    # Optional phone number
    office_type: str = "unknown"  # Categorized: assessor, tax, gis, recorder, etc.

    def categorize(self):
        """Categorize office by name keywords"""
        name_lower = self.name.lower()

        if any(kw in name_lower for kw in ['property appraiser', 'assessor', 'appraisal']):
            self.office_type = 'assessor'
        elif any(kw in name_lower for kw in ['tax collector', 'treasurer', 'tax']):
            self.office_type = 'tax'
        elif any(kw in name_lower for kw in ['gis', 'mapping', 'map']):
            self.office_type = 'gis'
        elif any(kw in name_lower for kw in ['clerk', 'recorder', 'deed', 'register']):
            self.office_type = 'recorder'
        elif any(kw in name_lower for kw in ['board of taxation']):
            self.office_type = 'taxation'
        else:
            self.office_type = 'other'
```

### 3.3 Scrape Result Model

```python
@dataclass
class ScrapeResult:
    """Result of scraping a single county"""
    state: str
    county: str
    success: bool
    offices_found: int = 0
    error: str = ""
    timestamp: str = ""
```

---

## 4. State Code Mapping

### 4.1 State Normalization

**NetrOnline uses 2-letter codes:**
- FL, NJ, CO, MD, CA, TX, etc.

**sources.csv uses:**
- Mostly lowercase with underscore: `fl_`, `az_`
- Multi-word states: `new_jersey`, `new_mexico`, `new_york`, etc.

**Mapping Table:**

| NetrOnline | sources.csv | State Name |
|------------|-------------|------------|
| FL | fl_ | Florida |
| NJ | new_jersey | New Jersey |
| NY | new_york | New York |
| NM | new_mexico | New Mexico |
| NC | north_carolina | North Carolina |
| ND | north_dakota | North Dakota |
| SC | south_carolina | South Carolina |
| SD | south_dakota | South Dakota |
| WV | west_virginia | West Virginia |
| RI | rhode_island | Rhode Island |
| NH | new_hampshire | New Hampshire |
| AL | al_ | Alabama |
| AK | ak_ | Alaska |
| AZ | az_ | Arizona |
| AR | ar_ | Arkansas |
| CA | ca_ | California |
| CO | co_ | Colorado |
| CT | ct_ | Connecticut |
| DE | de_ | Delaware |
| GA | ga_ | Georgia |
| HI | hi_ | Hawaii |
| ID | id_ | Idaho |
| IL | il_ | Illinois |
| IN | in_ | Indiana |
| IA | ia_ | Iowa |
| KS | ks_ | Kansas |
| KY | ky_ | Kentucky |
| LA | la_ | Louisiana |
| ME | me_ | Maine |
| MD | md_ | Maryland |
| MA | ma_ | Massachusetts |
| MI | mi_ | Michigan |
| MN | mn_ | Minnesota |
| MS | ms_ | Mississippi |
| MO | mo_ | Missouri |
| MT | mt_ | Montana |
| NE | ne_ | Nebraska |
| NV | nv_ | Nevada |
| OH | oh_ | Ohio |
| OK | ok_ | Oklahoma |
| OR | or_ | Oregon |
| PA | pa_ | Pennsylvania |
| TN | tn_ | Tennessee |
| TX | tx_ | Texas |
| UT | ut_ | Utah |
| VT | vt_ | Vermont |
| VA | va_ | Virginia |
| WA | wa_ | Washington |
| WI | wi_ | Wisconsin |
| WY | wy_ | Wyoming |

**Implementation:**
```python
STATE_MAPPING = {
    'FL': 'fl_',
    'NJ': 'new_jersey',
    'NY': 'new_york',
    'NM': 'new_mexico',
    'NC': 'north_carolina',
    'ND': 'north_dakota',
    'SC': 'south_carolina',
    'SD': 'south_dakota',
    'WV': 'west_virginia',
    'RI': 'rhode_island',
    'NH': 'new_hampshire',
    # Single-letter states get underscore
    **{code: f'{code.lower()}_' for code in [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'GA', 'HI',
        'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA',
        'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'OH', 'OK', 'OR',
        'PA', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WI', 'WY'
    ]}
}
```

---

## 5. Scraper Implementation

### 5.1 State Scraper

**Class:** `StateScraper`

**Methods:**

#### `get_counties(state_code: str) -> List[str]`
```python
def get_counties(self, state_code: str) -> List[str]:
    """Get list of counties for a state"""
    url = f'https://publicrecords.netronline.com/state/{state_code}'
    response = requests.get(url, headers=self.headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')

    county_links = soup.find_all('a', href=lambda x: x and '/county/' in x)
    counties = []

    for link in county_links:
        # Extract county name from href: /state/FL/county/alachua
        href = link['href']
        county_name = href.split('/county/')[-1]
        counties.append(county_name)

    return counties
```

**Expected counties per state:**
- FL: 67 counties
- NJ: 21 counties
- CO: 64 counties
- Total US: ~3,000-3,200 counties

---

### 5.2 County Scraper

**Class:** `CountyScraper`

**Methods:**

#### `scrape_county(state_code: str, county: str) -> County`
```python
def scrape_county(self, state_code: str, county: str) -> County:
    """Scrape office data for a county"""
    url = f'https://publicrecords.netronline.com/state/{state_code}/county/{county}'
    response = requests.get(url, headers=self.headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find office table
    table = soup.find('div', class_='div-table')
    if not table:
        raise ValueError(f"No data table found for {state_code} {county}")

    offices = []
    rows = table.find_all('div', class_='div-table-row')

    for row in rows:
        cols = row.find_all('div', class_='div-table-col')
        if len(cols) >= 2:
            office_name = cols[0].text.strip()

            # Skip header row
            if office_name in ['Name', 'Products available']:
                continue

            # Extract phone if available
            phone = cols[1].text.strip() if len(cols) > 1 else ""

            # Extract URL
            link = row.find('a', href=lambda x: x and x.startswith('http'))
            if link:
                office_url = link['href']

                # Create office object
                office = Office(
                    name=office_name,
                    url=office_url,
                    phone=phone
                )
                office.categorize()
                offices.append(office)

    return County(state=state_code, county=county, offices=offices)
```

---

### 5.3 Main Scraper Orchestrator

**Class:** `NetrOnlineScraper`

```python
class NetrOnlineScraper:
    def __init__(self, output_file='netronline_counties.csv'):
        self.output_file = output_file
        self.state_scraper = StateScraper()
        self.county_scraper = CountyScraper()
        self.stats = {
            'total_counties': 0,
            'successful': 0,
            'failed': 0,
            'total_urls': 0
        }

    def scrape_all_states(self, state_filter=None):
        """Scrape all states or filtered list"""
        states = state_filter or list(STATE_MAPPING.keys())

        all_counties = []

        for i, state_code in enumerate(states, 1):
            print(f'[{i}/{len(states)}] Scraping {state_code}...')

            try:
                # Get county list
                counties = self.state_scraper.get_counties(state_code)
                print(f'  Found {len(counties)} counties')

                # Scrape each county
                for j, county_name in enumerate(counties, 1):
                    print(f'    [{j}/{len(counties)}] {county_name}...', end=' ')

                    try:
                        county_data = self.county_scraper.scrape_county(state_code, county_name)
                        all_counties.append(county_data)

                        self.stats['successful'] += 1
                        self.stats['total_urls'] += len(county_data.offices)
                        print(f'{len(county_data.offices)} URLs')

                        # Polite delay
                        time.sleep(random.uniform(1, 2))

                    except Exception as e:
                        self.stats['failed'] += 1
                        print(f'ERROR: {e}')

                self.stats['total_counties'] += len(counties)

            except Exception as e:
                print(f'  ERROR: Failed to get counties: {e}')

        # Write to CSV
        self.write_csv(all_counties)
        self.print_summary()

        return all_counties
```

---

## 6. CSV Output Format

### 6.1 Output File Structure

**Filename:** `flows/sdd-netronline-scraper/netronline_counties_YYYY-MM-DD.csv`

**Format:** Match existing sources.csv

```csv
state,county,Assessor / Appraser,Treasurer / Tax / Tax collector,Mapping / Gis,Recorder / County clerk,Board of taxation,Register of Deeds / Historic Aerials,N,RA,AP,TX,R,example
fl_,alachua,https://qpublic.schneidercorp.com/...,https://alachua.county-taxes.com/...,https://map.netronline.com/...,https://www.alachuacounty.us/...,,,,,,,,,
fl_,baker,https://...,https://...,,https://...,,,,,,,,
```

**Column Mapping:**
- `state` → Normalized state code (fl_, new_jersey, etc.)
- `county` → Lowercase county name
- `Assessor / Appraser` → URL from office_type='assessor'
- `Treasurer / Tax / Tax collector` → URL from office_type='tax'
- `Mapping / Gis` → URL from office_type='gis'
- `Recorder / County clerk` → URL from office_type='recorder'
- `Board of taxation` → URL from office_type='taxation'
- Rest → Empty (populated manually or from other sources)

---

## 7. Error Handling

### 7.1 Network Errors

**Scenarios:**
- Timeout (30 seconds)
- Connection refused
- 404 Not Found
- 500 Server Error

**Handling:**
```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.Timeout:
    log_error(f"Timeout for {url}")
    return None
except requests.HTTPError as e:
    log_error(f"HTTP {e.response.status_code} for {url}")
    return None
except Exception as e:
    log_error(f"Network error for {url}: {e}")
    return None
```

---

### 7.2 Parsing Errors

**Scenarios:**
- No div-table found
- Empty table
- Malformed HTML

**Handling:**
```python
table = soup.find('div', class_='div-table')
if not table:
    log_error(f"No data table found for {state} {county}")
    return County(state=state, county=county, offices=[])

rows = table.find_all('div', class_='div-table-row')
if len(rows) <= 1:  # Only header row
    log_warning(f"No offices found for {state} {county}")
```

---

### 7.3 Rate Limiting

**Strategy:**
- Polite delays: 1-2 seconds between requests
- Exponential backoff on errors
- Respect robots.txt (if exists)

```python
# After each county scrape
time.sleep(random.uniform(1, 2))

# On error, increase delay
if error_count > 3:
    time.sleep(5)
```

---

## 8. Performance Characteristics

### 8.1 Expected Throughput

**Per County:**
- Network request: ~0.5-1 second
- Parsing: ~0.1 second
- Polite delay: 1-2 seconds
- **Total:** ~2-3 seconds per county

**Full Scrape (3,000 counties):**
- Best case: 2 sec/county × 3,000 = 100 minutes (~1.7 hours)
- Worst case: 3 sec/county × 3,000 = 150 minutes (~2.5 hours)
- **Estimated:** 2 hours for all 50 states

**Per State:**
- FL (67 counties): ~3-5 minutes
- NJ (21 counties): ~1-2 minutes
- CO (64 counties): ~3-5 minutes

---

### 8.2 Resource Usage

**Memory:**
- County objects: ~1KB each
- 3,000 counties: ~3MB
- BeautifulSoup overhead: ~100MB
- **Total:** < 200MB RAM

**Disk:**
- Output CSV: ~500KB - 2MB
- Log file: ~100KB
- **Total:** < 5MB

**Network:**
- Bandwidth: ~1-2 Mbps (polite scraping)
- Total data transferred: ~100-200MB

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Not implemented** (one-time scraper)

**Manual testing approach:**
- Test on 1 county (FL Alachua)
- Test on 3 states (FL, NJ, CO)
- Test full scrape with `--limit 50`

---

### 9.2 Integration Tests

**Test 1:** State scraper
```bash
python3 netronline_scraper.py --states FL --dry-run
# Expected: List of 67 FL counties
```

**Test 2:** County scraper
```bash
python3 netronline_scraper.py --states FL --limit 3
# Expected: CSV with 3 counties
```

**Test 3:** Full scrape (small)
```bash
python3 netronline_scraper.py --states FL NJ CO
# Expected: CSV with ~150 counties
```

**Test 4:** Full scrape (production)
```bash
python3 netronline_scraper.py
# Expected: CSV with ~3,000 counties
```

---

### 9.3 Validation Tests

**After scrape:**
1. Check row count: ~3,000 rows
2. Check URL count: ~8,000+ URLs
3. Verify state normalization: All lowercase with underscore
4. Spot-check URLs: Sample 20 random URLs, verify reachable

---

## 10. Merge Utility Specifications

### 10.1 Merge Logic

**Purpose:** Intelligently merge NetrOnline data with existing sources.csv

**Algorithm:**
```python
def merge_sources(existing_csv, netronline_csv, output_csv):
    """Merge two CSV files"""

    # Load both files
    existing = load_csv(existing_csv)  # 130 rows
    netronline = load_csv(netronline_csv)  # 3,000 rows

    # Create merged dict keyed by (state, county)
    merged = {}

    # First, add all existing rows
    for row in existing:
        key = (row['state'], row['county'])
        merged[key] = row

    # Then, merge or add NetrOnline rows
    for row in netronline:
        key = (row['state'], row['county'])

        if key in merged:
            # County exists - merge fields
            for field in ['Assessor / Appraser', 'Treasurer / Tax / Tax collector', 'Mapping / Gis', 'Recorder / County clerk']:
                # Fill empty fields from NetrOnline
                if not merged[key][field] and row[field]:
                    merged[key][field] = row[field]
        else:
            # New county - add it
            merged[key] = row

    # Convert back to list and sort
    output_rows = list(merged.values())
    output_rows.sort(key=lambda x: (x['state'], x['county']))

    # Write to CSV
    write_csv(output_csv, output_rows)

    return output_rows
```

**Expected output:**
- Rows: ~3,000 (130 existing + ~2,870 new)
- Existing counties: Fields preserved, empty fields filled from NetrOnline
- New counties: All fields from NetrOnline

---

## 11. CLI Interface

### 11.1 Command-Line Arguments

```bash
python3 netronline_scraper.py [OPTIONS]

Options:
  --states STATE...      Specific states to scrape (e.g., FL NJ CO)
                         Default: all 50 states

  --limit N              Limit counties per state (for testing)
                         Default: unlimited

  --output FILE          Output CSV filename
                         Default: netronline_counties_YYYY-MM-DD.csv

  --dry-run              Show what would be scraped, don't download

  --resume               Resume from last state (uses checkpoint file)

  --merge EXISTING       Merge with existing sources.csv
                         Creates sources_merged.csv
```

### 11.2 Usage Examples

**Test on Florida only:**
```bash
python3 netronline_scraper.py --states FL
```

**Test on first 10 counties per state:**
```bash
python3 netronline_scraper.py --states FL NJ CO --limit 10
```

**Full scrape:**
```bash
python3 netronline_scraper.py
```

**Merge with existing:**
```bash
python3 netronline_scraper.py --merge flows/sdd-sample-collector/sources.csv
```

---

## ✅ Specifications Approval Checklist

Before moving to PLAN phase:

- [x] System architecture documented
- [x] HTML structure analyzed
- [x] Data models defined
- [x] State normalization mapped
- [x] Scraper implementation specified
- [x] Error handling documented
- [x] Performance estimates provided
- [x] Testing strategy outlined
- [x] Merge utility specified
- [x] CLI interface defined
- [ ] **User approval:** Specifications reviewed and approved

---

**Status:** READY FOR REVIEW
**Next Phase:** PLAN
**Blocker:** Awaiting user approval
