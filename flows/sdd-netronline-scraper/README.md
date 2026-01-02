# NetrOnline County Data Scraper

Automated scraper to collect county office URLs from [publicrecords.netronline.com](https://publicrecords.netronline.com) for all 50 US states.

## Overview

This tool scrapes county-level public office URLs (Assessor, Tax Collector, GIS, Clerk/Recorder, etc.) from NetrOnline and outputs them in a CSV format compatible with the existing `sources.csv`.

**Coverage:**
- All 50 US states
- ~3,000 counties nationwide
- ~8,000+ office URLs

**Output:**
- CSV file with timestamped filename: `netronline_counties_YYYY-MM-DD.csv`
- Format matches existing `sources.csv` for easy merging

---

## Quick Start

### Run Full Scrape (All 50 States)

```bash
python3 flows/sdd-netronline-scraper/netronline_scraper.py
```

**Expected:**
- Runtime: ~2 hours
- Output: ~3,000 counties
- Success rate: >95%

---

## Usage Examples

### Scrape Specific States

```bash
# Scrape only Florida
python3 netronline_scraper.py --states FL

# Scrape multiple states
python3 netronline_scraper.py --states FL NJ CO TX CA
```

### Test with Limited Counties

```bash
# Scrape only first 3 counties from Florida (for testing)
python3 netronline_scraper.py --states FL --limit 3

# Scrape 5 counties from each of 3 states (15 total)
python3 netronline_scraper.py --states FL NJ CO --limit 5
```

### Custom Output File

```bash
python3 netronline_scraper.py --output my_counties.csv
```

---

## Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--states` | List of state codes to scrape (default: all 50) | `--states FL NJ CO` |
| `--limit` | Limit counties per state (for testing) | `--limit 5` |
| `--output` | Output CSV filename (auto-adds timestamp) | `--output data.csv` |

---

## Output Format

The scraper generates a CSV file with the following columns (matching `sources.csv`):

```csv
state,county,Assessor / Appraser,Treasurer / Tax / Tax collector,Mapping / Gis,Recorder / County clerk,Board of taxation,Register of Deeds / Historic Aerials,N,RA,AP,TX,R,example
```

**Example Row:**
```csv
fl_,alachua,https://qpublic.schneidercorp.com/...,https://alachua.county-taxes.com/...,https://map.netronline.com/...,https://www.alachuacounty.us/...,,,,,,,,
```

**Field Mapping:**
- `state`: State code in `sources.csv` format (e.g., `fl_`, `new_jersey`)
- `county`: County name (lowercase)
- `Assessor / Appraser`: Property Assessor/Appraiser URL
- `Treasurer / Tax / Tax collector`: Tax Collector/Treasurer URL
- `Mapping / Gis`: GIS/Mapping portal URL
- `Recorder / County clerk`: Clerk/Recorder URL
- `Board of taxation`: Board of Taxation URL (NJ specific)
- Remaining columns: Empty (for compatibility with `sources.csv`)

---

## State Code Mapping

NetrOnline uses 2-letter state codes (FL, NJ, CO), but `sources.csv` uses a different format. The scraper automatically converts:

| NetrOnline | sources.csv | Example County |
|------------|-------------|----------------|
| FL | fl_ | fl_,alachua |
| NJ | new_jersey | new_jersey,bergen |
| NY | new_york | new_york,albany |
| CO | colorado | colorado,denver |
| TX | texas | texas,harris |

See the full mapping in `STATE_MAPPING` dict in [netronline_scraper.py](netronline_scraper.py:27-77).

---

## Office Categorization

The scraper categorizes offices by keyword matching:

| Category | Keywords | Example |
|----------|----------|---------|
| `assessor` | property appraiser, assessor, apprais | "Alachua Property Appraiser" |
| `tax` | tax collector, treasurer, tax | "Tax Collector" |
| `gis` | gis, mapping, map | "NETR Mapping and GIS" |
| `recorder` | clerk, recorder, deed, register | "Clerk / Recorder" |
| `taxation` | board of taxation | "Board of Taxation" (NJ) |
| `other` | (anything else) | Other offices |

---

## Performance

**Test Results:**
- Single county: ~2 seconds
- 15 counties (3 states × 5): ~45 seconds
- Full scrape (3,000 counties): ~2 hours

**Rate Limiting:**
- 1-2 second delay between counties (polite scraping)
- User-Agent header to identify as browser

**Resource Usage:**
- Memory: <100MB
- Disk: ~2MB CSV output
- Network: ~10KB per county

---

## Merging with Existing sources.csv

The scraper creates a **separate file** to preserve your existing data. To merge:

### Option 1: Manual Review
1. Open both CSVs in a spreadsheet program
2. Copy rows from `netronline_counties_YYYY-MM-DD.csv`
3. Paste into `sources.csv`
4. Remove duplicates, keeping your preferred data

### Option 2: Automated Merge (Future Enhancement)
Use the optional `merge_sources.py` script (not yet implemented) for intelligent merging:
- Keep existing non-empty fields
- Fill empty fields from NetrOnline
- Add new counties

---

## Troubleshooting

### Error: "No module named 'bs4'"

**Solution:** Install dependencies
```bash
pip3 install requests beautifulsoup4
```

### Error: "Connection timeout"

**Cause:** Network issues or NetrOnline downtime

**Solution:**
1. Wait a few minutes and retry
2. Check your internet connection
3. Try scraping specific states: `--states FL NJ`

### Low Success Rate (<90%)

**Possible causes:**
1. NetrOnline website structure changed
2. Rate limiting/blocking

**Solution:**
1. Check a few failed counties manually on NetrOnline
2. Update HTML parsing logic if structure changed
3. Increase delay between requests

### Empty Office URLs

**Expected behavior:** Some counties may not have all office types listed on NetrOnline.

**Solution:** This is normal. You can manually add missing URLs later or find them through other sources.

---

## Implementation Details

### HTML Structure

NetrOnline uses a `div-table` structure (not HTML `<table>`):

```html
<div class="div-table">
  <div class="div-table-row">
    <div class="div-table-col">Office Name</div>
    <div class="div-table-col"><a href="https://...">Link</a></div>
  </div>
</div>
```

The scraper:
1. Finds `div.div-table`
2. Extracts rows: `div.div-table-row`
3. Parses columns: `div.div-table-col`
4. Extracts office name and URL
5. Categorizes by keyword matching

### Error Handling

- **Network errors:** Caught and logged, scraping continues
- **Missing tables:** Returns empty offices dict
- **Invalid HTML:** Skipped gracefully
- **State errors:** Logged, moves to next state

---

## Examples

### Example 1: Quick Test (1 County)

```bash
$ python3 netronline_scraper.py --states FL --limit 1

NetrOnline County Scraper
================================================================================

[1/1] Scraping FL...
  Found 67 counties
    [1/1] alachua... 5 URLs

================================================================================
SCRAPE SUMMARY
================================================================================
Total counties: 1
Successful: 1
Failed: 0
Total URLs extracted: 5
Success rate: 100.0%

✓ Saved to flows/sdd-netronline-scraper/netronline_counties_2026-01-01.csv

Done! Scraped 1 counties
```

### Example 2: Multi-State Test (15 Counties)

```bash
$ python3 netronline_scraper.py --states FL NJ CO --limit 5

NetrOnline County Scraper
================================================================================

[1/3] Scraping FL...
  Found 67 counties
    [1/5] alachua... 5 URLs
    [2/5] baker... 5 URLs
    [3/5] bay... 5 URLs
    [4/5] bradford... 5 URLs
    [5/5] brevard... 5 URLs

[2/3] Scraping NJ...
  Found 21 counties
    [1/5] atlantic... 4 URLs
    [2/5] bergen... 4 URLs
    [3/5] burlington... 4 URLs
    [4/5] camden... 4 URLs
    [5/5] cape_may... 4 URLs

[3/3] Scraping CO...
  Found 64 counties
    [1/5] adams... 5 URLs
    [2/5] alamosa... 5 URLs
    [3/5] arapahoe... 5 URLs
    [4/5] archuleta... 5 URLs
    [5/5] baca... 4 URLs

================================================================================
SCRAPE SUMMARY
================================================================================
Total counties: 15
Successful: 15
Failed: 0
Total URLs extracted: 69
Success rate: 100.0%

✓ Saved to flows/sdd-netronline-scraper/netronline_counties_2026-01-01.csv

Done! Scraped 15 counties
```

---

## Dependencies

**Required:**
- Python 3.7+
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing

**Install:**
```bash
pip3 install requests beautifulsoup4
```

---

## Files

| File | Purpose |
|------|---------|
| `netronline_scraper.py` | Main scraper script (~300 lines) |
| `README.md` | This documentation |
| `netronline_counties_YYYY-MM-DD.csv` | Output data (generated) |

---

## Future Enhancements

1. **Merge Utility** - `merge_sources.py` for intelligent CSV merging
2. **Resume Support** - Save progress, resume from last state
3. **Retry Logic** - Exponential backoff for failed requests
4. **URL Validation** - Test if URLs are reachable (optional)
5. **Parallel Scraping** - Multi-threaded for faster collection

---

## License

This tool is part of the TAXLIEN.online project.

---

## Support

**Issues?** Check:
1. Dependencies installed: `pip3 list | grep -E 'requests|beautifulsoup4'`
2. Internet connection working
3. NetrOnline website accessible: https://publicrecords.netronline.com

**Still stuck?** Review error logs and check NetrOnline website structure manually.

---

**Last Updated:** 2026-01-01
**Author:** Claude Sonnet 4.5 (SDD Implementation)
