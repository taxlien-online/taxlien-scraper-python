# Sample HTML Collector

Automated tool to collect HTML samples from county tax websites for parser development and testing.

## Quick Start

### List Available Counties

```bash
python3 download_samples.py --list
```

### Download Samples for Specific Counties

```bash
# Single county
python3 download_samples.py --counties fl_polk

# Multiple counties
python3 download_samples.py --counties fl_polk fl_sarasota fl_orange

# All available counties
python3 download_samples.py
```

### Using Selenium (for JavaScript-heavy pages)

```bash
# Note: Requires Xvfb on Linux for headless mode
python3 download_samples.py --counties fl_columbia --selenium
```

## Output Structure

Samples are saved to `samples_collected/` with the following structure:

```
samples_collected/
├── collection_summary.json          # Overall statistics
├── fl_/
│   ├── polk/
│   │   ├── assessor_222602000000013090.html
│   │   ├── assessor_222602000000013090_meta.json
│   │   ├── gis_222602000000013090.html
│   │   ├── gis_222602000000013090_meta.json
│   │   ├── tax_222602000000013090.html
│   │   └── tax_222602000000013090_meta.json
│   │
│   ├── sarasota/
│   └── orange/
│
└── az_/
    └── ...
```

### File Types

- **HTML files**: `{page_type}_{parcel_id}.html` - Downloaded web pages
- **Metadata**: `{page_type}_{parcel_id}_meta.json` - Download metadata (URL, date, platform, etc.)
- **Screenshots**: `{page_type}_{parcel_id}.png` - Only for Selenium downloads (when available)
- **Summary**: `collection_summary.json` - Collection statistics

## Available Counties

Currently configured with working examples for **14 counties**:

### Florida (12 counties)
- FL Alachua (QPublic)
- FL Columbia (Custom GIS)
- FL Union (Custom GIS)
- FL Dixie (QPublic)
- FL Gadsden (QPublic/Beacon)
- FL Polk (Custom) ✅ Working
- FL Sarasota (Custom) ✅ Working
- FL Suwannee (Custom GIS)
- FL Taylor (QPublic)
- FL Orange (Custom) ✅ Working
- FL Lafayette (Custom GIS)
- FL Okeechobee (Custom GIS)

### Arizona (2 counties)
- AZ Coconino (Tyler Technologies)
- AZ Pima (Custom)

✅ = Successfully downloaded samples (HTTP method)

## Platforms Supported

- **QPublic** (Schneider Corp) - Requires Selenium
- **Custom GIS** (floridapa.com) - Requires Selenium
- **PropertyTax** (county-taxes.com) - HTTP
- **Custom** county sites - HTTP
- **Tyler Technologies** - Requires Selenium
- **GovernMax** - Requires Selenium
- **MyFloridaCounty** - Requires Selenium

## Requirements

### Python Packages

```bash
pip3 install requests
pip3 install seleniumbase sbvirtualdisplay  # For Selenium downloads
```

### For Selenium (Linux only)

```bash
# Install Xvfb for headless browser
sudo apt-get install xvfb
```

**Note**: Selenium headless mode requires Xvfb, which is only available on Linux. On macOS, Selenium downloads will fail with "No such file or directory: 'Xvfb'" error. HTTP downloads work on all platforms.

## Command-Line Options

```bash
python3 download_samples.py [OPTIONS]

Options:
  --output DIR         Output directory (default: samples_collected)
  --counties COUNTY... Specific counties to download (e.g., fl_polk fl_union)
  --selenium           Use Selenium for all downloads (slower but handles JS)
  --list               List all available counties and exit
```

## Examples

### Test on One County

```bash
python3 download_samples.py --counties fl_polk --output test_samples
```

### Download from Multiple States

```bash
python3 download_samples.py --counties fl_polk fl_sarasota fl_orange
```

### Full Collection

```bash
python3 download_samples.py --output samples_collected
```

## Collection Summary

After running, check `samples_collected/collection_summary.json` for statistics:

```json
{
  "download_date": "2026-01-01T09:21:09.357783",
  "stats": {
    "total_downloads": 65,
    "successful": 9,
    "failed": 56,
    "by_platform": {
      "custom": 9
    },
    "by_state": {
      "fl": 9
    },
    "by_page_type": {
      "assessor": 3,
      "gis": 2,
      "tax": 3,
      "tangible": 1
    }
  }
}
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'requests'"

**Solution**: Install dependencies
```bash
pip3 install --user requests
```

### Issue: "Selenium not available"

**Solution**: Install seleniumbase
```bash
pip3 install --user seleniumbase sbvirtualdisplay
```

### Issue: "No such file or directory: 'Xvfb'"

**Cause**: Selenium headless mode requires Xvfb (Linux only)

**Solution**: Use HTTP downloads only (don't use `--selenium` flag), or run on a Linux system.

### Issue: HTTP 403 / 522 errors

**Cause**: Website blocking requests or timeout

**Solutions**:
- Some websites block automated requests
- Timeouts can occur for slow servers
- Try again later or use a different county

### Issue: "Page may contain error message"

**Cause**: HTML validation detected error keywords

**Solution**: Inspect the HTML file manually to verify if it's an error page or valid data.

## Development

### Adding New Counties

Edit `platform_sample_urls.py` and add to the `working_examples` dict:

```python
'fl_new_county': {
    'platform': 'custom_gis',
    'assessor': 'http://newcounty.floridapa.com/gis/',
    'tax': 'http://newcounty-taxcollector.com/',
    'sample_parcels': ['PARCEL001', 'PARCEL002'],
    'working_urls': {
        'assessor_example': 'http://newcounty.floridapa.com/gis/?pin=PARCEL001'
    }
},
```

## Related Files

- `platform_sample_urls.py` - URL generation with platform-specific patterns
- `download_samples.py` - Main downloader with HTTP + Selenium support
- `sample_collector.py` - Alternative orchestrator (reads from sources.csv)

## License

Part of taxlien-scraper-python project.
