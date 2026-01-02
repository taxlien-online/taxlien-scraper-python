# SDD: Sample HTML Collector for Tax Lien Data

> Development tool for collecting HTML test samples from county tax websites
> Status: Requirements Complete - Ready for Review
> Last Updated: 2025-12-31

---

## 🎯 Overview

**Sample Collector** - инструмент для автоматического сбора HTML-образцов из 130+ county websites для тестирования и разработки парсеров.

**Key Features:**
- ✅ 14 counties with working example URLs
- ✅ Support for 6 platform types
- ✅ Both HTTP and Selenium download methods
- ✅ Automatic metadata tracking
- ✅ Progress reporting and statistics
- ✅ CLI interface with filters

**Target:** 300-500 HTML samples from 50+ counties

---

## 📁 Documentation

### Requirements
- **[01-requirements.md](01-requirements.md)** - Complete requirements specification
  - 5 functional requirements (FR1-FR5)
  - 4 non-functional requirements (NFR1-NFR4)
  - User stories with acceptance criteria
  - Success metrics and coverage goals

---

## 🏗️ Architecture

### Components

```
Sample Collector Tool
├── platform_sample_urls.py    # URL generation with working examples
├── download_samples.py         # HTML downloader (HTTP + Selenium)
├── sample_collector.py         # Main orchestrator
└── Output:
    └── samples_collected/
        ├── fl_/columbia/custom_gis/*.html
        ├── fl_/union/custom_gis/*.html
        ├── az_/coconino/tyler/*.html
        └── collection_summary.json
```

### Workflow

```
1. Load counties from CSV
   ↓
2. Generate sample URLs (PlatformURLGenerator)
   ↓
3. Download HTML (SampleDownloader)
   ├── Simple HTTP (for static pages)
   └── Selenium (for JavaScript-heavy pages)
   ↓
4. Save with metadata
   ↓
5. Generate summary report
```

---

## 📊 Coverage Status

### Counties with Working URLs (14 total)

**Florida (12 counties):**
- ✅ Alachua (QPublic)
- ✅ Columbia (Custom GIS) - 3 sample parcels
- ✅ Union (Custom GIS) - 1 sample parcel
- ✅ Dixie (QPublic + GovernMax)
- ✅ Gadsden (QPublic + GovernMax)
- ✅ Polk (Custom) - 2 sample parcels
- ✅ Sarasota (Custom)
- ✅ Suwannee (Custom GIS) - 2 sample parcels
- ✅ Taylor (QPublic)
- ✅ Orange (Custom)
- ✅ Lafayette (Custom GIS) - 2 sample parcels
- ✅ Okeechobee (Custom GIS) - 1 sample parcel

**Arizona (2 counties):**
- ✅ Coconino (Tyler Technologies) - 2 sample parcels
- ✅ Pima (Custom) - 1 sample parcel

### Platform Distribution

| Platform | Counties | Sample Parcels | Status |
|----------|----------|----------------|--------|
| Custom GIS (floridapa.com) | 6 | 11 parcels | ✅ Ready |
| QPublic/Beacon | 4 | 6 parcels | ✅ Ready |
| GovernMax | 2 | 2 parcels | ✅ Ready |
| Custom (various) | 4 | 4 parcels | ✅ Ready |
| Tyler Technologies | 1 | 2 parcels | ✅ Ready |

**Total Ready to Download:** 25+ sample parcel URLs across 14 counties

---

## 🚀 Quick Start

### Prerequisites

```bash
cd /Users/anton/proj/TAXLIEN.online/parser
pip install seleniumbase requests beautifulsoup4
```

### List Available Counties

```bash
python download_samples.py --list
```

Output:
```
Counties with working sample URLs:
  - fl_columbia                  (FL Columbia)
  - fl_union                     (FL Union)
  - fl_polk                      (FL Polk)
  - az_coconino                  (AZ Coconino)
  ...
```

### Download Samples from Specific Counties

**Using Simple HTTP (fast):**
```bash
python download_samples.py --counties fl_columbia fl_union
```

**Using Selenium (for JavaScript pages):**
```bash
python download_samples.py --counties fl_columbia fl_union --selenium
```

### Download All Available Samples

```bash
python download_samples.py
```

This will download from all 14 counties with working URLs.

---

## 📂 Output Structure

```
samples_downloaded/
├── fl_/
│   ├── columbia/
│   │   ├── assessor_R00010-001.html
│   │   ├── assessor_R00010-001_meta.json
│   │   ├── assessor_R00010-001.png          # Screenshot if Selenium
│   │   ├── tax_R00010-001.html
│   │   ├── gis_142S1500061000.html
│   │   └── metadata.json
│   ├── union/
│   │   ├── assessor_1805210000005700.html
│   │   └── ...
│   └── polk/
│       └── ...
├── az_/
│   └── coconino/
│       └── ...
└── collection_summary.json                   # Stats report
```

### Metadata Example

```json
{
  "url": "https://columbia.floridapa.com/gis/?pin=R00010-001",
  "parcel_id": "R00010-001",
  "page_type": "assessor",
  "platform": "custom_gis",
  "county": "columbia",
  "state": "fl_",
  "download_date": "2025-12-31T18:30:00",
  "method": "selenium",
  "content_length": 125648,
  "screenshot": "assessor_R00010-001.png",
  "notes": "Working example from sources.csv"
}
```

---

## 🎯 Usage Examples

### Example 1: Test New Parser

```bash
# Download samples from Columbia County FL
python download_samples.py --counties fl_columbia --selenium

# Now use the downloaded HTML to test your parser
cd samples_downloaded/fl_/columbia/
ls *.html
```

### Example 2: Research Platform Structure

```python
from platform_sample_urls import PlatformURLGenerator

gen = PlatformURLGenerator()

# Show all info about Columbia County
gen.print_county_info('fl_', 'columbia')

# Get sample URLs
urls = gen.get_sample_urls('fl_', 'columbia', num_samples=3)
for url in urls:
    print(f"{url.page_type}: {url.url}")
```

### Example 3: Batch Download by Platform

```bash
# Download all Custom GIS counties
python download_samples.py \
  --counties fl_columbia fl_union fl_lafayette fl_suwannee fl_okeechobee \
  --selenium
```

---

## 📊 Expected Results

### Download Statistics

After running full collection:

```json
{
  "total_downloads": 72,
  "successful": 68,
  "failed": 4,
  "by_platform": {
    "custom_gis": 33,
    "qpublic": 18,
    "custom": 12,
    "governmax": 3,
    "tyler": 6
  },
  "by_state": {
    "fl_": 63,
    "az_": 9
  },
  "by_page_type": {
    "assessor": 28,
    "tax": 22,
    "gis": 15,
    "recorder": 7
  }
}
```

---

## 🔗 Related SDDs

### Relationship to Other Components

**This SDD (Sample Collector):**
- Purpose: Collect test samples (3-5 per county)
- Scope: Development tool
- Output: `samples_collected/` directory
- Frequency: One-time or periodic updates

**[sdd-scraper-service](../sdd-scraper-service/):**
- Purpose: Production data collection (ALL parcels)
- Scope: 15 platforms, 3,000+ counties
- Output: MongoDB + PostgreSQL
- Frequency: Daily/weekly via Celery

**Workflow:**
```
Sample Collector (this SDD)
    ↓ Provides test data
Parser Development
    ↓ Creates parser
Production Scraper (sdd-scraper-service)
    ↓ Uses parser at scale
Database (sdd-data-structure)
```

---

## 🎯 Success Metrics

### Current Status

**Scripts:** ✅ 90% Complete
- `platform_sample_urls.py` - ✅ Done (14 counties)
- `download_samples.py` - ✅ Done (full CLI)
- `sample_collector.py` - ✅ Done (orchestrator)

**Ready to Download:**
- 14 counties with working URLs
- 25+ sample parcel URLs
- Expected: 50-100 HTML files

**Next Steps:**
1. ✅ Requirements documented
2. ⏳ User approval (current)
3. ⏳ Test download on 5 counties
4. ⏳ Full collection run
5. ⏳ Document results

---

## 🐛 Troubleshooting

### Issue: Selenium not available

```bash
pip install seleniumbase sbvirtualdisplay
```

### Issue: Rate limiting / blocked

**Solution:** Increase delays
```python
# In download_samples.py
time.sleep(random.uniform(4, 8))  # instead of 2-4
```

### Issue: Page structure changed

**Solution:** URLs in `platform_sample_urls.py` are from 2025-12-30. If pages change:
1. Check CSV for updated example URLs
2. Update `working_examples` dict in `platform_sample_urls.py`

---

**Status:** REQUIREMENTS COMPLETE - Ready for Review
**Next Phase:** SPECIFICATIONS (design implementation details)
**Blocker:** Waiting for user approval
