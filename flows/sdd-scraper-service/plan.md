# Implementation Plan: Multi-Platform Scraper Service

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-01-01
> Specifications: [specifications.md](specifications.md)

## Summary

This plan outlines the implementation of CustomGISParser and core infrastructure improvements to support 15+ platform scrapers. The work is broken into 4 phases with clear dependencies and verification steps.

**Key Approach:**
- Start with infrastructure updates (storage, config, Celery)
- Implement CustomGISParser using 322 sample HTML files (offline parsing)
- Test and validate with live scraping
- Deploy to production

**Timeline Estimate:** 2-3 weeks for CustomGISParser + infrastructure

---

## Task Breakdown

### Phase 1: Infrastructure Foundation

#### Task 1.1: Environment Configuration Setup
- **Description**: Create `.env` file and configuration loader
- **Files**:
  - `.env` - Create (configuration file)
  - `.env.example` - Create (template for other developers)
  - `requirements.txt` - Modify (add python-dotenv, flower)
- **Dependencies**: None
- **Verification**:
  - Run `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('CELERY_BROKER_URL'))"`
  - Should print Redis URL
- **Complexity**: Low

**Implementation Details:**
```bash
# Create .env file with all configuration
cat > .env << 'EOF'
# Scraper Configuration
SCRAPER_STORAGE_PATH=./storage
SCRAPER_RATE_LIMIT_QPUBLIC=5/m
SCRAPER_RATE_LIMIT_BEACON=5/m
SCRAPER_RATE_LIMIT_CUSTOM_GIS=3/m
SCRAPER_HEADLESS=false
SCRAPER_ENABLE_MANIFEST=true

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1

# Platform-specific
CUSTOM_GIS_UNION_FL_URL=https://unionpa.com
CUSTOM_GIS_COLUMBIA_FL_URL=https://columbiapa.com
EOF

# Update requirements.txt
echo "python-dotenv==1.0.0" >> requirements.txt
echo "flower==2.0.1" >> requirements.txt

# Install new dependencies
pip install -r requirements.txt
```

---

#### Task 1.2: Update Storage Directory Structure
- **Description**: Modify storage to use pending/processing/processed subdirectories
- **Files**:
  - `functions.py` - Modify (`save_html`, `save_json`, `save_csv`)
- **Dependencies**: Task 1.1 (needs .env config)
- **Verification**:
  - Call `save_json({...}, 'test_platform', 'test_file')`
  - Verify `./storage/test_platform/pending/test_file.json` exists
  - Verify `./storage/test_platform/pending/manifest.jsonl` created
- **Complexity**: Medium

**Implementation Details:**
```python
# Update functions.py
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def save_html(html: str, platform: str, name: str) -> str:
    """Saves HTML to ./storage/{platform}/pending/{name}.html"""
    storage_path = os.getenv('SCRAPER_STORAGE_PATH', './storage')
    pending_dir = f"{storage_path}/{platform}/pending"
    os.makedirs(pending_dir, exist_ok=True)

    filepath = f"{pending_dir}/{name}.html"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML saved: {filepath}")
    return filepath

def save_json(data: dict, platform: str, name: str) -> None:
    """Saves JSON to pending/ and appends to manifest.jsonl"""
    storage_path = os.getenv('SCRAPER_STORAGE_PATH', './storage')
    pending_dir = f"{storage_path}/{platform}/pending"
    os.makedirs(pending_dir, exist_ok=True)

    # Save JSON
    filepath = f"{pending_dir}/{name}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Append to manifest (only if enabled)
    if os.getenv('SCRAPER_ENABLE_MANIFEST', 'true').lower() == 'true':
        manifest = {
            "file": f"{name}.json",
            "platform": platform,
            "county": data.get('county', 'unknown'),
            "parcel_id": data.get('parcel_id', 'unknown'),
            "scraped_at": data.get('scraped_at', datetime.now().isoformat()),
            "status": "pending"
        }

        manifest_path = f"{pending_dir}/manifest.jsonl"
        with open(manifest_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(manifest, ensure_ascii=False) + '\n')

    print(f"JSON saved: {filepath}")

def save_csv(data: dict, platform: str, name: str) -> None:
    """Saves CSV to pending/ (appends to existing file)"""
    import csv
    storage_path = os.getenv('SCRAPER_STORAGE_PATH', './storage')
    pending_dir = f"{storage_path}/{platform}/pending"
    os.makedirs(pending_dir, exist_ok=True)

    filepath = f"{pending_dir}/{name}.csv"
    file_exists = os.path.isfile(filepath)

    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

    print(f"CSV appended: {filepath}")
```

---

#### Task 1.3: Update Celery Configuration
- **Description**: Add queue routing, rate limiting, and .env support to celery_app.py
- **Files**:
  - `celery_app.py` - Modify (major update)
- **Dependencies**: Task 1.1 (needs .env)
- **Verification**:
  - Start Celery: `celery -A celery_app worker --loglevel=info`
  - Verify queues created: default, qpublic_queue, beacon_queue, custom_gis_queue, etc.
  - Check rate limits applied in logs
- **Complexity**: Medium

**Implementation Details:**
```python
# celery_app.py
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

# Route tasks to appropriate queues based on task name pattern
app.conf.task_routes = {
    'platforms.qpublic.*': {'queue': 'qpublic_queue'},
    'platforms.beacon.*': {'queue': 'beacon_queue'},
    'platforms.custom_gis.*': {'queue': 'custom_gis_queue'},
    'platforms.tyler_technologies.*': {'queue': 'tyler_queue'},
    'platforms.bid4assets.*': {'queue': 'bid4assets_queue'},
}

# Rate limiting per platform (loaded from .env)
app.conf.task_annotations = {
    'platforms.qpublic.*': {'rate_limit': os.getenv('SCRAPER_RATE_LIMIT_QPUBLIC', '5/m')},
    'platforms.beacon.*': {'rate_limit': os.getenv('SCRAPER_RATE_LIMIT_BEACON', '5/m')},
    'platforms.custom_gis.*': {'rate_limit': os.getenv('SCRAPER_RATE_LIMIT_CUSTOM_GIS', '3/m')},
}

# Worker settings from .env
app.conf.update(
    worker_concurrency=int(os.getenv('CELERY_WORKER_CONCURRENCY', 4)),
    worker_prefetch_multiplier=int(os.getenv('CELERY_WORKER_PREFETCH_MULTIPLIER', 1)),
    task_acks_late=True,  # Acknowledge task only after completion
    task_reject_on_worker_lost=True,  # Requeue if worker crashes
    result_expires=3600,  # Results expire after 1 hour
)
```

---

### Phase 2: CustomGISParser Implementation (Offline Parsing)

#### Task 2.1: Create CustomGIS Platform Structure
- **Description**: Create directory structure and config module for CustomGIS
- **Files**:
  - `platforms/custom_gis/__init__.py` - Create
  - `platforms/custom_gis/config.py` - Create (load from .env)
  - `platforms/custom_gis/custom_gis_functions.py` - Create (stub)
- **Dependencies**: Task 1.1 (needs .env support)
- **Verification**:
  - `python -c "from platforms.custom_gis.config import CUSTOM_GIS_CONFIGS; print(CUSTOM_GIS_CONFIGS)"`
  - Should print Union and Columbia county configs
- **Complexity**: Low

**Implementation Details:**
```python
# platforms/custom_gis/__init__.py
"""Custom GIS Parser for Union County FL and Columbia County FL"""

# platforms/custom_gis/config.py
import os
from dotenv import load_dotenv

load_dotenv()

CUSTOM_GIS_CONFIGS = {
    'union_fl': {
        'base_url': os.getenv('CUSTOM_GIS_UNION_FL_URL', 'https://unionpa.com'),
        'county': 'union_fl',
        'state': 'FL',
        'sample_dir': 'samples/UnionPA.com',
    },
    'columbia_fl': {
        'base_url': os.getenv('CUSTOM_GIS_COLUMBIA_FL_URL', 'https://columbiapa.com'),
        'county': 'columbia_fl',
        'state': 'FL',
        'sample_dir': 'samples/ColumbiaPA.com',
    }
}
```

---

#### Task 2.2: Implement HTML Parser (Sample-Based)
- **Description**: Implement `custom_gis_parse_single_html_task` using 322 sample files
- **Files**:
  - `platforms/custom_gis/custom_gis_functions.py` - Modify (add parser function)
- **Dependencies**: Task 2.1
- **Verification**:
  - Read one sample HTML: `with open('samples/UnionPA.com/sample1.html') as f: html = f.read()`
  - Parse: `data = custom_gis_parse_single_html_task(html)`
  - Verify data dict has parcel_id, owner, property_address, etc.
  - Test on all 322 samples, measure success rate
- **Complexity**: High (main parsing logic)

**Implementation Details:**
```python
# platforms/custom_gis/custom_gis_functions.py
from celery_app import app
from bs4 import BeautifulSoup
from datetime import datetime
import re

@app.task(bind=True, max_retries=3, name='platforms.custom_gis.parse_single_html')
def custom_gis_parse_single_html_task(self, html: str) -> dict:
    """
    Parse Custom GIS HTML page into standardized property data.

    Args:
        html: Raw HTML content

    Returns:
        dict: Standardized property data with 90+ attributes
    """
    # Initialize empty data dict with all fields
    data = {
        # Core identifiers
        'parcel_id': None,
        'property_address': None,
        'legal_description': None,

        # Owner information
        'owner': None,
        'mailing_address': None,

        # Property details
        'property_type': None,
        'bedrooms': None,
        'bathrooms': None,
        'building_sqft': None,
        'lot_size': None,
        'year_built': None,
        'zoning': None,

        # Financial data
        'assessed_value': None,
        'land_value': None,
        'improvement_value': None,
        'market_value': None,
        'total_due_amount': None,
        'tax_amount': None,

        # Tax information
        'tax_year': None,
        'tax_status': None,
        'exemptions': None,
        'has_delinquency': False,

        # Sales history
        'last_sale_date': None,
        'last_sale_price': None,
        'deed_book': None,
        'deed_page': None,

        # Media and documents
        'image_urls': [],
        'document_urls': [],
        'map_url': None,

        # Metadata
        'parse_error': None,
        'scraped_at': datetime.now().isoformat(),
        'source': 'custom_gis'
    }

    try:
        doc = BeautifulSoup(html, 'html.parser')

        # Parse parcel ID (multiple possible selectors)
        parcel_selectors = [
            {'id': re.compile('parcel', re.I)},
            {'class_': re.compile('parcel', re.I)},
            {'id': re.compile('gisSideMenu.*Details', re.I)},
        ]

        for selector in parcel_selectors:
            elem = doc.find(**selector)
            if elem:
                data['parcel_id'] = elem.get_text(strip=True)
                break

        # Parse owner name
        owner_selectors = [
            {'id': re.compile('owner', re.I)},
            {'class_': re.compile('owner', re.I)},
        ]

        for selector in owner_selectors:
            elem = doc.find(**selector)
            if elem:
                data['owner'] = elem.get_text(strip=True)
                break

        # Parse property address
        address_selectors = [
            {'id': re.compile('(situs|site|property).*address', re.I)},
            {'class_': re.compile('address', re.I)},
        ]

        for selector in address_selectors:
            elem = doc.find(**selector)
            if elem:
                data['property_address'] = elem.get_text(strip=True)
                break

        # Parse assessed value
        value_selectors = [
            {'id': re.compile('assessed.*value', re.I)},
            {'class_': re.compile('assessed', re.I)},
        ]

        for selector in value_selectors:
            elem = doc.find(**selector)
            if elem:
                data['assessed_value'] = elem.get_text(strip=True)
                break

        # TODO: Add more field parsing based on actual sample HTML structure
        # This requires analyzing the 322 sample files to find common patterns

        # Parse images (find all img tags)
        images = doc.find_all('img', src=True)
        data['image_urls'] = [img['src'] for img in images if 'logo' not in img['src'].lower()]

    except Exception as e:
        print(f"Error parsing custom_gis HTML: {e}")
        data['parse_error'] = str(e)

    return data
```

---

#### Task 2.3: Create Test Suite for Parser
- **Description**: Test parser on all 322 sample HTML files
- **Files**:
  - `tests/test_custom_gis_parser.py` - Create
- **Dependencies**: Task 2.2
- **Verification**:
  - Run `pytest tests/test_custom_gis_parser.py`
  - Verify ≥95% parse success rate (≥306/322 samples)
  - Verify ≥90% field coverage (≥81/90 attributes extracted)
- **Complexity**: Medium

**Implementation Details:**
```python
# tests/test_custom_gis_parser.py
import pytest
import os
from platforms.custom_gis.custom_gis_functions import custom_gis_parse_single_html_task

SAMPLE_DIRS = [
    'samples/UnionPA.com',
    'samples/ColumbiaPA.com'
]

def get_all_sample_files():
    """Find all .html files in sample directories"""
    samples = []
    for dir_path in SAMPLE_DIRS:
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                if filename.endswith('.html'):
                    samples.append(os.path.join(dir_path, filename))
    return samples

def test_parse_all_samples():
    """Test parser on all 322 sample files"""
    samples = get_all_sample_files()
    print(f"\\nFound {len(samples)} sample files")

    success_count = 0
    failed_samples = []

    for filepath in samples:
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()

        data = custom_gis_parse_single_html_task(html)

        # Check if parcel_id was extracted (minimum requirement)
        if data.get('parcel_id') and not data.get('parse_error'):
            success_count += 1
        else:
            failed_samples.append(filepath)

    success_rate = (success_count / len(samples)) * 100
    print(f"Success rate: {success_rate:.1f}% ({success_count}/{len(samples)})")

    if failed_samples:
        print(f"Failed samples ({len(failed_samples)}):")
        for f in failed_samples[:10]:  # Show first 10 failures
            print(f"  - {f}")

    # Assert 95%+ success rate
    assert success_rate >= 95.0, f"Parser success rate ({success_rate:.1f}%) below 95% threshold"

def test_field_coverage():
    """Test that parser extracts ≥90% of fields"""
    samples = get_all_sample_files()[:10]  # Test first 10 samples

    all_fields = [
        'parcel_id', 'property_address', 'owner', 'assessed_value',
        'land_value', 'improvement_value', 'year_built', 'building_sqft',
        # ... list all 90 fields
    ]

    field_counts = {field: 0 for field in all_fields}

    for filepath in samples:
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()

        data = custom_gis_parse_single_html_task(html)

        for field in all_fields:
            if data.get(field):
                field_counts[field] += 1

    # Calculate average field coverage
    avg_coverage = sum(field_counts.values()) / (len(all_fields) * len(samples)) * 100
    print(f"Average field coverage: {avg_coverage:.1f}%")

    assert avg_coverage >= 90.0, f"Field coverage ({avg_coverage:.1f}%) below 90% threshold"
```

---

### Phase 3: CustomGISParser Live Scraping

#### Task 3.1: Implement URL Discovery Functions
- **Description**: Implement `custom_gis_scrape_counties_urls_task` and `custom_gis_get_all_parcels_urls_task`
- **Files**:
  - `platforms/custom_gis/custom_gis_functions.py` - Modify (add URL discovery tasks)
- **Dependencies**: Task 2.2 (parser working)
- **Verification**:
  - Call `custom_gis_scrape_counties_urls_task()`
  - Should return `{'union_fl': 'https://unionpa.com/...', 'columbia_fl': '...'}`
  - Call `custom_gis_get_all_parcels_urls_task(counties)`
  - Should return list of 322+ parcel URLs
- **Complexity**: High (requires reverse-engineering county portals)

**Implementation Details:**
```python
# platforms/custom_gis/custom_gis_functions.py (add these tasks)

@app.task(name='platforms.custom_gis.scrape_counties_urls')
def custom_gis_scrape_counties_urls_task(base_url: str = None) -> dict:
    """
    Get list of county URLs for Custom GIS platform.

    Returns:
        dict: {county_name: county_url, ...}
    """
    from platforms.custom_gis.config import CUSTOM_GIS_CONFIGS

    counties_urls = {}

    for county_key, config in CUSTOM_GIS_CONFIGS.items():
        counties_urls[county_key] = config['base_url']

    print(f"Found {len(counties_urls)} Custom GIS counties")
    return counties_urls

@app.task(name='platforms.custom_gis.get_all_parcels_urls')
def custom_gis_get_all_parcels_urls_task(counties_urls: dict) -> list:
    """
    Extract all parcel URLs from given county URLs.

    This requires navigating each county portal and extracting parcel search results.
    Implementation depends on county-specific portal structure.

    Args:
        counties_urls: Dict from scrape_counties_urls_task

    Returns:
        list: [parcel_url1, parcel_url2, ...]
    """
    from functions import scrape_single_url

    all_parcel_urls = []

    for county, county_url in counties_urls.items():
        print(f"Scraping parcel URLs for {county}...")

        # TODO: Navigate county portal to find parcel search page
        # TODO: Execute search (may require form submission)
        # TODO: Extract all parcel URLs from results
        # TODO: Handle pagination if needed

        # Placeholder: Return empty list for now
        # This task requires manual inspection of each county portal

    print(f"Found {len(all_parcel_urls)} total parcel URLs")
    return all_parcel_urls
```

---

#### Task 3.2: Implement Main Chain Orchestration
- **Description**: Create `custom_gis_main_chain` and `custom_gis_single_url_chain`
- **Files**:
  - `platforms/custom_gis/custom_gis_functions.py` - Modify (add chain functions)
  - `tasks.py` - Modify (add wrapper tasks)
- **Dependencies**: Task 3.1, Task 2.2
- **Verification**:
  - Call `custom_gis_single_url_chain.delay('https://unionpa.com/parcel/12345')`
  - Verify HTML saved to `./storage/custom_gis/pending/`
  - Verify JSON saved with parsed data
  - Verify manifest.jsonl updated
- **Complexity**: Medium

**Implementation Details:**
```python
# platforms/custom_gis/custom_gis_functions.py (add chain tasks)

from celery import chain, group
from functions import scrape_single_url, save_html, save_json, generate_name

@app.task(name='platforms.custom_gis.single_url_chain')
def custom_gis_single_url_chain(url: str):
    """
    Process single parcel URL through complete chain:
    scrape → save HTML → parse → save JSON

    Args:
        url: Parcel URL to scrape
    """
    # Step 1: Scrape URL
    html = scrape_single_url(url, headless=False)

    # Step 2: Save HTML
    name = generate_name('custom_gis', url.split('/')[-1])
    save_html(html, 'custom_gis', name)

    # Step 3: Parse HTML
    data = custom_gis_parse_single_html_task(html)

    # Step 4: Save JSON
    save_json(data, 'custom_gis', name)

    print(f"Completed: {url}")
    return data

@app.task(name='platforms.custom_gis.main_chain')
def custom_gis_main_chain():
    """
    Execute full scraping workflow for Custom GIS platform:
    1. Get county URLs
    2. Get all parcel URLs
    3. Process each parcel in parallel
    """
    # Step 1: Get counties
    counties_urls = custom_gis_scrape_counties_urls_task()

    # Step 2: Get all parcel URLs
    all_parcels_urls = custom_gis_get_all_parcels_urls_task(counties_urls)

    # Step 3: Save URLs list
    from functions import save_json
    save_json({'urls': all_parcels_urls}, 'custom_gis', 'all_parcel_urls')

    # Step 4: Process each parcel in parallel
    job = group(
        custom_gis_single_url_chain.s(url)
        for url in all_parcels_urls
    )

    result = job.apply_async()
    print(f"Dispatched {len(all_parcels_urls)} tasks")

    return {'total_tasks': len(all_parcels_urls), 'job_id': result.id}
```

---

### Phase 4: Testing & Deployment

#### Task 4.1: Integration Testing
- **Description**: Test complete workflow end-to-end
- **Files**:
  - `tests/test_custom_gis_integration.py` - Create
- **Dependencies**: All previous tasks
- **Verification**:
  - Start Redis: `redis-server`
  - Start Celery worker: `celery -A celery_app worker --concurrency=2`
  - Run test: `pytest tests/test_custom_gis_integration.py`
  - Verify files created in `./storage/custom_gis/pending/`
- **Complexity**: Medium

**Implementation Details:**
```python
# tests/test_custom_gis_integration.py
import pytest
import os
from platforms.custom_gis.custom_gis_functions import (
    custom_gis_single_url_chain,
    custom_gis_scrape_counties_urls_task
)

def test_single_url_workflow():
    """Test single URL scraping workflow (using sample file)"""
    # Use a sample file to simulate scraping
    with open('samples/UnionPA.com/sample1.html', 'r') as f:
        html = f.read()

    # Test parser directly
    from platforms.custom_gis.custom_gis_functions import custom_gis_parse_single_html_task
    data = custom_gis_parse_single_html_task(html)

    assert data['parcel_id'] is not None
    assert data['source'] == 'custom_gis'
    assert data['parse_error'] is None

def test_counties_discovery():
    """Test county URL discovery"""
    counties = custom_gis_scrape_counties_urls_task()

    assert 'union_fl' in counties
    assert 'columbia_fl' in counties
    assert 'unionpa.com' in counties['union_fl'].lower()
```

---

#### Task 4.2: Production Deployment Setup
- **Description**: Document deployment process and create startup scripts
- **Files**:
  - `scripts/start_worker.sh` - Create (Celery worker startup)
  - `scripts/start_flower.sh` - Create (Flower monitoring)
  - `README_DEPLOYMENT.md` - Create (deployment guide)
- **Dependencies**: Task 4.1
- **Verification**:
  - Run `./scripts/start_worker.sh`
  - Verify Celery worker starts with correct config
  - Run `./scripts/start_flower.sh`
  - Access http://localhost:5555, verify Flower dashboard
- **Complexity**: Low

**Implementation Details:**
```bash
# scripts/start_worker.sh
#!/bin/bash
source .env
celery -A celery_app worker \
  --concurrency=$CELERY_WORKER_CONCURRENCY \
  --loglevel=info \
  --logfile=logs/celery_worker.log

# scripts/start_flower.sh
#!/bin/bash
source .env
celery -A celery_app flower \
  --port=5555 \
  --logfile=logs/flower.log
```

---

#### Task 4.3: Live Scraping Test (Limited)
- **Description**: Test live scraping on 10 parcels per county (20 total)
- **Files**:
  - `scripts/test_live_scraping.py` - Create
- **Dependencies**: Task 4.2
- **Verification**:
  - Run script: `python scripts/test_live_scraping.py`
  - Verify 20 HTML files saved to `./storage/custom_gis/pending/`
  - Verify 20 JSON files with parsed data
  - Verify manifest.jsonl has 20 entries
  - Compare live results to sample results (should match structure)
- **Complexity**: Medium

---

#### Task 4.4: Production Scraping (Full Scale)
- **Description**: Execute full scraping for Union County (214) + Columbia County (108)
- **Files**:
  - None (run existing code)
- **Dependencies**: Task 4.3 (live test successful)
- **Verification**:
  - Run `custom_gis_main_chain.delay()`
  - Monitor via Flower dashboard
  - Verify 322 files saved to pending/
  - Check parse success rate ≥95% (≥306 successful)
  - Monitor error rates in logs
- **Complexity**: Low (execution only)

---

## Dependency Graph

```
Phase 1: Infrastructure
Task 1.1 (Env Config)
   ↓
Task 1.2 (Storage Structure) ──┐
   ↓                            │
Task 1.3 (Celery Config) ──────┤
                                ↓
Phase 2: Parser (Offline)
Task 2.1 (Platform Structure) ──┤
   ↓                            │
Task 2.2 (HTML Parser) ─────────┤
   ↓                            │
Task 2.3 (Test Suite) ──────────┤
                                ↓
Phase 3: Live Scraping
Task 3.1 (URL Discovery) ───────┤
   ↓                            │
Task 3.2 (Chain Orchestration) ─┤
                                ↓
Phase 4: Testing & Deploy
Task 4.1 (Integration Tests) ───┤
   ↓                            │
Task 4.2 (Deployment Setup) ────┤
   ↓                            │
Task 4.3 (Live Test - 20) ──────┤
   ↓                            │
Task 4.4 (Production - 322) ────┘
```

---

## File Change Summary

| File | Action | Reason |
|------|--------|--------|
| `.env` | Create | Centralized configuration |
| `.env.example` | Create | Template for developers |
| `requirements.txt` | Modify | Add python-dotenv, flower |
| `functions.py` | Modify | Update save_* functions for pending/ + manifest |
| `celery_app.py` | Modify | Add queues, routing, rate limits, .env support |
| `platforms/custom_gis/__init__.py` | Create | Package initialization |
| `platforms/custom_gis/config.py` | Create | Load CustomGIS configs from .env |
| `platforms/custom_gis/custom_gis_functions.py` | Create | All CustomGIS tasks (parse, scrape, chains) |
| `tests/test_custom_gis_parser.py` | Create | Parser unit tests (322 samples) |
| `tests/test_custom_gis_integration.py` | Create | Integration tests |
| `scripts/start_worker.sh` | Create | Celery worker startup script |
| `scripts/start_flower.sh` | Create | Flower monitoring startup |
| `scripts/test_live_scraping.py` | Create | Live scraping test (20 parcels) |
| `README_DEPLOYMENT.md` | Create | Deployment documentation |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Sample HTML structure differs from live pages | Medium | High | Test on 10 live parcels first (Task 4.3) before full scrape |
| Rate limiting blocks scraping | Medium | Medium | Use 3/m rate limit, add retry logic, monitor for 429 errors |
| Cloudflare blocks Selenium | Low | High | Use `scraper_pass_challenge()`, rotate user agents, add delays |
| Parsing success rate <95% | Medium | Medium | Iterate on selectors, add fallback patterns, log failures |
| Redis/Celery crashes during scrape | Low | High | Use `task_acks_late=True`, implement health checks, auto-restart |
| Storage fills up (322 HTML+JSON files) | Low | Medium | Monitor disk space, implement cleanup script, archive to S3 |

---

## Rollback Strategy

If implementation fails or needs to be reverted:

1. **Revert code changes:**
   ```bash
   git revert <commit-hash>
   # OR restore from backup
   git checkout main -- functions.py celery_app.py
   ```

2. **Remove CustomGIS platform:**
   ```bash
   rm -rf platforms/custom_gis/
   ```

3. **Restore original storage structure:**
   ```bash
   # Old structure: ./storage/{platform}/{name}.json
   # New structure: ./storage/{platform}/pending/{name}.json
   # Migration script if needed to move files back
   ```

4. **Revert configuration:**
   ```bash
   # Remove .env file
   rm .env

   # Revert requirements.txt
   git checkout main -- requirements.txt
   pip install -r requirements.txt
   ```

---

## Checkpoints

After each phase, verify:

### Phase 1 Checkpoint:
- [ ] `.env` file exists with all variables
- [ ] `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('CELERY_BROKER_URL'))"` works
- [ ] `pip list | grep -E "(dotenv|flower)"` shows both packages
- [ ] Test `save_json()` creates `./storage/test/pending/test.json` and `manifest.jsonl`
- [ ] Celery worker starts with queues: `celery -A celery_app inspect active_queues`

### Phase 2 Checkpoint:
- [ ] `platforms/custom_gis/` directory exists with all files
- [ ] Import works: `from platforms.custom_gis.custom_gis_functions import custom_gis_parse_single_html_task`
- [ ] Parser test passes: `pytest tests/test_custom_gis_parser.py`
- [ ] Parse success rate ≥95% (≥306/322)
- [ ] Field coverage ≥90% (≥81/90 attributes)

### Phase 3 Checkpoint:
- [ ] `custom_gis_scrape_counties_urls_task()` returns 2 counties
- [ ] `custom_gis_single_url_chain` completes without errors (test with sample)
- [ ] Files saved to correct location: `./storage/custom_gis/pending/`
- [ ] Manifest updated correctly

### Phase 4 Checkpoint:
- [ ] Integration tests pass: `pytest tests/test_custom_gis_integration.py`
- [ ] Flower dashboard accessible at http://localhost:5555
- [ ] Live scraping test (20 parcels) succeeds
- [ ] Production scraping (322 parcels) completes
- [ ] Final parse success rate ≥95%

---

## Open Implementation Questions

- [ ] What is the exact HTML structure of Union/Columbia county portals? (Need to analyze 322 samples)
- [ ] Do county portals require login/authentication?
- [ ] How to handle JavaScript-rendered content? (Selenium wait times, element detection)
- [ ] Should we implement screenshot capture for debugging? (Add to `scrape_single_url`)
- [ ] What is the actual parcel URL format for each county? (Need manual discovery)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
