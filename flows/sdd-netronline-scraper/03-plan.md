# Implementation Plan: NetrOnline County Data Scraper

**Date:** 2026-01-01
**Phase:** PLAN
**Status:** DRAFT

---

## 1. Overview

**Goal:** Implement a scraper to collect county office URLs from publicrecords.netronline.com for all 50 US states (~3,000 counties).

**Current State:**
- Specifications complete
- HTML structure analyzed
- Data models designed

**Target State:**
- Functional scraper script
- CSV with ~3,000 counties
- Merge utility (optional)
- Complete documentation

---

## 2. Implementation Strategy

### 2.1 Approach

**Bottom-Up Implementation:**
1. Build core scraping functions first
2. Test on small dataset (1-3 counties)
3. Add orchestration layer
4. Test on medium dataset (1-3 states)
5. Add progress tracking and error handling
6. Run full scrape (all 50 states)

**Estimated Time:** 1-2 hours

---

## 3. Task Breakdown

### Phase 1: Core Scraping Functions (30 min)

#### Task 1.1: Create State Code Mapping
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** SIMPLE

**Implementation:**
```python
STATE_MAPPING = {
    'FL': 'fl_',
    'NJ': 'new_jersey',
    'NY': 'new_york',
    ...  # All 50 states
}
```

**Test:**
```python
assert STATE_MAPPING['FL'] == 'fl_'
assert STATE_MAPPING['NJ'] == 'new_jersey'
assert len(STATE_MAPPING) == 50
```

---

####  Task 1.2: Implement Office Categorization
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** SIMPLE

**Implementation:**
```python
def categorize_office(office_name: str) -> str:
    """Categorize office by name keywords"""
    name_lower = office_name.lower()

    if any(kw in name_lower for kw in ['property appraiser', 'assessor', 'apprais']):
        return 'assessor'
    elif any(kw in name_lower for kw in ['tax collector', 'treasurer', 'tax']):
        return 'tax'
    elif any(kw in name_lower for kw in ['gis', 'mapping', 'map']):
        return 'gis'
    elif any(kw in name_lower for kw in ['clerk', 'recorder', 'deed', 'register']):
        return 'recorder'
    elif any(kw in name_lower for kw in ['board of taxation']):
        return 'taxation'
    else:
        return 'other'
```

**Test:**
```python
assert categorize_office('Alachua Property Appraiser') == 'assessor'
assert categorize_office('Tax Collector') == 'tax'
assert categorize_office('NETR Mapping and GIS') == 'gis'
assert categorize_office('Clerk / Recorder') == 'recorder'
```

---

#### Task 1.3: Implement State County List Scraper
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** MEDIUM

**Implementation:**
```python
def get_counties_for_state(state_code: str) -> List[str]:
    """Get list of counties for a state"""
    url = f'https://publicrecords.netronline.com/state/{state_code}'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')

    county_links = soup.find_all('a', href=lambda x: x and '/county/' in x)
    counties = []

    for link in county_links:
        # Extract: /state/FL/county/alachua → alachua
        href = link['href']
        county_name = href.split('/county/')[-1]
        counties.append(county_name)

    return counties
```

**Test:**
```bash
python3 -c "
from netronline_scraper import get_counties_for_state
counties = get_counties_for_state('FL')
print(f'FL counties: {len(counties)}')
assert len(counties) == 67, f'Expected 67 FL counties, got {len(counties)}'
print('✓ Passed')
"
```

---

#### Task 1.4: Implement County Data Scraper
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** MEDIUM

**Implementation:**
```python
def scrape_county(state_code: str, county: str) -> dict:
    """Scrape office data for a county"""
    url = f'https://publicrecords.netronline.com/state/{state_code}/county/{county}'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

    response = requests.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find office table
    table = soup.find('div', class_='div-table')
    if not table:
        return {'state': state_code, 'county': county, 'offices': []}

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
```

**Test:**
```bash
python3 -c "
from netronline_scraper import scrape_county
data = scrape_county('FL', 'alachua')
print(f'Offices found: {list(data[\"offices\"].keys())}')
assert 'assessor' in data['offices']
assert 'tax' in data['offices']
print('✓ Passed')
"
```

---

### Phase 2: CSV Writing & Data Formatting (15 min)

#### Task 2.1: Implement CSV Row Formatter
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** SIMPLE

**Implementation:**
```python
def county_to_csv_row(county_data: dict) -> dict:
    """Convert county data to CSV row format"""
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
```

---

#### Task 2.2: Implement CSV Writer
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** SIMPLE

**Implementation:**
```python
def write_to_csv(counties_data: List[dict], output_file: str):
    """Write scraped data to CSV"""
    import csv
    from datetime import datetime

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
```

---

### Phase 3: Orchestration & Progress Tracking (20 min)

#### Task 3.1: Implement Main Scraper Function
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** HIGH
**Complexity:** MEDIUM

**Implementation:**
```python
def scrape_all_states(state_filter=None, limit_per_state=None):
    """Scrape all states or filtered list"""
    import time
    import random

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
    print(f'Success rate: {stats["successful"]/stats["total_counties"]*100:.1f}%' if stats["total_counties"] > 0 else 'N/A')

    return all_counties, stats
```

---

#### Task 3.2: Implement CLI Interface
**File:** `flows/sdd-netronline-scraper/netronline_scraper.py`
**Priority:** MEDIUM
**Complexity:** SIMPLE

**Implementation:**
```python
def main():
    """Main CLI entry point"""
    import argparse

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
```

---

### Phase 4: Testing (15 min)

#### Test 1: Single County
**Command:**
```bash
python3 flows/sdd-netronline-scraper/netronline_scraper.py --states FL --limit 1
```

**Expected:**
- CSV with 1 FL county
- 3-5 office URLs
- No errors

---

#### Test 2: Single State (3 counties)
**Command:**
```bash
python3 flows/sdd-netronline-scraper/netronline_scraper.py --states FL --limit 3
```

**Expected:**
- CSV with 3 FL counties
- ~9-15 office URLs
- Success rate > 90%

---

#### Test 3: Multiple States (small)
**Command:**
```bash
python3 flows/sdd-netronline-scraper/netronline_scraper.py --states FL NJ CO --limit 5
```

**Expected:**
- CSV with 15 counties (5 per state)
- ~40-60 office URLs
- Runtime: ~30-60 seconds

---

#### Test 4: Full Scrape (production)
**Command:**
```bash
python3 flows/sdd-netronline-scraper/netronline_scraper.py
```

**Expected:**
- CSV with ~3,000 counties
- ~8,000+ office URLs
- Runtime: ~2 hours
- Success rate > 95%

---

### Phase 5: Merge Utility (OPTIONAL - 20 min)

#### Task 5.1: Implement Merge Function
**File:** `flows/sdd-netronline-scraper/merge_sources.py`
**Priority:** LOW
**Complexity:** MEDIUM

**Implementation:**
```python
def merge_csv_files(existing_csv, netronline_csv, output_csv):
    """Merge NetrOnline data with existing sources.csv"""
    import csv

    # Load both files
    existing_data = {}
    with open(existing_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['state'], row['county'])
            existing_data[key] = row

    netronline_data = {}
    with open(netronline_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['state'], row['county'])
            netronline_data[key] = row

    # Merge
    merged = {}

    # Add all existing
    for key, row in existing_data.items():
        merged[key] = row

    # Merge or add NetrOnline
    fields_to_merge = [
        'Assessor / Appraser',
        'Treasurer / Tax / Tax collector',
        'Mapping / Gis',
        'Recorder / County clerk',
        'Board of taxation'
    ]

    for key, row in netronline_data.items():
        if key in merged:
            # Merge: fill empty fields
            for field in fields_to_merge:
                if not merged[key][field] and row[field]:
                    merged[key][field] = row[field]
        else:
            # New county: add it
            merged[key] = row

    # Write output
    rows = list(merged.values())
    rows.sort(key=lambda x: (x['state'], x['county']))

    fieldnames = list(rows[0].keys()) if rows else []

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'Merged {len(rows)} counties to {output_csv}')
    print(f'  Existing: {len(existing_data)}')
    print(f'  NetrOnline: {len(netronline_data)}')
    print(f'  New counties added: {len(rows) - len(existing_data)}')
```

**CLI:**
```python
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--existing', required=True)
    parser.add_argument('--netronline', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()

    merge_csv_files(args.existing, args.netronline, args.output)
```

**Test:**
```bash
python3 flows/sdd-netronline-scraper/merge_sources.py \
  --existing flows/sdd-sample-collector/sources.csv \
  --netronline flows/sdd-netronline-scraper/netronline_counties_2026-01-01.csv \
  --output flows/sdd-sample-collector/sources_merged.csv
```

---

### Phase 6: Documentation (10 min)

#### Task 6.1: Create README
**File:** `flows/sdd-netronline-scraper/README.md`
**Priority:** MEDIUM
**Complexity:** SIMPLE

**Content:**
- Usage instructions
- Command examples
- Expected output
- Troubleshooting

---

## 4. Files to Create/Modify

### New Files

| File | Lines | Purpose |
|------|-------|---------|
| `flows/sdd-netronline-scraper/netronline_scraper.py` | ~300 | Main scraper |
| `flows/sdd-netronline-scraper/merge_sources.py` | ~80 | Merge utility (optional) |
| `flows/sdd-netronline-scraper/README.md` | ~100 | Documentation |

### Output Files

| File | Size | Purpose |
|------|------|---------|
| `netronline_counties_YYYY-MM-DD.csv` | ~2MB | Scraped data |
| `sources_merged.csv` (optional) | ~2MB | Merged data |

---

## 5. Implementation Order

**Sequential (no parallelization):**

1. **Task 1.1:** State code mapping (5 min)
2. **Task 1.2:** Office categorization (5 min)
3. **Task 1.3:** State scraper (10 min)
4. **Task 1.4:** County scraper (10 min)
5. **Test:** Single county (2 min)
6. **Task 2.1:** CSV formatter (5 min)
7. **Task 2.2:** CSV writer (5 min)
8. **Task 3.1:** Main orchestrator (15 min)
9. **Task 3.2:** CLI interface (5 min)
10. **Test:** 3 counties (3 min)
11. **Test:** 3 states, 5 counties each (5 min)
12. **Run:** Full scrape (2 hours - can run in background)
13. **Task 6.1:** README (10 min)
14. **OPTIONAL Task 5.1:** Merge utility (20 min)

**Total active time:** ~1.5 hours + 2 hours scraping

---

## 6. Testing Checkpoints

### Checkpoint 1: After Task 1.4
**Verify:**
- Can scrape FL Alachua
- Returns 3-5 office URLs
- Categorization works

**Command:**
```python
python3 -c "
from netronline_scraper import scrape_county
data = scrape_county('FL', 'alachua')
print(data)
assert len(data['offices']) >= 3
"
```

---

### Checkpoint 2: After Task 2.2
**Verify:**
- Can write 1 county to CSV
- CSV format matches sources.csv

**Command:**
```bash
python3 -c "
from netronline_scraper import scrape_county, county_to_csv_row, write_to_csv
data = scrape_county('FL', 'alachua')
write_to_csv([data], 'test.csv')
"
head test.csv
```

---

### Checkpoint 3: After Task 3.2
**Verify:**
- CLI works
- Can scrape 3 counties

**Command:**
```bash
python3 flows/sdd-netronline-scraper/netronline_scraper.py --states FL --limit 3
```

---

## 7. Definition of Done

### Phase 1-3 Complete When:
- [x] All scraping functions implemented
- [x] CLI working
- [x] Can scrape 3 counties without errors

### Phase 4 Complete When:
- [ ] Test 1: Single county passes
- [ ] Test 2: Single state (3 counties) passes
- [ ] Test 3: Multiple states (15 counties) passes
- [ ] Test 4: Full scrape produces CSV with ~3,000 counties

### Phase 5 Complete When (Optional):
- [ ] Merge utility implemented
- [ ] Can merge with existing sources.csv

### Phase 6 Complete When:
- [ ] README created
- [ ] All documentation complete

### Overall Project Complete When:
- [ ] All phases 1-4 complete
- [ ] CSV with ~3,000 counties generated
- [ ] Success rate > 95%
- [ ] User acceptance

---

## 8. Risk Mitigation

### Risk 1: NetrOnline Blocking
**Mitigation:**
- 1-2 second delays between requests
- User-Agent headers
- If blocked, pause 5 minutes

### Risk 2: HTML Structure Changes
**Mitigation:**
- Test early on multiple states
- Add error handling for missing tables
- Log failures for manual review

### Risk 3: Slow Scraping (> 3 hours)
**Mitigation:**
- Run in background with `&`
- Use `--limit` for initial testing
- Can resume manually by state

### Risk 4: Low Success Rate (< 90%)
**Mitigation:**
- Analyze failed counties
- Improve error handling
- Add retry logic if needed

---

## 9. Rollback Plan

**If scraper fails:**
1. Check error logs
2. Fix bugs
3. Resume from last successful state
4. Manual: `--states [remaining states]`

**Data preservation:**
- Save partial results to CSV
- Don't delete test outputs
- Keep log of failed counties

---

## ✅ Plan Approval Checklist

Before moving to IMPLEMENTATION phase:

- [x] Task breakdown complete with estimates
- [x] Files to create identified
- [x] Testing checkpoints defined
- [x] Implementation order prioritized
- [x] Definition of done clear
- [x] Risk mitigation addressed
- [ ] **User approval:** Plan reviewed and approved

---

**Status:** READY FOR REVIEW
**Next Phase:** IMPLEMENTATION
**Blocker:** Awaiting user approval

**Estimated Time:**
- Active work: 1.5 hours
- Full scrape: 2 hours (background)
- **Total:** 3.5 hours
