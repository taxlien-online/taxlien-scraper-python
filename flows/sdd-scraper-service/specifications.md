# Specifications: Multi-Platform Scraper Service

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-01-01
> Requirements: [README.md](README.md), [01-platform-support.md](01-platform-support.md)

## Overview

This specification defines the extension of the existing Celery-based scraper architecture to support 15+ property tax platforms. The immediate focus is implementing CustomGISParser for JavaScript-heavy county portals (Union County FL, Columbia County FL with 322 sample HTML files).

**Key Design Decision:** The codebase uses a **task-based pattern** (Celery tasks) rather than class inheritance. Each platform implements standalone functions following consistent naming conventions, orchestrated via Celery chains.

## Affected Systems

| System | Impact | Notes |
|--------|--------|-------|
| `platforms/` directory | Create | New platform subdirectories for each parser |
| `platforms/custom_gis/` | Create | Priority 1: CustomGISParser implementation |
| `platforms/custom_gis/config.py` | Create | Load configuration from .env file |
| `tasks.py` | Modify | Add new platform chain orchestration tasks |
| `functions.py` | Modify | Update `save_json()` to write to pending/ + manifest.jsonl |
| `celery_app.py` | Modify | Add per-platform rate limiting from .env |
| `.env` | Create | Configuration file for all platform settings |
| `requirements.txt` | Modify | Add `python-dotenv` dependency |
| `./storage/` structure | Modify | Add `pending/`, `processing/`, `processed/` subdirs |
| Database integration | Future | Handled by Airflow pipeline (separate service) |

## Architecture

### Current State: Task-Based Pattern

```
User → Celery Task Chain → Platform Functions → Storage
                ↓
        Redis Broker (localhost:6379)
                ↓
        Workers (async execution)
```

**No BaseParser Class:** Each platform is self-contained in `platforms/{platform}/{platform}_functions.py`

### Standard Platform Implementation Pattern

Every platform implements 3-4 Celery tasks:

```python
# 1. Get county/location URLs
@app.task
def {platform}_scrape_counties_urls_task(base_url: str) -> dict:
    """Returns: {county_name: county_url, ...}"""

# 2. Get all parcel URLs for counties
@app.task
def {platform}_get_all_parcels_urls_task(counties_urls: dict) -> list:
    """Returns: [parcel_url1, parcel_url2, ...]"""

# 3. Parse single HTML page
@app.task
def {platform}_parse_single_html_task(html: str) -> dict:
    """Returns: standardized property data dict"""

# 4. (Optional) Main orchestration chain
@app.task
def {platform}_main_chain():
    """Orchestrates workflow: counties → parcels → scrape → parse → save"""
```

### Task Orchestration with Celery

**Sequential Processing:**
```python
chain(
    scrape_url_task.s(url),
    save_html_task.s(platform='custom_gis', name=name),
    custom_gis_parse_html_task.s(),
    import_to_db_task.s()
)()
```

**Parallel Processing:**
```python
group(
    custom_gis_single_url_chain.s(url)
    for url in parcel_urls
)()
```

## Data Flow

```
1. Base URL(s)
   ↓
2. {platform}_scrape_counties_urls_task
   → Returns: {county1: url1, county2: url2, ...}
   ↓
3. {platform}_get_all_parcels_urls_task
   → Returns: [parcel_url1, parcel_url2, ...]
   ↓
4. save_json(parcel_urls, platform, name)
   ↓
5. FOR EACH parcel_url IN PARALLEL:
   ├─ scrape_url_task(url) → HTML string
   ├─ save_html_task(html, platform, name) → filepath
   ├─ {platform}_parse_html_task(html) → data dict
   └─ import_to_db_task(data) → CSV/JSON (MongoDB/PostgreSQL future)
```

## Interfaces

### Task Signatures (Function Contracts)

```python
# Required for all platforms
def {platform}_scrape_counties_urls_task(base_url: str) -> dict:
    """
    Get list of county/location URLs for the platform.

    Args:
        base_url: Starting URL for the platform

    Returns:
        dict: {county_name: county_url, ...}
        Example: {'union_fl': 'https://unionpa.com/...', ...}
    """

def {platform}_get_all_parcels_urls_task(counties_urls: dict) -> list:
    """
    Extract all parcel URLs from given county URLs.

    Args:
        counties_urls: Dict from scrape_counties_urls_task

    Returns:
        list: [parcel_url1, parcel_url2, ...]
        Example: ['https://unionpa.com/parcel/12345', ...]
    """

def {platform}_parse_single_html_task(html: str) -> dict:
    """
    Parse HTML page into standardized property data.

    Args:
        html: Raw HTML content from scrape_url_task

    Returns:
        dict: Standardized property data (see Data Models below)
    """

# Optional orchestration
def {platform}_main_chain():
    """Execute full scraping workflow for platform."""

def {platform}_single_url_chain(url: str):
    """Execute scrape → save → parse → import for single URL."""
```

### Shared Utility Functions (functions.py)

```python
# Already implemented - use as-is
def scrape_single_url(url: str, headless: bool = False) -> str:
    """Opens URL with Selenium, bypasses Cloudflare, returns HTML"""

def scraper_pass_challenge(sb: SB):
    """Handles Cloudflare challenges"""

def scraper_pass_modal(sb: SB):
    """Dismisses modal dialogs"""

def make_sites_visited_history(sb: SB):
    """Visits sites to appear as real user"""

def save_html(html: str, platform: str, name: str) -> str:
    """Saves HTML to ./storage/{platform}/{name}.html"""

def save_json(data: dict, platform: str, name: str) -> None:
    """Saves JSON to ./storage/{platform}/{name}.json"""

def save_csv(data: dict, platform: str, name: str) -> None:
    """Appends data as CSV row"""

def generate_name(platform: str, uid: str) -> str:
    """Creates filename: {platform}_{date}_{uid}"""
```

## Data Models

### Standardized Property Data Dictionary

All `{platform}_parse_single_html_task` functions MUST return a dict with these keys:

```python
{
    # Core identifiers (REQUIRED)
    'parcel_id': str,              # Unique parcel identifier
    'property_address': str,       # Physical address
    'legal_description': str,      # Legal property description

    # Owner information
    'owner': str,                  # Owner name(s)
    'mailing_address': str,        # Mailing address

    # Property details
    'property_type': str,          # Residential, Commercial, etc.
    'bedrooms': str,               # Number of bedrooms
    'bathrooms': str,              # Number of bathrooms
    'building_sqft': str,          # Building square footage
    'lot_size': str,               # Lot size (acres or sqft)
    'year_built': str,             # Year constructed
    'zoning': str,                 # Zoning classification

    # Financial data
    'assessed_value': str,         # Total assessed value
    'land_value': str,             # Land value
    'improvement_value': str,      # Improvement/building value
    'market_value': str,           # Market value
    'total_due_amount': str,       # Total taxes due
    'tax_amount': str,             # Annual tax amount

    # Tax information
    'tax_year': str,               # Tax year
    'tax_status': str,             # Current, Delinquent, etc.
    'exemptions': str,             # Tax exemptions (comma-separated)
    'has_delinquency': bool,       # Boolean delinquency flag

    # Sales history
    'last_sale_date': str,         # Last sale date (ISO format)
    'last_sale_price': str,        # Last sale price
    'deed_book': str,              # Deed book number
    'deed_page': str,              # Deed page number

    # Media and documents
    'image_urls': list,            # List of property image URLs
    'document_urls': list,         # List of document URLs
    'map_url': str,                # GIS/map URL

    # Metadata (REQUIRED)
    'parse_error': str,            # Error message if parsing failed (else None)
    'scraped_at': str,             # ISO format datetime
    'source': str                  # Platform name (e.g., 'custom_gis')
}
```

**Data Handling Rules:**
- Use `None` or empty string `""` for missing fields (don't omit keys)
- Numeric values stored as strings (conversion happens at DB layer)
- Dates in ISO format: `YYYY-MM-DD`
- Lists as Python list objects (converted to JSON arrays when saved)
- Include `parse_error` key with error message if parsing fails

## Behavior Specifications

### Happy Path: CustomGISParser Flow

1. **User initiates scraping**
   - Calls `custom_gis_main_chain.delay()` via Celery
   - Or manually triggers: `custom_gis_single_url_chain.delay(url)`

2. **System discovers county URLs**
   - `custom_gis_scrape_counties_urls_task(base_url)` executes
   - Returns: `{'union_fl': 'https://unionpa.com/..., 'columbia_fl': 'https://columbiapa.com/...'}`

3. **System extracts parcel URLs**
   - `custom_gis_get_all_parcels_urls_task(counties_urls)` executes
   - Returns: `['https://unionpa.com/parcel/12345', ...]` (322+ URLs for samples)

4. **System saves URL list**
   - `save_json(parcel_urls, 'custom_gis', generate_name(...))`

5. **System processes parcels in parallel**
   - For each URL, execute chain:
     - `scrape_url_task(url)` → HTML
     - `save_html_task(html, 'custom_gis', name)` → filepath
     - `custom_gis_parse_html_task(html)` → data dict
     - `import_to_db_task(data)` → CSV/JSON (DB future)

6. **System completes successfully**
   - All 322 parcels parsed
   - HTML saved to `./storage/custom_gis/{date}_{parcel_id}.html`
   - Data saved to `./storage/custom_gis/{date}_{parcel_id}.json`
   - CSV appended to `./storage/custom_gis/custom_gis.csv`

### Edge Cases

| Case | Trigger | Expected Behavior |
|------|---------|-------------------|
| Cloudflare challenge | Bot detection on page load | `scraper_pass_challenge()` waits for page load, retries |
| Modal dialogs | "Agree to Terms" popup | `scraper_pass_modal()` detects and dismisses |
| Missing data fields | Element not found in HTML | Return `None` or `""` for field, continue parsing |
| JavaScript timeout | Page takes >30s to render | Retry with longer timeout, log error if fails |
| Invalid parcel URL | 404 or redirect | Save HTML with error, set `parse_error` in data dict |
| Rate limiting | Server blocks requests | Celery rate limit: `5/m`, retry with exponential backoff |
| Incomplete HTML | Page partially loaded | Parse available fields, note missing fields in `parse_error` |

### Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| `ElementNotFoundError` | Selector doesn't match HTML | Try fallback selectors, return `None` for field |
| `TimeoutException` | Page load timeout | Retry 3x with increasing timeout (10s, 20s, 30s) |
| `WebDriverException` | Browser crash | Restart browser session, retry task |
| `ParsingException` | BeautifulSoup parsing fails | Set `parse_error` field, save raw HTML for debugging |
| `NetworkError` | Connection lost | Retry task (Celery auto-retry with exponential backoff) |
| `ValueError` | Invalid data format | Log warning, use default value or `None` |

**Error Handling Pattern:**
```python
@app.task(bind=True, max_retries=3)
def custom_gis_parse_single_html_task(self, html: str) -> dict:
    data = initialize_empty_data_dict()
    try:
        # Parsing logic
        doc = BeautifulSoup(html, 'html.parser')
        data['parcel_id'] = doc.find(id=re.compile('parcel', re.I)).text
        # ... more parsing
    except Exception as e:
        print(f"Error parsing custom_gis HTML: {e}")
        data['parse_error'] = str(e)
        # Optionally retry
        # raise self.retry(exc=e, countdown=60)
    finally:
        data['scraped_at'] = datetime.now().isoformat()
        data['source'] = 'custom_gis'
    return data
```

## CustomGISParser - Platform-Specific Specifications

### Target Platforms

**Priority 1 (Week 1-2):**
1. Union County FL - 214 parcels
   - URL pattern: `https://unionpa.com/...`
   - Sample files: `samples/UnionPA.com/*.html`

2. Columbia County FL - 108 parcels
   - URL pattern: `https://columbiapa.com/...`
   - Sample files: `samples/ColumbiaPA.com/*.html`

**Total Sample Data:** 322 HTML files in `/samples/` directory

### Technical Challenges

**JavaScript-Heavy Pages:**
- Custom GIS systems use dynamic content loading
- Element IDs: `gisSideMenu_3_Details`, `gisSideMenu_*`
- Requires Selenium with JavaScript execution
- Page load times: 5-15 seconds typical

**Non-Standard Formats:**
- Custom domain names (no uniform vendor URL pattern)
- Parcel IDs vary by county (no standard format)
- Element selectors differ between counties

### Implementation Strategy

**Phase 1: Sample-Based Development**
1. Use 322 existing HTML files for parser development
2. No scraping required initially (work offline)
3. Extract common patterns across samples
4. Build robust selector fallback logic

**Phase 2: Live Scraping**
1. Implement URL discovery (county portals → parcel search)
2. Test with SeleniumBase + JavaScript rendering
3. Add screenshot capture for debugging
4. Verify parse success rate ≥95%

**Phase 3: Production Deployment**
1. Deploy Celery workers with rate limiting
2. Monitor parse success metrics
3. Iterate on selector patterns based on failures

### File Structure

```
platforms/
└── custom_gis/
    ├── __init__.py                     # Empty or imports
    ├── custom_gis_functions.py         # Main implementation
    ├── configs.py                      # County-specific configs (optional)
    └── selectors.py                    # CSS/XPath selector patterns (optional)
```

### Configuration Schema

```python
# Optional: platforms/custom_gis/configs.py
CUSTOM_GIS_CONFIGS = {
    'union_fl': {
        'base_url': 'https://unionpa.com',
        'county': 'union_fl',
        'state': 'FL',
        'sample_dir': 'samples/UnionPA.com',
        'num_samples': 214
    },
    'columbia_fl': {
        'base_url': 'https://columbiapa.com',
        'county': 'columbia_fl',
        'state': 'FL',
        'sample_dir': 'samples/ColumbiaPA.com',
        'num_samples': 108
    }
}
```

## Dependencies

### Existing (No Changes Required)

```txt
celery==5.4.0
redis==5.2.1
seleniumbase==4.34.7
selenium==4.28.1
sbvirtualdisplay==1.4.0
beautifulsoup4==4.13.3
lxml==5.3.0
```

### New Required Dependencies

```txt
python-dotenv==1.0.0  # Load configuration from .env file
flower==2.0.1         # Celery monitoring web UI (optional but recommended)
```

### Future Additions (Not for Initial Implementation)

```txt
# For advanced JavaScript execution (if needed later)
# playwright==1.49.0  # Alternative to Selenium for complex JS

# For image/PDF extraction (if parsing images in future)
# pytesseract==0.3.13  # OCR for image-based data
# pdf2image==1.17.0    # Convert PDF documents to images

# For proxy rotation (when scaling)
# requests[socks]==2.31.0  # Proxy support
```

## Integration Points

### Internal Systems

| System | Integration | Notes |
|--------|-------------|-------|
| `tasks.py` | Add `custom_gis_main_chain`, `custom_gis_single_url_chain` | Follow existing pattern |
| `celery_app.py` | Auto-discover new tasks | No changes needed (auto-discovery enabled) |
| `functions.py` | Use existing utilities | `scrape_single_url`, `save_*` functions |
| Redis | Task broker | Existing localhost:6379 connection |

### External Systems

| System | Purpose | Notes |
|--------|---------|-------|
| Union County FL Portal | Scrape parcel data | Custom GIS, JavaScript-heavy |
| Columbia County FL Portal | Scrape parcel data | Custom GIS, JavaScript-heavy |
| Cloudflare | Bot protection | Handled by `scraper_pass_challenge()` |

## Testing Strategy

### Unit Tests

**Phase 1: Sample-Based Testing**
- [ ] `test_custom_gis_parse_union_sample()` - Parse Union County sample HTML
- [ ] `test_custom_gis_parse_columbia_sample()` - Parse Columbia County sample HTML
- [ ] `test_custom_gis_parse_all_322_samples()` - Batch parse all samples
- [ ] `test_custom_gis_parse_success_rate()` - Verify ≥95% parse success
- [ ] `test_custom_gis_data_completeness()` - Verify ≥90% field coverage

**Phase 2: Live Scraping Tests**
- [ ] `test_custom_gis_scrape_single_url()` - Scrape live URL with Selenium
- [ ] `test_custom_gis_javascript_rendering()` - Verify JS content loads
- [ ] `test_custom_gis_cloudflare_bypass()` - Test challenge handling

### Integration Tests

- [ ] `test_custom_gis_main_chain()` - Full workflow: counties → parcels → parse
- [ ] `test_custom_gis_celery_task()` - Verify async execution works
- [ ] `test_custom_gis_save_outputs()` - Verify HTML/JSON/CSV saving
- [ ] `test_custom_gis_error_recovery()` - Test retry logic on failures

### Manual Verification

- [ ] Run `custom_gis_main_chain()` on 10 random parcels
- [ ] Inspect saved HTML files for completeness
- [ ] Verify JSON data matches HTML content
- [ ] Check CSV output for proper formatting
- [ ] Monitor Celery worker logs for errors

### Success Criteria

**Parse Quality:**
- ✅ 95%+ parse success rate (317/322 samples)
- ✅ 90%+ field coverage (81/90 attributes extracted)
- ✅ <2% error rate (≤6 failed parses)

**Performance:**
- ✅ <10 sec average parse time (including JS rendering)
- ✅ No browser crashes during 322-sample batch
- ✅ No Celery worker failures

## Migration / Rollout

### Phase 1: Development (Week 1)
1. Implement `custom_gis_functions.py` using 322 samples
2. Test offline parsing (no live scraping)
3. Achieve 95%+ parse success on samples
4. Code review + approval

### Phase 2: Live Testing (Week 2)
1. Implement URL discovery (scrape county portals)
2. Test live scraping on 10 parcels per county
3. Compare live results to sample results
4. Fix any discrepancies

### Phase 3: Production (Week 3)
1. Deploy to Celery workers
2. Scrape Union County (214 parcels)
3. Scrape Columbia County (108 parcels)
4. Verify all data saved to CSV/JSON
5. Monitor error rates

### Phase 4: Expansion (Month 2+)
1. Add PropertyMax parser (100+ counties)
2. Add CivicSource parser (500+ counties)
3. Continue adding platforms per [01-platform-support.md](01-platform-support.md) priority list

## Scraper → Parser Data Handoff Strategy

Based on the [sdd-system-architecture](../sdd-system-architecture/) requirements, the scraper service outputs data that will be consumed by a separate Data Processing Pipeline (Apache Airflow).

### Architecture Overview

```
┌──────────────────┐
│ Scraper Service  │
│ (This Service)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  File-Based Storage (Intermediate)        │
├──────────────────────────────────────────┤
│  • HTML: ./storage/{platform}/{name}.html │
│  • JSON: ./storage/{platform}/{name}.json │
│  • CSV:  ./storage/{platform}/{name}.csv  │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│ Airflow DAG      │
│ (Data Pipeline)  │
├──────────────────┤
│ 1. Extract       │ ← Read from ./storage/
│ 2. Transform     │ ← Geocode, enrich, dedupe
│ 3. Load          │ ← Write to PostgreSQL + ClickHouse
│ 4. Index         │ ← Update Elasticsearch
└──────────────────┘
```

### Implementation Options

**Option 1: File-Based Queue (Recommended for MVP)**
- Scraper writes to `./storage/{platform}/pending/`
- Airflow watches directory for new files (File Sensor)
- After processing, moves to `./storage/{platform}/processed/`
- Simple, works with current architecture, no new dependencies

**Option 2: Event-Driven (Future)**
- Scraper publishes `scrape.completed` event to Kafka/EventBridge
- Airflow DAG triggered by event (Airflow 2.0+ event-driven triggers)
- Event payload includes file path or S3 key
- More scalable, but requires message bus infrastructure

**Option 3: Database Queue (Alternative)**
- Scraper writes to `scraping_jobs` table in PostgreSQL
- Fields: `id`, `platform`, `parcel_id`, `status`, `html_path`, `json_path`, `created_at`, `processed_at`
- Airflow DAG polls for `status='pending'` rows
- Updates `status='processing'` → `status='completed'`
- More robust than files, but adds DB complexity

### Recommended Approach: File-Based with Metadata

**Directory Structure:**
```
./storage/
├── custom_gis/
│   ├── pending/           # New scrapes
│   │   ├── 2026-01-01_12345.html
│   │   ├── 2026-01-01_12345.json
│   │   └── manifest.jsonl  # One-line JSON per file
│   ├── processing/        # Being parsed
│   └── processed/         # Completed
│       ├── 2026-01-01_12345.html
│       └── 2026-01-01_12345.json
└── qpublic/
    ├── pending/
    ├── processing/
    └── processed/
```

**Manifest Format (manifest.jsonl):**
```jsonl
{"file": "2026-01-01_12345.json", "platform": "custom_gis", "county": "union_fl", "parcel_id": "12345", "scraped_at": "2026-01-01T10:30:00Z", "status": "pending"}
{"file": "2026-01-01_67890.json", "platform": "custom_gis", "county": "columbia_fl", "parcel_id": "67890", "scraped_at": "2026-01-01T10:31:00Z", "status": "pending"}
```

**Benefits:**
- ✅ No external dependencies (Kafka, etc.)
- ✅ Works with existing file storage
- ✅ Airflow can read manifest line-by-line for batch processing
- ✅ Easy debugging (just look at files)
- ✅ Can migrate to event-driven later without code changes

### Updated `save_json()` Function Spec

Modify `functions.py` to append to manifest file:

```python
def save_json(data: dict, platform: str, name: str) -> None:
    """
    Saves JSON to ./storage/{platform}/pending/{name}.json
    Appends metadata to manifest.jsonl for pipeline consumption
    """
    pending_dir = f"./storage/{platform}/pending"
    os.makedirs(pending_dir, exist_ok=True)

    # Save JSON
    filepath = f"{pending_dir}/{name}.json"
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

    # Append to manifest
    manifest = {
        "file": f"{name}.json",
        "platform": platform,
        "county": data.get('county', 'unknown'),
        "parcel_id": data.get('parcel_id', 'unknown'),
        "scraped_at": data.get('scraped_at', datetime.now().isoformat()),
        "status": "pending"
    }

    manifest_path = f"{pending_dir}/manifest.jsonl"
    with open(manifest_path, 'a') as f:
        f.write(json.dumps(manifest) + '\n')
```

### Airflow DAG (Example for Reference)

```python
# This will be in a separate repo/service, not in scraper codebase
from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.python import PythonOperator

def process_scraped_files():
    """Read manifest, parse files, load to DB"""
    manifest_path = "/path/to/storage/custom_gis/pending/manifest.jsonl"

    with open(manifest_path, 'r') as f:
        for line in f:
            record = json.loads(line)
            if record['status'] == 'pending':
                # Read JSON file
                data = json.load(open(f"/path/to/storage/{record['platform']}/pending/{record['file']}"))

                # Transform & load to PostgreSQL
                load_to_postgres(data)

                # Move to processed
                shutil.move(
                    f"/path/to/storage/{record['platform']}/pending/{record['file']}",
                    f"/path/to/storage/{record['platform']}/processed/{record['file']}"
                )

dag = DAG('custom_gis_etl', schedule_interval='@hourly')

wait_for_files = FileSensor(
    task_id='wait_for_manifest',
    filepath='/path/to/storage/custom_gis/pending/manifest.jsonl',
    dag=dag
)

process = PythonOperator(
    task_id='process_files',
    python_callable=process_scraped_files,
    dag=dag
)

wait_for_files >> process
```

### Configuration (.env Settings)

Add to `.env` file:

```bash
# Scraper Configuration
SCRAPER_STORAGE_PATH=./storage
SCRAPER_RATE_LIMIT_QPUBLIC=5/m
SCRAPER_RATE_LIMIT_BEACON=5/m
SCRAPER_RATE_LIMIT_CUSTOM_GIS=3/m  # Slower for custom GIS
SCRAPER_HEADLESS=false
SCRAPER_ENABLE_MANIFEST=true

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKER_CONCURRENCY=4  # Number of parallel worker processes
CELERY_WORKER_PREFETCH_MULTIPLIER=1  # How many tasks to prefetch per worker

# Platform-specific
CUSTOM_GIS_UNION_FL_URL=https://unionpa.com
CUSTOM_GIS_COLUMBIA_FL_URL=https://columbiapa.com

# Future: Proxy rotation (when needed)
# PROXY_ROTATION_ENABLED=false
# PROXY_PROVIDER=brightdata
# PROXY_API_KEY=xxx
```

### Running Multiple Instances (Multi-County Parallel Scraping)

**Architecture for Parallel Scraping:**

Celery natively supports running multiple workers in parallel. Each worker can process different counties simultaneously using Celery's distributed task queue.

**Option 1: Single Worker with Concurrency (Recommended)**

Run one Celery worker with multiple concurrent processes:

```bash
# Start Celery worker with 8 concurrent processes
celery -A celery_app worker --concurrency=8 --loglevel=info

# This allows 8 counties to be scraped simultaneously
# Celery automatically distributes tasks across processes
```

**Option 2: Multiple Named Workers (County-Specific)**

Run separate Celery workers for different platforms/counties:

```bash
# Terminal 1: Worker for QPublic platform
celery -A celery_app worker -Q qpublic_queue --concurrency=4 --loglevel=info -n qpublic_worker@%h

# Terminal 2: Worker for Custom GIS platform
celery -A celery_app worker -Q custom_gis_queue --concurrency=2 --loglevel=info -n custom_gis_worker@%h

# Terminal 3: Worker for Beacon platform
celery -A celery_app worker -Q beacon_queue --concurrency=4 --loglevel=info -n beacon_worker@%h
```

**Option 3: Geographic Distribution (Different Machines)**

For scaling across multiple computers:

```bash
# Machine 1 (scrapes Union County FL)
WORKER_NAME=union_fl celery -A celery_app worker --concurrency=2 -n union_worker@machine1

# Machine 2 (scrapes Columbia County FL)
WORKER_NAME=columbia_fl celery -A celery_app worker --concurrency=2 -n columbia_worker@machine2

# Both connect to same Redis broker (central coordination)
```

### Updated Celery Configuration (celery_app.py)

Add task routing to send different platforms to different queues:

```python
from celery import Celery
from kombu import Queue
import os
from dotenv import load_dotenv

load_dotenv()

app = Celery(
    'taxlien_scraper',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Define queues for different platforms
app.conf.task_queues = (
    Queue('default'),
    Queue('qpublic_queue'),
    Queue('beacon_queue'),
    Queue('custom_gis_queue'),
    Queue('tyler_queue'),
    Queue('bid4assets_queue'),
)

# Route tasks to appropriate queues based on name
app.conf.task_routes = {
    'platforms.qpublic.*': {'queue': 'qpublic_queue'},
    'platforms.beacon.*': {'queue': 'beacon_queue'},
    'platforms.custom_gis.*': {'queue': 'custom_gis_queue'},
    'platforms.tyler_technologies.*': {'queue': 'tyler_queue'},
    'platforms.bid4assets.*': {'queue': 'bid4assets_queue'},
}

# Rate limiting per platform (from .env)
app.conf.task_annotations = {
    'platforms.qpublic.*': {'rate_limit': os.getenv('SCRAPER_RATE_LIMIT_QPUBLIC', '5/m')},
    'platforms.beacon.*': {'rate_limit': os.getenv('SCRAPER_RATE_LIMIT_BEACON', '5/m')},
    'platforms.custom_gis.*': {'rate_limit': os.getenv('SCRAPER_RATE_LIMIT_CUSTOM_GIS', '3/m')},
}

# Worker settings
app.conf.update(
    worker_concurrency=int(os.getenv('CELERY_WORKER_CONCURRENCY', 4)),
    worker_prefetch_multiplier=int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', 1)),
    task_acks_late=True,  # Acknowledge task only after completion
    task_reject_on_worker_lost=True,  # Requeue if worker dies
)
```

### Example: Scraping Multiple Counties Simultaneously

**Scenario:** Scrape Union County and Columbia County in parallel

```python
# Dispatch both counties at once
from celery import group
from platforms.custom_gis.custom_gis_functions import custom_gis_single_url_chain

union_urls = [
    'https://unionpa.com/parcel/12345',
    'https://unionpa.com/parcel/12346',
    # ... 214 URLs
]

columbia_urls = [
    'https://columbiapa.com/parcel/67890',
    'https://columbiapa.com/parcel/67891',
    # ... 108 URLs
]

# Create task group (all tasks run in parallel, distributed across workers)
job = group(
    custom_gis_single_url_chain.s(url) for url in union_urls + columbia_urls
)

# Execute asynchronously
result = job.apply_async()

# Monitor progress
print(f"Total tasks: {len(result)}")
print(f"Completed: {result.completed_count()}")
```

### Resource Management

**Browser Instances:**
- Each Celery worker process runs its own Selenium browser instance
- With `concurrency=8`, you'll have 8 browsers running simultaneously
- **Memory requirement:** ~500MB per browser = 4GB RAM for 8 workers

**CPU Usage:**
- Each browser uses ~20-30% CPU during active scraping
- **Recommended:** 4-8 workers on 8-core machine

**Network:**
- Rate limits still apply (e.g., 3 tasks/min for custom_gis)
- Multiple workers share the rate limit quota
- Celery enforces rate limits globally across all workers

### Monitoring Multi-Worker Setup

**Terminal 1: Redis (Broker)**
```bash
redis-server
```

**Terminal 2: Celery Worker**
```bash
celery -A celery_app worker --concurrency=8 --loglevel=info
```

**Terminal 3: Celery Flower (Web Monitoring UI)**
```bash
pip install flower
celery -A celery_app flower

# Access dashboard at http://localhost:5555
# View: Active tasks, worker status, task history, success/failure rates
```

**Terminal 4: Dispatch Tasks**
```python
python
>>> from platforms.custom_gis.custom_gis_functions import custom_gis_main_chain
>>> custom_gis_main_chain.delay()
```

### Scaling Strategy

| Workers | Concurrency | Total Parallel Tasks | RAM Required | Use Case |
|---------|-------------|----------------------|--------------|----------|
| 1 | 2 | 2 | 1GB | Development, testing |
| 1 | 4 | 4 | 2GB | Small-scale production |
| 1 | 8 | 8 | 4GB | Medium-scale (1-2 platforms) |
| 2 | 4 | 8 | 4GB | Multi-platform (dedicated workers) |
| 4 | 4 | 16 | 8GB | Large-scale (10+ platforms) |

**Auto-Scaling with Kubernetes (Future):**
```yaml
# Deploy Celery workers as Kubernetes Deployment
# Horizontal Pod Autoscaler scales workers based on queue length
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: External
    external:
      metric:
        name: celery_queue_length
      target:
        type: AverageValue
        averageValue: "10"  # Scale up if queue > 10 tasks per worker
```

### File Structure Updates

```
platforms/custom_gis/
├── __init__.py
├── custom_gis_functions.py     # Task implementations
└── config.py                   # Load from .env

# New file:
.env                            # Environment configuration
```

**config.py example:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Rate limiting per platform
RATE_LIMITS = {
    'qpublic': os.getenv('SCRAPER_RATE_LIMIT_QPUBLIC', '5/m'),
    'beacon': os.getenv('SCRAPER_RATE_LIMIT_BEACON', '5/m'),
    'custom_gis': os.getenv('SCRAPER_RATE_LIMIT_CUSTOM_GIS', '3/m'),
}

# Custom GIS URLs
CUSTOM_GIS_CONFIGS = {
    'union_fl': {
        'base_url': os.getenv('CUSTOM_GIS_UNION_FL_URL', 'https://unionpa.com'),
        'county': 'union_fl',
        'state': 'FL',
    },
    'columbia_fl': {
        'base_url': os.getenv('CUSTOM_GIS_COLUMBIA_FL_URL', 'https://columbiapa.com'),
        'county': 'columbia_fl',
        'state': 'FL',
    }
}
```

---

## Open Design Questions

- [x] ~~Should we use BaseParser abstract class?~~ **NO** - Task-based pattern is already established
- [x] ~~Should we add Playwright as fallback for complex JavaScript sites?~~ **NO** - Use Selenium first
- [x] ~~Should we implement database integration (MongoDB/PostgreSQL) before adding more platforms?~~ **NO** - File-based storage first, Airflow pipeline handles DB
- [x] ~~Should we add rate limiting per platform (currently global 5/m)?~~ **YES** - Move to .env settings, different limits per platform
- [ ] ~~Should we implement proxy rotation for large-scale scraping?~~ **LATER** - Add .env settings placeholder, implement when needed
- [ ] Should we add screenshot capture to `scrape_single_url()` for debugging?

---

## Approval

- [x] Reviewed by: Anton (Product Owner)
- [x] Approved on: 2026-01-01
- [x] Notes: All design questions resolved, ready for implementation planning
