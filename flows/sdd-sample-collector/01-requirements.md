# Requirements: Sample HTML Collector for Tax Lien Data

**Date:** 2025-12-31
**Phase:** REQUIREMENTS
**Purpose:** Собрать образцы HTML-страниц из всех county tax websites для разработки парсеров

---

## 📊 Problem Statement

### Current Situation

**Existing Scraper:**
- Уже есть production scraper в `parser/taxlien-scraper-python/`
- Поддерживает 4 платформы: QPublic, Beacon, Tyler Technologies, Bid4Assets
- Использует Celery + SeleniumBase для скрапинга
- Сохраняет HTML в `downloaded_files/`

**Problem:**
- Перед добавлением новой платформы нужны HTML-примеры для анализа
- Ручной сбор образцов медленный и неэффективный
- Нет централизованной базы образцов для тестирования парсеров
- Сложно протестировать парсер без живых данных

### What We Need

**Sample Collector Tool** - инструмент для автоматического сбора HTML-образцов со всех county websites:

1. **Input:** CSV file с 130+ округами (`Tax Liens - Sources - Sheet1.csv`)
2. **Output:** Организованная коллекция HTML-файлов по структуре:
   ```
   samples_collected/
   ├── fl_/
   │   ├── columbia/
   │   │   ├── custom_gis/
   │   │   │   ├── assessor_R00010-001.html
   │   │   │   ├── assessor_R00010-001_meta.json
   │   │   │   ├── tax_R00010-001.html
   │   │   │   └── gis_142S1500061000.html
   │   │   └── metadata.json
   │   ├── union/
   │   └── ...
   ├── az_/
   └── ...
   ```
3. **Coverage:** 108 образцов на округ × 130 округов = ~14,040 HTML файлов

---

## 👥 User Stories

### Story 1: Developer Testing Parser
**As a** parser developer
**I want** to have 3-5 real HTML examples from each county
**So that** I can test my parser logic without making live requests

**Acceptance Criteria:**
- ✅ Each county has at least 3 HTML samples
- ✅ Samples include different types: assessor, tax, GIS, recorder
- ✅ Metadata includes URL, parcel ID, download date
- ✅ Screenshots saved for JavaScript-heavy pages

---

### Story 2: Platform Research
**As a** platform analyst
**I want** to download samples from a new platform
**So that** I can study its HTML structure before implementing a parser

**Acceptance Criteria:**
- ✅ Can specify specific counties to download
- ✅ Can use Selenium for JavaScript-heavy pages
- ✅ HTML is saved with proper encoding (UTF-8)
- ✅ Failed downloads are logged with error details

---

### Story 3: Regression Testing
**As a** QA engineer
**I want** to have a static collection of HTML samples
**So that** I can run parser tests without depending on live websites

**Acceptance Criteria:**
- ✅ Samples are version-controlled
- ✅ Each sample has metadata (download date, platform type)
- ✅ Can re-download samples to compare HTML changes over time
- ✅ Summary report shows coverage stats

---

## 🎯 Functional Requirements

### FR1: Source Management
**Priority:** HIGH

**Description:** Загрузка и парсинг CSV файла с источниками округов

**Requirements:**
- Read `Tax Liens - Sources - Sheet1.csv` (130 counties)
- Parse columns: state, county, Assessor URL, Tax URL, GIS URL, Recorder URL
- Identify platform type from URL patterns and indicators (QP, PT, GIS, etc.)
- Filter counties by state or platform type

**Inputs:**
- CSV file path
- Optional: state filter (e.g., `fl_`, `az_`)
- Optional: platform filter (e.g., `qpublic`, `custom_gis`)

**Outputs:**
- List of counties to process
- Platform identification for each county

---

### FR2: URL Generation
**Priority:** HIGH

**Description:** Генерация рабочих URL для скачивания образцов

**Requirements:**
- Use working example URLs from CSV (example parcel IDs)
- Generate 3-5 URLs per county for different page types
- Support platform-specific URL patterns:
  - **Custom GIS (floridapa.com):** `?pin=PARCEL_ID`
  - **QPublic:** Search-based, needs interactive navigation
  - **PropertyTax:** `?parcel=PARCEL_ID`
  - **Tyler:** ASPX ViewState-based

**Inputs:**
- County config (state, county, platform)
- Sample parcel IDs

**Outputs:**
- List of `SampleURL` objects with:
  - url
  - parcel_id
  - page_type (assessor, tax, gis, recorder)
  - platform
  - notes

---

### FR3: HTML Download
**Priority:** HIGH

**Description:** Скачивание HTML-страниц с разными методами

**Methods:**
1. **Simple HTTP** - для статических страниц
2. **Selenium** - для JavaScript-heavy страниц

**Requirements:**
- Auto-detect which method to use based on platform
- Save HTML with UTF-8 encoding
- Save screenshots for Selenium downloads
- Polite delays between requests (2-4 seconds)
- User-Agent rotation
- Handle redirects and errors gracefully

**Inputs:**
- SampleURL object
- Method choice (auto/simple/selenium)

**Outputs:**
- HTML file: `{page_type}_{parcel_id}.html`
- Screenshot: `{page_type}_{parcel_id}.png` (if Selenium)
- Metadata JSON: `{page_type}_{parcel_id}_meta.json`

---

### FR4: Metadata Tracking
**Priority:** MEDIUM

**Description:** Сохранение метаданных о каждом образце

**Metadata Fields:**
- url: Original URL
- parcel_id: Parcel identifier
- page_type: assessor/tax/gis/recorder
- platform: Platform type
- county: County name
- state: State code
- download_date: ISO timestamp
- method: simple_http/selenium
- status_code: HTTP status (if applicable)
- content_length: HTML size in bytes
- notes: Any special notes

**Output Format:** JSON

---

### FR5: Progress Tracking & Reporting
**Priority:** MEDIUM

**Description:** Отслеживание прогресса и генерация отчета

**Requirements:**
- Show progress: `[15/130] FL Columbia - downloading 3 URLs...`
- Track stats:
  - Total downloads attempted
  - Successful downloads
  - Failed downloads
  - By platform breakdown
  - By state breakdown
- Generate summary report: `collection_summary.json`

**Report Fields:**
```json
{
  "collection_date": "2025-12-31T...",
  "stats": {
    "total_downloads": 450,
    "successful": 412,
    "failed": 38,
    "by_platform": {
      "custom_gis": 87,
      "qpublic": 126,
      "propertytax": 98,
      ...
    },
    "by_state": {
      "fl_": 305,
      "az_": 67,
      "new jersey": 12,
      "new mexico": 28
    }
  },
  "results": [...]
}
```

---

## 🚫 Non-Functional Requirements

### NFR1: Performance
- **Download Speed:** 2-4 seconds delay per request (polite scraping)
- **Batch Processing:** Can process all 130 counties in ~2-4 hours
- **Memory:** < 2GB RAM usage
- **Disk Space:** ~500MB for 500 samples (avg 1MB per HTML)

### NFR2: Reliability
- **Error Handling:** Graceful handling of HTTP errors, timeouts
- **Resume Support:** Can resume from where it left off
- **Duplicate Prevention:** Skip already downloaded samples
- **Logging:** Detailed logs for debugging

### NFR3: Usability
- **CLI Interface:** Simple command-line arguments
- **Filters:** Can filter by state, county, platform
- **List Mode:** `--list` to show all available counties
- **Dry Run:** `--dry-run` to preview what will be downloaded

### NFR4: Maintainability
- **Modular Code:** Separate concerns (URL generation, download, metadata)
- **Configuration:** Platform-specific configs in separate file
- **Documentation:** Clear README with examples

---

## 🔗 Dependencies

### External Dependencies
- **Python 3.13+**
- **SeleniumBase** - for JavaScript-heavy pages
- **requests** - for simple HTTP downloads
- **BeautifulSoup4** - for HTML parsing (metadata extraction)
- **sbvirtualdisplay** - for headless Selenium

### Internal Dependencies
- **Tax Liens - Sources - Sheet1.csv** - must exist
- **Existing scraper** (`parser/taxlien-scraper-python/`) - для reference, не зависимость

---

## 📦 Deliverables

### Scripts
1. **platform_sample_urls.py** ✅ Done
   - `PlatformURLGenerator` class
   - Working example URLs for 14 counties

2. **download_samples.py** ✅ Done
   - `SampleDownloader` class
   - CLI interface
   - Progress tracking

3. **sample_collector.py** ✅ Done
   - Main orchestrator
   - Combines URL generation + download

### Documentation
4. **README.md**
   - Quick start guide
   - Usage examples
   - Troubleshooting

### Data
5. **samples_collected/** directory
   - Organized by state/county/platform
   - ~400-650 HTML files
   - Metadata JSON files

6. **collection_summary.json**
   - Statistics report
   - Coverage metrics

---

## 🎯 Success Metrics

### Coverage Metrics
- ✅ **130 counties cataloged** from CSV
- ✅ **14 counties with working example URLs** (FL: 12, AZ: 2)
- 🎯 **50+ counties with downloaded samples** (target)
- 🎯 **300+ HTML samples collected** (3 per county × 100 counties)

### Quality Metrics
- 🎯 **95%+ download success rate** for counties with working URLs
- 🎯 **100% metadata completeness** for successful downloads
- 🎯 **All platforms covered:** QPublic, Custom GIS, PropertyTax, Tyler, etc.

### Platform Coverage
| Platform | Counties in CSV | Working URLs | Target Samples |
|----------|----------------|--------------|----------------|
| QPublic (QP) | 27 | 6 | 18-30 |
| PropertyTax (PT) | 28 | 0 | 0-15 |
| Custom GIS | 6 | 6 | 18-30 |
| MyFloridaCounty (MF) | 17 | 3 | 9-15 |
| GovernMax (GM) | 3 | 3 | 9-15 |
| Tyler | ? | 2 | 6-10 |

---

## 🚀 Out of Scope

This tool is **NOT**:
- ❌ A production scraper (that's `taxlien-scraper-python/`)
- ❌ A parser (that's `platforms/*/parse_html()`)
- ❌ A database loader (that's MongoDB/PostgreSQL integration)
- ❌ A scheduler (that's Celery)

This tool **IS**:
- ✅ A one-time sample collection utility
- ✅ A testing data generator
- ✅ A platform research tool

---

## 🔄 Integration with Existing System

### Relationship to `taxlien-scraper-python/`

**Sample Collector** (this SDD):
- Purpose: Collect test data
- Scope: 3-5 samples per county
- Frequency: One-time or periodic updates
- Output: `samples_collected/` directory

**Production Scraper** (`taxlien-scraper-python/`):
- Purpose: Continuous data collection
- Scope: All parcels in county (thousands)
- Frequency: Daily/weekly via Celery beat
- Output: MongoDB (raw HTML) + PostgreSQL (parsed data)

**Workflow:**
```
1. Use Sample Collector to get HTML examples
     ↓
2. Develop parser using samples (offline testing)
     ↓
3. Add parser to Production Scraper
     ↓
4. Deploy Production Scraper with Celery
```

---

## ✅ Requirements Approval Checklist

Before moving to SPECIFICATIONS phase:

- [x] User stories defined with acceptance criteria
- [x] Functional requirements documented (FR1-FR5)
- [x] Non-functional requirements defined (NFR1-NFR4)
- [x] Dependencies identified
- [x] Success metrics established
- [x] Out of scope clearly defined
- [x] Integration with existing system explained
- [ ] **User approval:** Requirements reviewed and approved

---

**Status:** READY FOR REVIEW
**Next Phase:** SPECIFICATIONS
**Blocker:** None

---

## 🗺️ Related SDDs

- **[sdd-scraper-service](../sdd-scraper-service/)** - Main scraper service with 15 platform support
  - This SDD focuses on production scraping (ALL parcels)
  - Sample collector focuses on TEST DATA (3-5 samples per county)

- **[sdd-data-structure](../sdd-data-structure/)** - Database schemas
  - Sample collector saves raw HTML (no DB integration)
  - Production scraper saves to MongoDB + PostgreSQL

- **[sdd-data-pipeline](../sdd-data-pipeline/)** - ETL workflow
  - Sample collector is NOT part of ETL pipeline
  - It's a development tool for parser testing
