#!/usr/bin/env python3
"""
Merge NetrOnline County Data with Existing sources.csv

This script merges the NetrOnline scraped data with your existing sources.csv file.

Merge Strategy:
- Keep existing non-empty fields from sources.csv
- Fill empty fields with data from NetrOnline
- Add new counties that don't exist in sources.csv

Usage:
    python3 merge_sources.py --existing sources.csv --netronline netronline_counties.csv --output merged.csv
"""

import csv
import argparse
from typing import Dict, Tuple


def load_csv(filename: str) -> Dict[Tuple[str, str], Dict]:
    """
    Load CSV file into dictionary keyed by (state, county).

    Args:
        filename: Path to CSV file

    Returns:
        Dictionary with (state, county) tuples as keys
    """
    data = {}

    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row['state'], row['county'])
            data[key] = row

    return data


def merge_csv_files(existing_csv: str, netronline_csv: str, output_csv: str):
    """
    Merge NetrOnline data with existing sources.csv.

    Strategy:
    - For existing counties: keep non-empty fields, fill empty fields from NetrOnline
    - For new counties: add them from NetrOnline

    Args:
        existing_csv: Path to existing sources.csv
        netronline_csv: Path to NetrOnline scraped data
        output_csv: Path to output merged CSV
    """
    print(f'Loading existing data from: {existing_csv}')
    existing_data = load_csv(existing_csv)
    print(f'  → Loaded {len(existing_data)} counties')

    print(f'\nLoading NetrOnline data from: {netronline_csv}')
    netronline_data = load_csv(netronline_csv)
    print(f'  → Loaded {len(netronline_data)} counties')

    # Fields to merge (URL fields only)
    fields_to_merge = [
        'Assessor / Appraser',
        'Treasurer / Tax / Tax collector',
        'Mapping / Gis',
        'Recorder / County clerk',
        'Board of taxation',
        'Register of Deeds / Historic Aerials'
    ]

    # Start with existing data
    merged = {}
    for key, row in existing_data.items():
        merged[key] = row.copy()

    # Track statistics
    stats = {
        'existing_kept': 0,
        'new_added': 0,
        'fields_filled': 0,
        'fields_kept': 0
    }

    # Merge NetrOnline data
    print('\nMerging data...')
    for key, netronline_row in netronline_data.items():
        if key in merged:
            # County exists - merge fields
            stats['existing_kept'] += 1

            for field in fields_to_merge:
                existing_value = merged[key].get(field, '').strip()
                netronline_value = netronline_row.get(field, '').strip()

                if not existing_value and netronline_value:
                    # Fill empty field with NetrOnline data
                    merged[key][field] = netronline_value
                    stats['fields_filled'] += 1
                elif existing_value:
                    # Keep existing non-empty field
                    stats['fields_kept'] += 1
        else:
            # New county - add it
            merged[key] = netronline_row.copy()
            stats['new_added'] += 1

    # Sort by state, then county
    sorted_rows = sorted(merged.values(), key=lambda x: (x['state'], x['county']))

    # Write merged data
    print(f'\nWriting merged data to: {output_csv}')

    # Collect all unique fieldnames from all rows
    all_fieldnames = set()
    for row in sorted_rows:
        all_fieldnames.update(row.keys())

    # Order fieldnames: standard fields first, then extras
    standard_fields = [
        'state', 'county', 'Assessor / Appraser',
        'Treasurer / Tax / Tax collector', 'Mapping / Gis',
        'Recorder / County clerk', 'Board of taxation',
        'Register of Deeds / Historic Aerials',
        'N', 'RA', 'AP', 'TX', 'R', 'example'
    ]

    # Start with standard fields that exist
    fieldnames = [f for f in standard_fields if f in all_fieldnames]

    # Add any extra fields not in standard list
    extra_fields = sorted(all_fieldnames - set(standard_fields))
    fieldnames.extend(extra_fields)

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        # Write rows, filling missing fields with empty strings
        for row in sorted_rows:
            # Ensure all fieldnames exist in row
            complete_row = {field: row.get(field, '') for field in fieldnames}
            writer.writerow(complete_row)

    # Print summary
    print('\n' + '=' * 80)
    print('MERGE SUMMARY')
    print('=' * 80)
    print(f'Total counties in merged file: {len(merged)}')
    print(f'\nBreakdown:')
    print(f'  Existing counties kept: {stats["existing_kept"]}')
    print(f'  New counties added: {stats["new_added"]}')
    print(f'\nField updates:')
    print(f'  Empty fields filled from NetrOnline: {stats["fields_filled"]}')
    print(f'  Non-empty fields kept from existing: {stats["fields_kept"]}')
    print('\n✓ Merge complete!')


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Merge NetrOnline data with existing sources.csv'
    )
    parser.add_argument(
        '--existing',
        required=True,
        help='Path to existing sources.csv file'
    )
    parser.add_argument(
        '--netronline',
        required=True,
        help='Path to NetrOnline scraped CSV file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output merged CSV file'
    )

    args = parser.parse_args()

    print('NetrOnline CSV Merge Utility')
    print('=' * 80)

    merge_csv_files(args.existing, args.netronline, args.output)


if __name__ == '__main__':
    main()
