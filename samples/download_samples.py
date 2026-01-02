#!/usr/bin/env python3
"""
Download Sample HTML Pages from County Tax Websites

Downloads real HTML pages using the working URLs from platform_sample_urls.py
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

try:
    from seleniumbase import SB
    from sbvirtualdisplay import Display
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  SeleniumBase not available. Install with: pip install seleniumbase")

import requests
from platform_sample_urls import PlatformURLGenerator, SampleURL


class SampleDownloader:
    """Download HTML samples from county websites"""

    def __init__(self, output_dir: str = "samples_downloaded"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.url_generator = PlatformURLGenerator()

        # Statistics
        self.stats = {
            'total_downloads': 0,
            'successful': 0,
            'failed': 0,
            'by_platform': {},
            'by_state': {},
            'by_page_type': {}
        }

        # Download history to avoid duplicates
        self.downloaded = set()

    def download_url_simple(self, sample_url: SampleURL, output_path: Path) -> bool:
        """Download using simple HTTP request"""
        try:
            print(f"  📥 GET {sample_url.url[:80]}...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            response = requests.get(sample_url.url, headers=headers, timeout=30, allow_redirects=True)

            if response.status_code == 200:
                # Basic validation - check HTML contains expected content
                if len(response.text) < 500:
                    print(f"  ⚠️  Suspiciously small HTML ({len(response.text)} bytes)")

                if 'error' in response.text.lower() or 'not found' in response.text.lower():
                    print(f"  ⚠️  Page may contain error message")

                # Save HTML
                html_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}.html"
                html_file.write_text(response.text, encoding='utf-8')

                # Save metadata
                meta = {
                    'url': sample_url.url,
                    'parcel_id': sample_url.parcel_id,
                    'page_type': sample_url.page_type,
                    'platform': sample_url.platform,
                    'county': sample_url.county,
                    'state': sample_url.state,
                    'download_date': datetime.now().isoformat(),
                    'method': 'simple_http',
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'notes': sample_url.notes
                }

                meta_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}_meta.json"
                with open(meta_file, 'w') as f:
                    json.dump(meta, f, indent=2)

                print(f"  ✅ Saved {html_file.name} ({len(response.text):,} bytes)")
                return True

            else:
                print(f"  ❌ HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False

    def download_url_selenium(self, sample_url: SampleURL, output_path: Path) -> bool:
        """Download using Selenium for JavaScript-heavy pages"""
        if not SELENIUM_AVAILABLE:
            print("  ⚠️  Selenium not available, skipping")
            return False

        try:
            print(f"  🌐 Selenium GET {sample_url.url[:80]}...")

            with Display(visible=False, size=(1920, 1080)):
                with SB(uc=True, headless2=True) as sb:
                    # Open URL
                    sb.uc_open_with_reconnect(sample_url.url, reconnect_time=3)

                    # Wait for page to load
                    time.sleep(3)

                    # Scroll to load dynamic content
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(1)
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)

                    # Get page source
                    html = sb.get_page_source()

                    # Save HTML
                    html_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}.html"
                    html_file.write_text(html, encoding='utf-8')

                    # Save screenshot
                    screenshot_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}.png"
                    sb.save_screenshot(str(screenshot_file))

                    # Save metadata
                    meta = {
                        'url': sample_url.url,
                        'parcel_id': sample_url.parcel_id,
                        'page_type': sample_url.page_type,
                        'platform': sample_url.platform,
                        'county': sample_url.county,
                        'state': sample_url.state,
                        'download_date': datetime.now().isoformat(),
                        'method': 'selenium',
                        'content_length': len(html),
                        'screenshot': screenshot_file.name,
                        'notes': sample_url.notes
                    }

                    meta_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}_meta.json"
                    with open(meta_file, 'w') as f:
                        json.dump(meta, f, indent=2)

                    print(f"  ✅ Saved {html_file.name} + screenshot ({len(html):,} bytes)")
                    return True

        except Exception as e:
            print(f"  ❌ Selenium error: {e}")
            return False

    def download_county_samples(self, state: str, county: str, use_selenium: bool = False) -> Dict:
        """Download all sample URLs for a county"""
        print(f"\n{'='*80}")
        print(f"📍 {state.upper()} - {county.title()}")
        print(f"{'='*80}")

        # Get sample URLs
        sample_urls = self.url_generator.get_sample_urls(state, county, num_samples=3)

        if not sample_urls:
            print(f"  ⚠️  No sample URLs available for {state}_{county}")
            return {'county': f"{state}_{county}", 'downloads': 0, 'status': 'no_urls'}

        print(f"  Found {len(sample_urls)} URLs to download")

        # Create output directory
        output_path = self.output_dir / state / county
        output_path.mkdir(parents=True, exist_ok=True)

        # Download each URL
        downloads_successful = 0
        downloads_failed = 0

        for i, sample_url in enumerate(sample_urls, 1):
            print(f"\n  [{i}/{len(sample_urls)}] {sample_url.page_type.upper()}")

            # Check if file already exists on disk
            html_file = output_path / f"{sample_url.page_type}_{sample_url.parcel_id.replace('/', '_')}.html"
            if html_file.exists():
                print(f"  ⏭️  Already exists: {html_file.name}")
                self.downloaded.add(hash(sample_url.url))
                continue

            # Also check in-memory hash
            url_hash = hash(sample_url.url)
            if url_hash in self.downloaded:
                print(f"  ⏭️  Already downloaded in this session")
                continue

            # Choose download method
            if use_selenium or sample_url.platform in ['custom_gis', 'qpublic']:
                success = self.download_url_selenium(sample_url, output_path)
            else:
                success = self.download_url_simple(sample_url, output_path)

            # Update stats
            self.downloaded.add(url_hash)
            self.stats['total_downloads'] += 1

            if success:
                downloads_successful += 1
                self.stats['successful'] += 1

                # Update stats by platform
                if sample_url.platform not in self.stats['by_platform']:
                    self.stats['by_platform'][sample_url.platform] = 0
                self.stats['by_platform'][sample_url.platform] += 1

                # Update stats by state
                if state not in self.stats['by_state']:
                    self.stats['by_state'][state] = 0
                self.stats['by_state'][state] += 1

                # Update stats by page type
                if sample_url.page_type not in self.stats['by_page_type']:
                    self.stats['by_page_type'][sample_url.page_type] = 0
                self.stats['by_page_type'][sample_url.page_type] += 1

            else:
                downloads_failed += 1
                self.stats['failed'] += 1

            # Polite delay
            time.sleep(random.uniform(2, 4))

        print(f"\n  📊 Results: {downloads_successful} successful, {downloads_failed} failed")

        return {
            'county': f"{state}_{county}",
            'downloads': downloads_successful,
            'failed': downloads_failed,
            'status': 'success' if downloads_successful > 0 else 'failed'
        }

    def run(self, counties: Optional[List[str]] = None, use_selenium: bool = False):
        """Run downloader for specified counties or all available"""
        print(f"\n{'='*80}")
        print(f"🚀 SAMPLE DOWNLOADER")
        print(f"{'='*80}")
        print(f"Output directory: {self.output_dir}")
        print(f"Selenium enabled: {use_selenium and SELENIUM_AVAILABLE}")

        # Get counties to process
        if counties:
            counties_to_process = counties
        else:
            counties_to_process = self.url_generator.get_all_counties_with_examples()

        print(f"Counties to process: {len(counties_to_process)}")

        # Process each county
        results = []
        for i, county_key in enumerate(counties_to_process, 1):
            state, county = county_key.split('_', 1)

            print(f"\n{'='*80}")
            print(f"Progress: {i}/{len(counties_to_process)}")
            print(f"{'='*80}")

            result = self.download_county_samples(state, county, use_selenium=use_selenium)
            results.append(result)

            # Save progress after each county
            self._save_summary(results)

        # Final summary
        self._print_summary(results)

    def _print_summary(self, results: List[Dict]):
        """Print download summary"""
        print(f"\n{'='*80}")
        print(f"📊 DOWNLOAD SUMMARY")
        print(f"{'='*80}")
        print(f"Total downloads attempted: {self.stats['total_downloads']}")
        print(f"Successful: {self.stats['successful']}")
        print(f"Failed: {self.stats['failed']}")

        if self.stats['by_platform']:
            print(f"\n{'='*80}")
            print(f"BY PLATFORM")
            print(f"{'='*80}")
            for platform, count in sorted(self.stats['by_platform'].items(), key=lambda x: -x[1]):
                print(f"  {platform:20} {count:3} samples")

        if self.stats['by_state']:
            print(f"\n{'='*80}")
            print(f"BY STATE")
            print(f"{'='*80}")
            for state, count in sorted(self.stats['by_state'].items()):
                print(f"  {state:10} {count:3} samples")

        if self.stats['by_page_type']:
            print(f"\n{'='*80}")
            print(f"BY PAGE TYPE")
            print(f"{'='*80}")
            for page_type, count in sorted(self.stats['by_page_type'].items(), key=lambda x: -x[1]):
                print(f"  {page_type:20} {count:3} samples")

    def _save_summary(self, results: List[Dict]):
        """Save download summary"""
        summary = {
            'download_date': datetime.now().isoformat(),
            'stats': self.stats,
            'results': results
        }

        summary_file = self.output_dir / 'download_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Download sample HTML pages from county tax websites')
    parser.add_argument('--output', default='samples_downloaded',
                        help='Output directory for downloaded samples')
    parser.add_argument('--counties', nargs='+',
                        help='Specific counties to download (e.g., fl_columbia fl_union)')
    parser.add_argument('--selenium', action='store_true',
                        help='Use Selenium for all downloads (slower but handles JavaScript)')
    parser.add_argument('--list', action='store_true',
                        help='List all available counties and exit')

    args = parser.parse_args()

    downloader = SampleDownloader(args.output)

    if args.list:
        print("Counties with working sample URLs:")
        for county_key in downloader.url_generator.get_all_counties_with_examples():
            state, county = county_key.split('_', 1)
            print(f"  - {county_key:30} ({state.upper()} {county.title()})")
        return

    downloader.run(counties=args.counties, use_selenium=args.selenium)


if __name__ == '__main__':
    main()
