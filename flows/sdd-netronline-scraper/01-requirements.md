# Requirements: NetrOnline County Data Scraper

**Date:** 2026-01-01
**Phase:** REQUIREMENTS
**Purpose:** Scrape county data from publicrecords.netronline.com to expand coverage to all 50 US states

---

## 📊 Problem Statement

### Current Situation

**Existing County Coverage:**
- `sources.csv` has ~130 counties (mostly FL and AZ)
- Manual data entry is slow and error-prone
- Limited geographic coverage

**Sample Collector Limitation:**
- Only 14 counties have working example URLs
- Only 9 samples collected (3 counties successful)
- Missing data for 3,000+ US counties

### What We Need

**NetrOnline Scraper** - Automated tool to scrape county office URLs from publicrecords.netronline.com:

1. **Input:** List of 50 US state codes (FL, NJ, CO, MD, etc.)
2. **Process:**
   - Scrape county list for each state
   - Extract office URLs (Assessor, Tax, GIS, Recorder)
   - Normalize and validate data
3. **Output:** CSV file with ~3,000 counties and their office URLs

---

## 👥 User Stories

### Story 1: Expand Geographic Coverage
**As a** data analyst
**I want** to have office URLs for all US counties
**So that** I can collect property data nationwide

**Acceptance Criteria:**
- ✅ All 50 states scraped
- ✅ ~3,000 counties cataloged
- ✅ At least 2 office URLs per county (Assessor + Tax minimum)
- ✅ Data saved to CSV format compatible with existing tools

---

### Story 2: Automated Data Collection
**As a** developer
**I want** to automate county URL collection
**So that** I don't have to manually research 3,000+ counties

**Acceptance Criteria:**
- ✅ One command scrapes all states
- ✅ Can filter specific states (e.g., only scrape FL, TX, CA)
- ✅ Progress tracking shows current state/county
- ✅ Completed in < 1 hour for all 50 states

---

### Story 3: Merge with Existing Data
**As a** data manager
**I want** to merge NetrOnline data with existing sources.csv
**So that** I preserve manual research while adding new coverage

**Acceptance Criteria:**
- ✅ Creates separate output file (netronline_counties.csv)
- ✅ Can merge with existing sources.csv intelligently
- ✅ Fill empty fields from NetrOnline
- ✅ Keep existing non-empty fields
- ✅ Add new counties not in sources.csv

---

## 🎯 Functional Requirements

### FR1: State List Scraping
**Priority:** HIGH

**Description:** Scrape county lists for all 50 US states

**Requirements:**
- Access `https://publicrecords.netronline.com/state/{STATE}` for each state
- Extract all county names listed
- Handle variations (e.g., "St. Johns" vs "St Johns")
- Detect total county count per state

**Inputs:**
- List of 50 state codes: [FL, AL, AK, AZ, AR, CA, CO, CT, DE, GA, HI, ID, IL, IN, IA, KS, KY, LA, ME, MD, MA, MI, MN, MS, MO, MT, NE, NV, NH, NJ, NM, NY, NC, ND, OH, OK, OR, PA, RI, SC, SD, TN, TX, UT, VT, VA, WA, WV, WI, WY]
- Optional: state filter (e.g., only FL, TX, CA)

**Outputs:**
- List of (state, county) tuples
- Expected: ~3,000 counties total

---

### FR2: County Office URL Extraction
**Priority:** HIGH

**Description:** For each county, extract URLs for public offices

**Requirements:**
- Access `https://publicrecords.netronline.com/state/{STATE}/county/{COUNTY}`
- Extract URLs for:
  - **Property Appraiser/Assessor** (highest priority)
  - **Tax Collector/Treasurer** (highest priority)
  - **GIS/Mapping** (high priority)
  - **Clerk/Recorder** (high priority)
  - Any other available offices (medium priority)
- Categorize URLs by office type
- Handle missing URLs gracefully

**Inputs:**
- State code (e.g., "FL")
- County name (e.g., "Alachua")

**Outputs:**
- Dictionary with office URLs:
```python
{
    'state': 'FL',
    'county': 'Alachua',
    'assessor_url': 'https://...',
    'tax_url': 'https://...',
    'gis_url': 'https://...',
    'recorder_url': 'https://...',
    'other_offices': [...]
}
```

---

### FR3: Data Normalization
**Priority:** MEDIUM

**Description:** Normalize scraped data to match sources.csv format

**Requirements:**
- State codes: lowercase with underscore (e.g., "fl_", "new_jersey")
- County names: lowercase
- URL validation: check if URL is reachable (optional, slow)
- Remove duplicates
- Sort by state, then county

**CSV Columns:**
```csv
state,county,Assessor / Appraser,Treasurer / Tax / Tax collector,Mapping / Gis,Recorder / County clerk,Board of taxation,Register of Deeds / Historic Aerials,N,RA,AP,TX,R,example
```

---

### FR4: Output File Generation
**Priority:** HIGH

**Description:** Save scraped data to CSV file

**Requirements:**
- Save to `flows/sdd-netronline-scraper/netronline_counties.csv`
- UTF-8 encoding
- Compatible with sources.csv format
- Include scrape date in filename (e.g., `netronline_counties_2026-01-01.csv`)

**Output Format:**
- CSV with headers matching sources.csv
- One row per county
- Empty columns if data not available from NetrOnline

---

### FR5: Merge Utility (Optional Enhancement)
**Priority:** LOW (Nice to have)

**Description:** Merge NetrOnline data with existing sources.csv

**Requirements:**
- Read both files
- For each county:
  - If county doesn't exist in sources.csv → add it
  - If county exists:
    - Keep existing non-empty fields
    - Fill empty fields from NetrOnline
- Save to new file: `sources_merged.csv`

**Merge Logic:**
```python
for county in netronline_data:
    if county not in sources_csv:
        # Add new county
        sources_csv.append(county)
    else:
        # Merge fields
        for field in fields:
            if not sources_csv[county][field] and netronline_data[county][field]:
                sources_csv[county][field] = netronline_data[county][field]
```

---

### FR6: Progress Tracking & Logging
**Priority:** MEDIUM

**Description:** Show progress during scraping

**Requirements:**
- Print current state being scraped
- Print current county being processed
- Show stats: `[125/3,000] FL Alachua - Extracted 4 URLs`
- Log errors to file: `scrape_errors.log`
- Generate summary report at end

**Example Output:**
```
NetrOnline County Scraper
================================================================================
Scraping 50 states...

[1/50] Alabama - 67 counties
  [1/67] Autauga County - 3 URLs found
  [2/67] Baldwin County - 4 URLs found
  ...

Summary:
  Total counties scraped: 3,143
  Total URLs extracted: 9,429
  Success rate: 98.5%
  Errors: 47 counties (see scrape_errors.log)
```

---

## 🚫 Non-Functional Requirements

### NFR1: Performance
- **Scrape Speed:** ~1-2 seconds per county (polite delays)
- **Total Time:** ~1 hour for 3,000 counties
- **Memory:** < 500MB RAM usage
- **Disk Space:** ~5MB for CSV output

### NFR2: Reliability
- **Error Handling:** Continue on errors, don't crash
- **Retry Logic:** Retry failed requests 3 times with backoff
- **Resume Support:** Can resume from last state/county
- **Rate Limiting:** Polite delays (1-2 seconds between requests)

### NFR3: Maintainability
- **Modular Code:** Separate scraper, parser, writer
- **Configuration:** State list in config file
- **Logging:** Structured logging for debugging
- **Documentation:** README with examples

---

## 🔗 Dependencies

### External Dependencies
- **Python 3.13+**
- **requests** - HTTP requests
- **BeautifulSoup4** - HTML parsing
- **pandas** (optional) - CSV manipulation

### Internal Dependencies
- **sources.csv** - Existing county data (for merge)
- NetrOnline website availability (external dependency)

---

## 📦 Deliverables

### Scripts
1. **netronline_scraper.py**
   - Main scraper script
   - CLI interface
   - Progress tracking

2. **merge_sources.py** (Optional)
   - Merge utility
   - Conflict resolution

### Data
3. **netronline_counties.csv**
   - Scraped data for all counties
   - ~3,000 rows

4. **scrape_summary.json**
   - Statistics report
   - Error log

### Documentation
5. **README.md**
   - Usage guide
   - Examples
   - Troubleshooting

---

## 🎯 Success Metrics

### Coverage Metrics
- 🎯 **50 states scraped** (100% coverage)
- 🎯 **3,000+ counties cataloged** (95%+ of US counties)
- 🎯 **8,000+ office URLs extracted** (avg 2.5 URLs per county)

### Quality Metrics
- 🎯 **95%+ success rate** (counties with at least 1 URL)
- 🎯 **90%+ completeness** (counties with 2+ URLs)
- 🎯 **All URLs valid** (HTTP 200 response - optional check)

### Platform Coverage
Expected office types:
- Property Assessor/Appraiser: ~90% of counties
- Tax Collector: ~85% of counties
- GIS/Mapping: ~60% of counties
- Clerk/Recorder: ~70% of counties

---

## 🚀 Out of Scope

This scraper is **NOT**:
- ❌ A production data pipeline (one-time scrape)
- ❌ A real-time data sync tool
- ❌ A URL validator (doesn't test if URLs work)
- ❌ A parser (doesn't extract data from office websites)

This scraper **IS**:
- ✅ A one-time data collection tool
- ✅ A county catalog generator
- ✅ A foundation for sample collector expansion

---

## 🔄 Integration with Sample Collector

### Current Workflow
1. Manual research → sources.csv (130 counties)
2. Manual URL entry → platform_sample_urls.py (14 counties)
3. Run sample collector → 9 HTML samples

### New Workflow with NetrOnline Scraper
1. **Run NetrOnline scraper** → netronline_counties.csv (3,000 counties)
2. **Merge with sources.csv** → sources_merged.csv
3. **Update platform_sample_urls.py** → Add counties from merged CSV
4. **Run sample collector** → 300+ HTML samples (target)

### Benefits
- 3,000+ counties available (vs 130)
- Automated data collection (vs manual)
- Comprehensive US coverage (vs FL/AZ only)

---

## ✅ Requirements Approval Checklist

Before moving to SPECIFICATIONS phase:

- [x] User stories defined with acceptance criteria
- [x] Functional requirements documented (FR1-FR6)
- [x] Non-functional requirements defined (NFR1-NFR3)
- [x] Dependencies identified
- [x] Success metrics established
- [x] Out of scope clearly defined
- [x] Integration with sample collector explained
- [x] User confirmed data extraction preferences
- [ ] **User approval:** Requirements reviewed and approved

---

**Status:** READY FOR REVIEW
**Next Phase:** SPECIFICATIONS
**Blocker:** Awaiting user approval

---

## 📝 Open Questions

1. **State Codes:** Should we use 2-letter codes (FL) or full names? → **Decision: Use sources.csv format (fl_, new_jersey)**

2. **URL Validation:** Should we test if URLs are reachable? → **Decision: No (too slow, ~1 hour becomes ~5 hours)**

3. **Update Frequency:** How often to re-scrape NetrOnline? → **Decision: One-time scrape, manual re-run as needed**

4. **Error Threshold:** What % of failed counties is acceptable? → **Decision: < 5% failure rate**
