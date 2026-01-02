#!/usr/bin/env python3
"""
Sample HTML Collector for Tax Lien Property Data
Collects 3-5 sample HTML pages from each county source in sources.csv

Platform Support:
- QPublic (Schneider Corp)
- PropertyTax (.county-taxes.com)
- Custom GIS systems
- Tyler Technologies
- MyFloridaCounty
- GovernMax
- Beacon
"""

import csv
import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

try:
    from seleniumbase import SB
    from sbvirtualdisplay import Display
    from bs4 import BeautifulSoup
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("WARNING: SeleniumBase not available. Install with: pip install seleniumbase")

import requests


class SampleCollector:
    """Collects sample HTML pages from county tax websites"""

    def __init__(self, sources_csv: str, output_dir: str = "samples_collected"):
        self.sources_csv = sources_csv
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Load counties from CSV
        self.counties = self._load_counties()

        # Statistics
        self.stats = {
            'total_counties': 0,
            'successful': 0,
            'failed': 0,
            'total_samples': 0,
            'by_platform': {}
        }

    def _load_counties(self) -> List[Dict]:
        """Load county data from CSV"""
        counties = []
        with open(self.sources_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['state'] and row['county']:
                    counties.append(row)
        return counties

    def identify_platform(self, county: Dict) -> str:
        """Identify which platform the county uses"""
        assessor_url = county.get('Assessor / Appraser', '').lower()
        tax_url = county.get('Treasurer / Tax / Tax collector', '').lower()
        ap_indicator = county.get('AP', '')
        tx_indicator = county.get('TX', '')

        # QPublic/Beacon (Schneider Corp)
        if 'qpublic.schneidercorp.com' in assessor_url or 'beacon.schneidercorp.com' in assessor_url:
            return 'qpublic'
        elif ap_indicator == 'QP':
            return 'qpublic'

        # PropertyTax (county-taxes.com)
        if 'county-taxes.com' in tax_url:
            return 'propertytax'
        elif tx_indicator == 'PT':
            return 'propertytax'

        # Tyler Technologies
        if 'tylerhost.net' in assessor_url or 'tylerhost.net' in tax_url:
            return 'tyler'

        # Custom GIS
        if '/gis/' in assessor_url.lower() or 'floridapa.com' in assessor_url:
            return 'custom_gis'
        elif ap_indicator == 'GIS':
            return 'custom_gis'

        # GovernMax
        if 'governmax.com' in assessor_url or 'governmax.com' in tax_url:
            return 'governmax'
        elif tx_indicator == 'GM':
            return 'governmax'

        # MyFloridaCounty
        if 'myfloridacounty.com' in assessor_url or 'myfloridacounty.com' in tax_url:
            return 'myfloridacounty'
        elif county.get('R', '') == 'MF':
            return 'myfloridacounty'

        # Generic/Unknown
        return 'unknown'

    def get_sample_parcel_ids(self, county: Dict, platform: str) -> List[str]:
        """Get sample parcel IDs for the county"""
        # Use example parcel ID from CSV if available
        example_parcel = county.get('example', '').strip()
        if example_parcel:
            # Handle comma-separated parcel IDs
            parcels = [p.strip() for p in example_parcel.split(',') if p.strip()]
            return parcels

        # Platform-specific sample parcel IDs
        # (In production, these would be discovered by crawling)
        county_name = county['county'].lower()
        state = county['state'].lower().replace('_', '')

        # Return empty list - will need manual parcel IDs or discovery
        return []

    def collect_samples_simple_http(self, county: Dict, platform: str, parcel_ids: List[str]) -> int:
        """Collect samples using simple HTTP requests (for non-JS sites)"""
        samples_collected = 0

        state = county['state']
        county_name = county['county']
        output_path = self.output_dir / state / county_name / platform
        output_path.mkdir(parents=True, exist_ok=True)

        assessor_url = county.get('Assessor / Appraser', '')
        tax_url = county.get('Treasurer / Tax / Tax collector', '')

        # Collect assessor/property pages
        if assessor_url and parcel_ids:
            for parcel_id in parcel_ids:
                try:
                    # This is a simplified example - real URLs vary by platform
                    url = f"{assessor_url}?parcel={parcel_id}"

                    response = requests.get(url, timeout=30, headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
                    })

                    if response.status_code == 200:
                        filename = f"assessor_{parcel_id.replace('/', '_')}.html"
                        filepath = output_path / filename
                        filepath.write_text(response.text, encoding='utf-8')
                        samples_collected += 1
                        print(f"  ✓ Saved {filename}")
                        time.sleep(random.uniform(1, 3))  # Polite delay

                except Exception as e:
                    print(f"  ✗ Failed to fetch assessor for {parcel_id}: {e}")

        return samples_collected

    def collect_samples_selenium(self, county: Dict, platform: str, parcel_ids: List[str]) -> int:
        """Collect samples using Selenium (for JS-heavy sites)"""
        if not SELENIUM_AVAILABLE:
            print("  ⚠ Selenium not available, skipping")
            return 0

        samples_collected = 0
        state = county['state']
        county_name = county['county']
        output_path = self.output_dir / state / county_name / platform
        output_path.mkdir(parents=True, exist_ok=True)

        assessor_url = county.get('Assessor / Appraser', '')

        try:
            with Display(visible=False, size=(1920, 1080)):
                with SB(uc=True, headless2=True) as sb:
                    for parcel_id in parcel_ids:
                        try:
                            # Navigate to parcel page
                            # (This is simplified - real implementation varies by platform)
                            url = f"{assessor_url}?parcel={parcel_id}"
                            sb.uc_open_with_reconnect(url, 3)
                            sb.sleep(2)

                            # Get page source
                            html = sb.get_page_source()

                            # Save HTML
                            filename = f"assessor_{parcel_id.replace('/', '_')}.html"
                            filepath = output_path / filename
                            filepath.write_text(html, encoding='utf-8')

                            # Save screenshot
                            screenshot_file = f"assessor_{parcel_id.replace('/', '_')}.png"
                            sb.save_screenshot(str(output_path / screenshot_file))

                            samples_collected += 1
                            print(f"  ✓ Saved {filename} + screenshot")

                            time.sleep(random.uniform(2, 4))

                        except Exception as e:
                            print(f"  ✗ Failed for {parcel_id}: {e}")

        except Exception as e:
            print(f"  ✗ Selenium failed: {e}")

        return samples_collected

    def collect_county_samples(self, county: Dict, max_samples: int = 5) -> Dict:
        """Collect sample pages for a single county"""
        state = county['state']
        county_name = county['county']
        platform = self.identify_platform(county)

        print(f"\n{'='*80}")
        print(f"Collecting samples: {state}{county_name} (Platform: {platform})")
        print(f"{'='*80}")

        # Get sample parcel IDs
        parcel_ids = self.get_sample_parcel_ids(county, platform)

        if not parcel_ids:
            print(f"  ⚠ No sample parcel IDs available for {state}{county_name}")
            print(f"  Assessor URL: {county.get('Assessor / Appraser', 'N/A')}")
            print(f"  Tax URL: {county.get('Treasurer / Tax / Tax collector', 'N/A')}")

            # Save metadata anyway
            self._save_county_metadata(county, platform, [])
            return {'county': f"{state}{county_name}", 'platform': platform, 'samples': 0, 'status': 'no_parcel_ids'}

        # Limit samples
        parcel_ids = parcel_ids[:max_samples]

        # Choose collection method based on platform
        if platform in ['custom_gis', 'qpublic', 'tyler']:
            # Use Selenium for JS-heavy sites
            samples_collected = self.collect_samples_selenium(county, platform, parcel_ids)
        else:
            # Try simple HTTP first
            samples_collected = self.collect_samples_simple_http(county, platform, parcel_ids)

        # Save metadata
        self._save_county_metadata(county, platform, parcel_ids)

        result = {
            'county': f"{state}{county_name}",
            'platform': platform,
            'samples': samples_collected,
            'status': 'success' if samples_collected > 0 else 'failed'
        }

        return result

    def _save_county_metadata(self, county: Dict, platform: str, parcel_ids: List[str]):
        """Save metadata about the county and collection attempt"""
        state = county['state']
        county_name = county['county']
        output_path = self.output_dir / state / county_name
        output_path.mkdir(parents=True, exist_ok=True)

        metadata = {
            'county': f"{state}{county_name}",
            'state': state,
            'county_name': county_name,
            'platform': platform,
            'assessor_url': county.get('Assessor / Appraser', ''),
            'tax_url': county.get('Treasurer / Tax / Tax collector', ''),
            'gis_url': county.get('Mapping / Gis', ''),
            'recorder_url': county.get('Recorder / County clerk', ''),
            'sample_parcel_ids': parcel_ids,
            'collection_date': datetime.now().isoformat(),
            'indicators': {
                'RA': county.get('RA', ''),
                'AP': county.get('AP', ''),
                'TX': county.get('TX', ''),
                'R': county.get('R', ''),
            }
        }

        metadata_file = output_path / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def run(self, states_filter: Optional[List[str]] = None, limit: Optional[int] = None):
        """Run sample collection for all counties"""
        print(f"\n{'='*80}")
        print(f"TAX LIEN SAMPLE COLLECTOR")
        print(f"{'='*80}")
        print(f"Total counties in CSV: {len(self.counties)}")
        print(f"Output directory: {self.output_dir}")

        # Filter by states if specified
        counties_to_process = self.counties
        if states_filter:
            counties_to_process = [c for c in self.counties if c['state'] in states_filter]
            print(f"Filtering to states: {states_filter}")
            print(f"Counties to process: {len(counties_to_process)}")

        # Apply limit
        if limit:
            counties_to_process = counties_to_process[:limit]
            print(f"Limiting to first {limit} counties")

        # Process each county
        results = []
        for i, county in enumerate(counties_to_process, 1):
            print(f"\nProgress: {i}/{len(counties_to_process)}")

            result = self.collect_county_samples(county)
            results.append(result)

            # Update stats
            self.stats['total_counties'] += 1
            self.stats['total_samples'] += result['samples']

            platform = result['platform']
            if platform not in self.stats['by_platform']:
                self.stats['by_platform'][platform] = {'counties': 0, 'samples': 0}
            self.stats['by_platform'][platform]['counties'] += 1
            self.stats['by_platform'][platform]['samples'] += result['samples']

            if result['status'] == 'success':
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1

        # Print summary
        self._print_summary(results)

        # Save summary
        self._save_summary(results)

    def _print_summary(self, results: List[Dict]):
        """Print collection summary"""
        print(f"\n{'='*80}")
        print(f"COLLECTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total counties processed: {self.stats['total_counties']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Total samples collected: {self.stats['total_samples']}")

        print(f"\n{'='*80}")
        print(f"BY PLATFORM")
        print(f"{'='*80}")
        for platform, data in sorted(self.stats['by_platform'].items()):
            print(f"{platform:20} {data['counties']} counties, {data['samples']} samples")

    def _save_summary(self, results: List[Dict]):
        """Save collection summary"""
        summary = {
            'collection_date': datetime.now().isoformat(),
            'stats': self.stats,
            'results': results
        }

        summary_file = self.output_dir / 'collection_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Collect sample HTML pages from county tax websites')
    parser.add_argument('--csv', default='flows/sdd-sample-collector/sources.csv',
                        help='Path to sources CSV file')
    parser.add_argument('--output', default='samples_collected',
                        help='Output directory for collected samples')
    parser.add_argument('--states', nargs='+',
                        help='Filter to specific states (e.g., fl_ az_)')
    parser.add_argument('--limit', type=int,
                        help='Limit number of counties to process')
    parser.add_argument('--samples-per-county', type=int, default=5,
                        help='Number of samples to collect per county')

    args = parser.parse_args()

    collector = SampleCollector(args.csv, args.output)
    collector.run(states_filter=args.states, limit=args.limit)


if __name__ == '__main__':
    main()
