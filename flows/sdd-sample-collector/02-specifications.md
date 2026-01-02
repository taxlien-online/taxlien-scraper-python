# Specifications: Sample HTML Collector for Tax Lien Data

**Date:** 2026-01-01
**Phase:** SPECIFICATIONS
**Status:** DRAFT

---

## 1. System Overview

### 1.1 Architecture

```
Sample Collector System
│
├── Data Input Layer
│   └── CSV Reader → Parses sources.csv with county metadata
│
├── URL Generation Layer
│   ├── PlatformURLGenerator → Platform-specific URL patterns
│   └── SampleURL (data class) → URL metadata container
│
├── Download Layer
│   ├── HTTP Downloader → Simple requests for static pages
│   └── Selenium Downloader → JavaScript-heavy pages
│
├── Storage Layer
│   ├── HTML Files → Saved samples
│   ├── Metadata JSON → Per-sample metadata
│   └── Screenshots → For Selenium downloads
│
└── Orchestration Layer
    ├── SampleCollector → High-level coordinator
    └── SampleDownloader → Download-focused coordinator
```

### 1.2 Component Relationships

```
[sources.csv]
    ↓
[SampleCollector._load_counties()]
    ↓
[identify_platform()] → Determines QPublic/Custom GIS/Tyler/etc
    ↓
[PlatformURLGenerator.get_sample_urls()] → Generates working URLs
    ↓
[SampleDownloader.download_county_samples()]
    ↓
    ├─→ [download_url_simple()] → HTTP request
    │       ↓
    │   [Save HTML + metadata.json]
    │
    └─→ [download_url_selenium()] → SeleniumBase
            ↓
        [Save HTML + screenshot + metadata.json]
```

---

## 2. Data Models

### 2.1 SampleURL (Dataclass)

**Purpose:** Container for a single sample URL with metadata

**Fields:**
```python
@dataclass
class SampleURL:
    url: str              # Full URL to download
    parcel_id: str        # Parcel identifier (e.g., "R00010-001")
    page_type: str        # 'assessor', 'tax', 'gis', 'recorder'
    platform: str         # Platform type (e.g., 'qpublic', 'custom_gis')
    county: str           # County name (e.g., 'columbia')
    state: str            # State code (e.g., 'fl_')
    notes: str = ""       # Optional notes
```

**Validation:**
- `url` must be valid HTTP/HTTPS URL
- `page_type` must be in: `['assessor', 'tax', 'gis', 'recorder', 'tangible']`
- `platform` must be in: `['qpublic', 'custom_gis', 'tyler', 'propertytax', 'governmax', 'myfloridacounty', 'custom', 'unknown']`
- `parcel_id` can contain special characters (`-`, `/`, alphanumeric)

### 2.2 Download Metadata JSON

**Purpose:** Track download metadata for each HTML sample

**Schema:**
```json
{
  "url": "https://columbia.floridapa.com/gis/?pin=142S1500061000",
  "parcel_id": "142S1500061000",
  "page_type": "assessor",
  "platform": "custom_gis",
  "county": "columbia",
  "state": "fl_",
  "download_date": "2026-01-01T10:30:00.123456",
  "method": "selenium",
  "status_code": 200,           // Optional: only for HTTP downloads
  "content_length": 45672,
  "screenshot": "assessor_142S1500061000.png",  // Optional: only for Selenium
  "notes": "Working example from sources.csv"
}
```

**File naming:** `{page_type}_{parcel_id}_meta.json`

### 2.3 County Metadata JSON

**Purpose:** Track county configuration and collection status

**Schema:**
```json
{
  "county": "fl_columbia",
  "state": "fl_",
  "county_name": "columbia",
  "platform": "custom_gis",
  "assessor_url": "http://columbia.floridapa.com/gis/",
  "tax_url": "http://fl-columbia-taxcollector.governmax.com/collectmax/collect30.asp",
  "gis_url": "http://columbia.floridapa.com/gis/",
  "recorder_url": "https://www.myfloridacounty.com/ori/index.do",
  "sample_parcel_ids": ["R00010-001", "142S1500061000", "R12074-000"],
  "collection_date": "2026-01-01T10:30:00.123456",
  "indicators": {
    "RA": "",
    "AP": "GIS",
    "TX": "GM",
    "R": "MF"
  }
}
```

**File location:** `samples_collected/{state}/{county}/metadata.json`

### 2.4 Collection Summary JSON

**Purpose:** Overall collection statistics

**Schema:**
```json
{
  "collection_date": "2026-01-01T12:00:00.123456",
  "stats": {
    "total_downloads": 42,
    "successful": 38,
    "failed": 4,
    "by_platform": {
      "qpublic": 12,
      "custom_gis": 18,
      "tyler": 8
    },
    "by_state": {
      "fl_": 30,
      "az_": 8,
      "new jersey": 4
    },
    "by_page_type": {
      "assessor": 20,
      "tax": 10,
      "gis": 8,
      "recorder": 4
    }
  },
  "results": [
    {
      "county": "fl_columbia",
      "downloads": 3,
      "failed": 0,
      "status": "success"
    },
    ...
  ]
}
```

**File location:** `samples_collected/collection_summary.json`

---

## 3. Platform-Specific Behaviors

### 3.1 Platform Identification Logic

**Input:** County data from CSV
**Output:** Platform type string

**Algorithm:**
```python
def identify_platform(county: Dict) -> str:
    assessor_url = county.get('Assessor / Appraser', '').lower()
    tax_url = county.get('Treasurer / Tax / Tax collector', '').lower()
    ap_indicator = county.get('AP', '')
    tx_indicator = county.get('TX', '')

    # Priority 1: URL patterns
    if 'qpublic.schneidercorp.com' in assessor_url
       or 'beacon.schneidercorp.com' in assessor_url:
        return 'qpublic'

    if 'county-taxes.com' in tax_url:
        return 'propertytax'

    if '/gis/' in assessor_url or 'floridapa.com' in assessor_url:
        return 'custom_gis'

    if 'governmax.com' in assessor_url or tax_url:
        return 'governmax'

    # Priority 2: CSV indicators
    if ap_indicator == 'QP':
        return 'qpublic'

    if ap_indicator == 'GIS':
        return 'custom_gis'

    if tx_indicator == 'PT':
        return 'propertytax'

    # Fallback
    return 'unknown'
```

### 3.2 Platform URL Generation

#### Custom GIS (floridapa.com)
**Pattern:** `{base_url}?pin={parcel_id}`
**Example:** `https://columbia.floridapa.com/gis/?pin=142S1500061000`
**Download method:** Selenium (JavaScript-heavy)

**Special handling:**
- May use iframes (`recordSearchContent_1_iframe`)
- Tax link format: `{base_url}/GIS/TaxLink_wait.asp?{parcel_id}`

#### QPublic (Schneider Corp)
**Pattern:** Search-based, no direct parcel URLs
**Example:** `https://qpublic.schneidercorp.com/Application.aspx?AppID=867&LayerID=16385&PageTypeID=4&PageID=7232&Q=1806901892&KeyValue=35-08-13-0000-3900-0200`
**Download method:** Selenium (requires search interaction)

**Special handling:**
- Needs search form submission
- Parcel URLs contain query parameter `Q={hash}&KeyValue={parcel_id}`
- Cannot generate URLs without interactive search

#### PropertyTax (county-taxes.com)
**Pattern:** `{base_url}?parcel={parcel_id}`
**Example:** `https://alachua.county-taxes.com/public/search/property_tax?parcel=01234-000-000`
**Download method:** HTTP (simple)

#### Tyler Technologies
**Pattern:** Search-based with ASPX ViewState
**Example:** `https://eagleassessor.coconino.az.gov/treasurer/treasurerweb/account.jsp?account=R0050197`
**Download method:** Selenium (ASPX ViewState)

**Special handling:**
- Requires ViewState management
- Session-based

#### GovernMax
**Pattern:** Search form
**Example:** `https://fl-columbia-taxcollector.governmax.com/collectmax/collect30.asp`
**Download method:** Selenium (requires form)

#### MyFloridaCounty
**Pattern:** Search-based
**Example:** `https://www.myfloridacounty.com/ori/index.do`
**Download method:** Selenium

### 3.3 Download Method Selection

**Decision tree:**
```python
def choose_download_method(platform: str, use_selenium_override: bool) -> str:
    if use_selenium_override:
        return 'selenium'

    # Platforms requiring Selenium
    if platform in ['custom_gis', 'qpublic', 'tyler', 'governmax', 'myfloridacounty']:
        return 'selenium'

    # Simple HTTP for others
    return 'http'
```

---

## 4. File System Layout

### 4.1 Output Directory Structure

```
samples_collected/
├── collection_summary.json          # Overall statistics
│
├── fl_/
│   ├── columbia/
│   │   ├── metadata.json            # County metadata
│   │   ├── custom_gis/              # Platform subdirectory
│   │   │   ├── assessor_R00010-001.html
│   │   │   ├── assessor_R00010-001_meta.json
│   │   │   ├── assessor_R00010-001.png
│   │   │   ├── tax_R00010-001.html
│   │   │   ├── tax_R00010-001_meta.json
│   │   │   └── gis_142S1500061000.html
│   │   │       ...
│   │   │
│   │   └── (other platforms if multi-platform county)
│   │
│   ├── union/
│   │   ├── metadata.json
│   │   └── custom_gis/
│   │       └── ...
│   │
│   └── polk/
│       ├── metadata.json
│       └── custom/
│           └── ...
│
├── az_/
│   ├── coconino/
│   │   ├── metadata.json
│   │   └── tyler/
│   │       └── ...
│   │
│   └── pima/
│       └── ...
│
└── new_jersey/
    └── ...
```

### 4.2 File Naming Conventions

**HTML files:**
- Pattern: `{page_type}_{parcel_id_sanitized}.html`
- Sanitization: Replace `/` with `_`
- Examples:
  - `assessor_R00010-001.html`
  - `assessor_35-08-13-0000-3900-0200.html` (QPublic parcel)
  - `tax_222602-000000-013180.html`

**Screenshots (Selenium only):**
- Pattern: `{page_type}_{parcel_id_sanitized}.png`
- Examples:
  - `assessor_R00010-001.png`
  - `gis_142S1500061000.png`

**Metadata JSON:**
- Pattern: `{page_type}_{parcel_id_sanitized}_meta.json`
- Examples:
  - `assessor_R00010-001_meta.json`

---

## 5. Interfaces and APIs

### 5.1 PlatformURLGenerator

**Class:** `PlatformURLGenerator`
**File:** `samples/platform_sample_urls.py`

**Methods:**

#### `__init__()`
```python
def __init__(self):
    self.working_examples = self._load_working_examples()
```
Initializes generator with hardcoded working examples for 14 counties.

#### `get_sample_urls(state: str, county: str, num_samples: int = 3) -> List[SampleURL]`
**Purpose:** Generate sample URLs for a county
**Returns:** List of SampleURL objects (up to `num_samples * 3`)
**Behavior:**
1. Look up county in `working_examples`
2. Extract working URLs from `working_urls` dict
3. Generate additional URLs using `sample_parcels` and `_generate_url()`
4. Return combined list

#### `_generate_url(base_url: str, parcel_id: str, platform: str, page_type: str) -> Optional[str]`
**Purpose:** Generate platform-specific URL
**Returns:** Generated URL or None
**Platform logic:**
- Custom GIS: `{base_url}?pin={parcel_id}`
- QPublic/Beacon: Return base search URL (cannot generate direct parcel URLs)
- PropertyTax: `{base_url}?parcel={parcel_id}`
- GovernMax/Tyler: Return base URL (needs search)
- Generic: `{base_url}?parcel={parcel_id}`

#### `get_all_counties_with_examples() -> List[str]`
**Purpose:** List all counties with working examples
**Returns:** List of county keys (e.g., `['fl_columbia', 'fl_union', ...]`)

#### `print_county_info(state: str, county: str)`
**Purpose:** Debug output for county configuration
**Output:** Prints platform, URLs, sample parcels, working examples

### 5.2 SampleDownloader

**Class:** `SampleDownloader`
**File:** `samples/download_samples.py`

**Methods:**

#### `__init__(output_dir: str = "samples_downloaded")`
```python
def __init__(self, output_dir: str = "samples_downloaded"):
    self.output_dir = Path(output_dir)
    self.url_generator = PlatformURLGenerator()
    self.stats = {...}
    self.downloaded = set()  # Duplicate prevention
```

#### `download_url_simple(sample_url: SampleURL, output_path: Path) -> bool`
**Purpose:** Download using HTTP requests
**Returns:** True if successful
**Behavior:**
1. Send GET request with User-Agent headers
2. Check status code == 200
3. Save HTML with UTF-8 encoding
4. Save metadata JSON
5. Print progress
6. Return success/failure

**Error handling:**
- Catch all exceptions, print error, return False
- HTTP errors (status != 200) → print status, return False

#### `download_url_selenium(sample_url: SampleURL, output_path: Path) -> bool`
**Purpose:** Download using SeleniumBase
**Returns:** True if successful
**Behavior:**
1. Check if Selenium available
2. Launch virtual display (headless)
3. Open URL with `uc_open_with_reconnect()`
4. Wait 3 seconds for page load
5. Scroll to load dynamic content
6. Extract page source
7. Save HTML, screenshot, metadata
8. Return success/failure

**Error handling:**
- Selenium not available → print warning, return False
- Any exception → print error, return False

#### `download_county_samples(state: str, county: str, use_selenium: bool = False) -> Dict`
**Purpose:** Download all samples for a county
**Returns:** Result dict with status
**Behavior:**
1. Get sample URLs from `PlatformURLGenerator`
2. Create output directory: `{output_dir}/{state}/{county}`
3. Loop through URLs:
   - Skip if already downloaded (hash check)
   - Choose download method (Selenium or HTTP)
   - Download and update stats
   - Polite delay: 2-4 seconds
4. Return result summary

#### `run(counties: Optional[List[str]] = None, use_selenium: bool = False)`
**Purpose:** Main orchestrator
**Behavior:**
1. Get counties to process (filtered or all)
2. Loop through counties
3. Call `download_county_samples()` for each
4. Save progress after each county
5. Print final summary

#### `_print_summary(results: List[Dict])`
**Purpose:** Print statistics

#### `_save_summary(results: List[Dict])`
**Purpose:** Save `collection_summary.json`

### 5.3 SampleCollector

**Class:** `SampleCollector`
**File:** `samples/sample_collector.py`

**Methods:**

#### `__init__(sources_csv: str, output_dir: str = "samples_collected")`
```python
def __init__(self, sources_csv: str, output_dir: str = "samples_collected"):
    self.sources_csv = sources_csv
    self.output_dir = Path(output_dir)
    self.counties = self._load_counties()
    self.stats = {...}
```

#### `_load_counties() -> List[Dict]`
**Purpose:** Load county data from CSV
**Returns:** List of county dicts
**CSV columns:**
- `state` (e.g., "fl_")
- `county` (e.g., "columbia")
- `Assessor / Appraser`
- `Treasurer / Tax / Tax collector`
- `Mapping / Gis`
- `Recorder / County clerk`
- `AP`, `TX`, `R`, `RA` (indicators)
- `example` (sample parcel ID)

#### `identify_platform(county: Dict) -> str`
**Purpose:** Determine platform type
**Returns:** Platform string
**Logic:** See section 3.1

#### `get_sample_parcel_ids(county: Dict, platform: str) -> List[str]`
**Purpose:** Extract sample parcel IDs
**Returns:** List of parcel IDs
**Behavior:**
- Use `example` column from CSV if available
- Otherwise return empty list (needs manual entry)

#### `collect_samples_simple_http(county: Dict, platform: str, parcel_ids: List[str]) -> int`
**Purpose:** Collect using HTTP
**Returns:** Count of samples collected
**Behavior:**
1. Create output directory
2. Loop through parcel IDs
3. Generate URL: `{assessor_url}?parcel={parcel_id}` (simplified)
4. Download with requests
5. Save HTML
6. Polite delay

**Limitations:**
- Simplified URL generation (platform-agnostic)
- Not used in practice (SampleDownloader preferred)

#### `collect_samples_selenium(county: Dict, platform: str, parcel_ids: List[str]) -> int`
**Purpose:** Collect using Selenium
**Returns:** Count of samples collected
**Behavior:** Similar to `collect_samples_simple_http()` but with Selenium

#### `collect_county_samples(county: Dict, max_samples: int = 5) -> Dict`
**Purpose:** Collect samples for one county
**Returns:** Result dict
**Behavior:**
1. Identify platform
2. Get sample parcel IDs
3. If no parcels → save metadata, return 'no_parcel_ids' status
4. Choose collection method (Selenium for GIS/QPublic/Tyler)
5. Collect samples
6. Save county metadata
7. Return result

#### `run(states_filter: Optional[List[str]] = None, limit: Optional[int] = None)`
**Purpose:** Main entry point
**Behavior:**
1. Load counties
2. Filter by states if specified
3. Apply limit
4. Process each county
5. Update stats
6. Print and save summary

---

## 6. Error Handling and Edge Cases

### 6.1 HTTP Errors

**Scenario:** Website returns 404, 500, timeout
**Handling:**
```python
try:
    response = requests.get(url, timeout=30)
    if response.status_code == 200:
        # Save
    else:
        print(f"❌ HTTP {response.status_code}")
        return False
except requests.Timeout:
    print(f"❌ Timeout")
    return False
except Exception as e:
    print(f"❌ Error: {e}")
    return False
```

**Impact:**
- Failed download → increment `stats['failed']`
- Continue to next URL
- No retry logic (fail fast)

### 6.2 Selenium Errors

**Scenarios:**
- Selenium not installed → `SELENIUM_AVAILABLE = False`
- Browser crash
- Page load timeout
- Element not found

**Handling:**
```python
if not SELENIUM_AVAILABLE:
    print("⚠️ Selenium not available")
    return False

try:
    with Display(...):
        with SB(...) as sb:
            sb.uc_open_with_reconnect(url, reconnect_time=3)
            ...
except Exception as e:
    print(f"❌ Selenium error: {e}")
    return False
```

**Impact:**
- Skip Selenium downloads if unavailable
- Log error and continue

### 6.3 File System Errors

**Scenarios:**
- Permission denied
- Disk full
- Invalid path characters

**Handling:**
```python
output_path.mkdir(parents=True, exist_ok=True)

# Sanitize filenames
parcel_id_safe = parcel_id.replace('/', '_')
filename = f"{page_type}_{parcel_id_safe}.html"
```

**Impact:**
- Create parent directories automatically
- Sanitize parcel IDs for filenames
- UTF-8 encoding for HTML

### 6.4 Missing Data

**Scenario:** County has no example parcel IDs
**Current behavior:**
```python
if not sample_urls:
    print(f"⚠️ No sample URLs available for {county}")
    return {'status': 'no_urls'}
```

**Impact:**
- 20/20 counties failed in initial test run
- Need to populate `working_examples` dict with more counties
- Or implement parcel discovery mechanism

### 6.5 Duplicate Downloads

**Scenario:** Same URL downloaded multiple times
**Prevention:**
```python
self.downloaded = set()  # Track URL hashes

url_hash = hash(sample_url.url)
if url_hash in self.downloaded:
    print(f"⏭️ Already downloaded, skipping")
    continue

self.downloaded.add(url_hash)
```

**Impact:**
- Prevent duplicate downloads in single session
- Does not check disk (will re-download in new session)

### 6.6 Invalid Parcel IDs

**Scenario:** Parcel ID format mismatch
**Example:** QPublic needs `35-08-13-0000-3900-0200` but CSV has `010813-00003634-1100`

**Current handling:** None (URL generation fails silently)
**Improvement needed:** Validate parcel ID format per platform

### 6.7 Rate Limiting

**Scenario:** Website blocks rapid requests
**Prevention:**
```python
time.sleep(random.uniform(2, 4))  # Polite delay after each download
```

**User-Agent rotation:**
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...'
}
```

**Impact:**
- 2-4 second delay → ~15-30 downloads per minute
- Single User-Agent (no rotation yet)

### 6.8 CSV Parsing Errors

**Scenario:** CSV format change or encoding issue
**Handling:**
```python
with open(self.sources_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['state'] and row['county']:  # Skip empty rows
            counties.append(row)
```

**Impact:**
- Skip rows with missing state/county
- Assume UTF-8 encoding

---

## 7. Dependencies and Integration

### 7.1 External Dependencies

```
Python 3.13+
│
├── requests             # HTTP downloads
├── seleniumbase         # JavaScript-heavy pages
├── sbvirtualdisplay     # Headless Selenium
├── beautifulsoup4       # HTML parsing (not yet used)
└── csv (stdlib)         # CSV parsing
```

**Installation:**
```bash
pip install seleniumbase requests beautifulsoup4
```

### 7.2 Integration with Existing Scraper

**No integration** - Sample Collector is standalone:
- Different output directory (`samples_collected/` vs `downloaded_files/`)
- Different purpose (test data vs production)
- No Celery integration
- No database integration

**Potential future integration:**
- Reuse platform detection logic
- Reuse URL generation patterns
- Import parsers for validation

### 7.3 CSV Data Source

**File:** `flows/sdd-sample-collector/sources.csv`
**Columns:**
- `state` - State code (e.g., "fl_")
- `county` - County name (lowercase)
- `Assessor / Appraser` - Assessor URL
- `Treasurer / Tax / Tax collector` - Tax URL
- `Mapping / Gis` - GIS URL
- `Recorder / County clerk` - Recorder URL
- `AP` - Assessor platform indicator (QP/GIS/PT/...)
- `TX` - Tax platform indicator
- `R` - Recorder platform indicator (MF/...)
- `RA` - Real estate auction indicator
- `example` - Example parcel ID

**Sample row:**
```csv
state,county,Assessor / Appraser,Treasurer / Tax / Tax collector,...,example
fl_,columbia,http://columbia.floridapa.com/gis/,http://fl-columbia-taxcollector.governmax.com/collectmax/collect30.asp,...,142S1500061000
```

---

## 8. Performance Characteristics

### 8.1 Download Speed

**HTTP downloads:**
- Request time: ~1-3 seconds
- Polite delay: 2-4 seconds
- **Total:** 3-7 seconds per sample

**Selenium downloads:**
- Browser startup: ~2 seconds
- Page load: ~3 seconds
- Scrolling: ~2 seconds
- Polite delay: 2-4 seconds
- **Total:** 9-11 seconds per sample

**Batch processing:**
- 3 samples/county × 5 seconds/sample = 15 seconds/county
- 130 counties × 15 seconds = ~32 minutes (HTTP)
- 130 counties × 10 seconds = ~22 minutes (Selenium, best case)

### 8.2 Resource Usage

**Memory:**
- HTTP: < 100MB
- Selenium: ~500MB per browser instance
- Total: < 1GB

**Disk:**
- HTML: ~50KB - 500KB per file
- Screenshot: ~100KB - 2MB per file
- 500 samples × 300KB avg = ~150MB

**Network:**
- Bandwidth: ~1-5 Mbps (polite scraping)
- No concurrent downloads (sequential)

### 8.3 Scalability

**Current limitations:**
- Single-threaded
- No parallelization
- No retry logic
- No resume capability

**Potential improvements:**
- Parallel downloads (multi-threading)
- Checkpoint/resume support
- Exponential backoff retry

---

## 9. Security Considerations

### 9.1 Data Privacy

**PII in HTML:**
- Property records may contain owner names, addresses
- Not a concern (public records)

**Credentials:**
- No authentication required for public records
- No credentials stored

### 9.2 Rate Limiting and Blocking

**Risk:** IP blocking from aggressive scraping
**Mitigation:**
- Polite delays (2-4 seconds)
- User-Agent headers
- Sequential downloads (not parallel)

**Future improvements:**
- Proxy rotation
- User-Agent rotation
- Respect robots.txt

### 9.3 Code Security

**Risks:**
- Path traversal (parcel IDs in filenames)
- Command injection (URLs in Selenium)

**Mitigations:**
```python
# Path sanitization
parcel_id_safe = parcel_id.replace('/', '_')

# URL validation
if not url.startswith(('http://', 'https://')):
    return None
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Not implemented yet**

**Proposed tests:**
- `test_platform_identification()` - Test all platform patterns
- `test_url_generation()` - Test URL generation per platform
- `test_parcel_id_sanitization()` - Test filename sanitization
- `test_sample_url_dataclass()` - Test data model validation

### 10.2 Integration Tests

**Proposed:**
- `test_download_http()` - Test HTTP download with mock server
- `test_download_selenium()` - Test Selenium download (slow)
- `test_csv_loading()` - Test CSV parsing

### 10.3 Manual Testing

**Current approach:**
```bash
# Test single county
python samples/download_samples.py --counties fl_columbia

# Test multiple counties
python samples/download_samples.py --counties fl_columbia fl_union fl_polk

# List available counties
python samples/download_samples.py --list

# Use Selenium for all
python samples/download_samples.py --counties fl_columbia --selenium
```

**Test coverage:**
- ✅ Tested: FL Columbia, Union, Polk, Dixie, Gadsden
- ✅ Tested: AZ Coconino
- ⏳ Not tested: 124 other counties (no parcel IDs yet)

---

## 11. Deployment and Operations

### 11.1 Deployment

**Method:** Manual execution (no deployment)

**Requirements:**
- Python 3.13+ environment
- Dependencies installed
- `sources.csv` file present
- Sufficient disk space (~500MB)

**Installation:**
```bash
cd /Users/anton/proj/TAXLIEN.online/taxlien-scraper-python
pip install -r requirements.txt
python samples/download_samples.py --list
```

### 11.2 Configuration

**No config file** - Hardcoded in code

**Configuration points:**
- Output directory: `--output` arg (default: `samples_downloaded`)
- CSV path: `--csv` arg in `sample_collector.py`
- Polite delay: `time.sleep(random.uniform(2, 4))` (hardcoded)
- Timeout: `requests.get(..., timeout=30)` (hardcoded)

**Improvement needed:** Config file for:
- Delays
- Timeouts
- User-Agents
- Platform patterns

### 11.3 Monitoring

**Current:** Print statements only

**Metrics available:**
- `stats['total_downloads']`
- `stats['successful']` / `stats['failed']`
- `stats['by_platform']` / `stats['by_state']`

**Improvement needed:**
- Structured logging
- Progress bar (tqdm)
- Error rate alerts

### 11.4 Maintenance

**Data updates:**
- Update `working_examples` dict when adding new counties
- Update CSV when sources change

**Code maintenance:**
- Add new platform patterns to `identify_platform()`
- Add new URL generation logic to `_generate_url()`

---

## 12. Open Questions and Risks

### 12.1 Open Questions

1. **Parcel ID Discovery:** How to automatically discover valid parcel IDs for counties without examples?
   - Option A: Scrape search pages
   - Option B: Manual entry from county websites
   - Option C: Import from existing scraper data

2. **Platform Variations:** How to handle platform sub-types?
   - Example: QPublic has variations (qpublic.net vs qpublic.schneidercorp.com vs beacon.schneidercorp.com)
   - Need more granular platform classification?

3. **URL Validity:** How long are generated URLs valid?
   - Some platforms use session IDs or expiring tokens
   - Need to re-generate URLs periodically?

4. **Coverage Goal:** What is acceptable coverage?
   - Target: 50+ counties with samples (current: 14)
   - Or: 300+ HTML samples total
   - Or: All 6 major platforms covered

### 12.2 Risks

**Risk 1:** Low coverage due to missing parcel IDs
**Impact:** HIGH - 20/20 counties failed initial run (no parcel IDs)
**Mitigation:** Populate `working_examples` with more counties (14 done, 116 to go)

**Risk 2:** Platform blocking
**Impact:** MEDIUM - Could get IP blocked
**Mitigation:** Polite delays, single-threaded, User-Agent headers

**Risk 3:** URL format changes
**Impact:** MEDIUM - Generated URLs may break
**Mitigation:** Use working examples from CSV as ground truth

**Risk 4:** Selenium reliability
**Impact:** MEDIUM - Selenium can be flaky (timeouts, crashes)
**Mitigation:** Retry logic, fallback to HTTP where possible

**Risk 5:** Disk space
**Impact:** LOW - 500 samples ~150MB, well under limits
**Mitigation:** None needed

---

## 13. Implementation Notes

### 13.1 Current State (as of 2026-01-01)

**Completed:**
- ✅ Three scripts implemented:
  - `samples/platform_sample_urls.py` (372 lines)
  - `samples/download_samples.py` (346 lines)
  - `samples/sample_collector.py` (392 lines)
- ✅ 14 counties with working examples
- ✅ CLI interface with argparse
- ✅ Statistics tracking
- ✅ Metadata JSON generation

**Partially complete:**
- ⚠️ Platform identification (basic patterns only)
- ⚠️ URL generation (works for Custom GIS, partial for others)
- ⚠️ Error handling (basic try/catch only)

**Not started:**
- ❌ Parcel ID discovery
- ❌ Config file
- ❌ Retry logic
- ❌ Resume capability
- ❌ Unit tests

### 13.2 Gaps Analysis

**Gap 1:** Missing parcel IDs for 116 counties
**Solution:** Manual data entry or scraping discovery

**Gap 2:** Platform URL generation incomplete
**Current:** Only Custom GIS, QPublic, PropertyTax
**Missing:** Tyler, GovernMax, Beacon variations, MyFloridaCounty

**Gap 3:** No validation of downloaded HTML
**Solution:** Add HTML parsing to check if page loaded correctly

**Gap 4:** Duplicate detection only in-memory
**Solution:** Check disk before downloading

**Gap 5:** No progress persistence
**Solution:** Save checkpoint after each county

---

## 14. Next Steps (PLAN Phase)

The following will be detailed in the PLAN phase:

1. **Complete working examples** for 30-50 counties (target platforms)
2. **Implement missing platform URL generators** (Tyler, GovernMax, etc.)
3. **Add HTML validation** to detect empty/error pages
4. **Add disk-based duplicate detection**
5. **Run full collection** on 50+ counties
6. **Document results** and coverage metrics

**Estimated complexity:**
- Gap filling: 2-3 hours
- Full collection run: 1-2 hours
- Documentation: 1 hour

---

## ✅ Specifications Approval Checklist

Before moving to PLAN phase:

- [x] System architecture documented
- [x] Data models defined with schemas
- [x] Platform-specific behaviors specified
- [x] File system layout documented
- [x] Interfaces and APIs detailed
- [x] Error handling and edge cases identified
- [x] Dependencies documented
- [x] Performance characteristics analyzed
- [x] Security considerations addressed
- [x] Testing strategy outlined
- [x] Open questions and risks identified
- [x] Implementation gaps analyzed
- [ ] **User approval:** Specifications reviewed and approved

---

**Status:** READY FOR REVIEW
**Next Phase:** PLAN
**Blocker:** Awaiting user approval of specifications
