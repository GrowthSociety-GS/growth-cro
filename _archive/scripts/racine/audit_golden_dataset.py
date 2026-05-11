#!/usr/bin/env python3
"""
Comprehensive audit of the Golden Dataset (data/golden/)
Checks spatial_v9.json and page.html for each site/pageType combination
Reports: completeness, totalHeight, content validation, error detection
"""

import os
import json
import sys
from pathlib import Path
from collections import defaultdict

# Project root
PROJECT_ROOT = Path(__file__).parent
GOLDEN_DIR = PROJECT_ROOT / "data" / "golden"

def check_spatial_file(spatial_path):
    """Read first 60 lines of spatial_v9.json and extract metadata"""
    if not spatial_path.exists():
        return None, "FILE_MISSING"

    try:
        with open(spatial_path, 'r', encoding='utf-8') as f:
            content = f.read()

        data = json.loads(content)
        return {
            'completeness': data.get('completeness', 0),
            'totalHeight': data.get('totalHeight', 0),
            'url': data.get('url', 'N/A'),
            'numSections': len(data.get('sections', [])),
            'numElements': len(data.get('elements', [])),
            'stagesCompleted': data.get('stagesCompleted', []),
            'errors': data.get('errors', []),
            'fileSize': spatial_path.stat().st_size,
        }, None
    except json.JSONDecodeError as e:
        return None, f"JSON_ERROR: {str(e)[:100]}"
    except Exception as e:
        return None, f"ERROR: {str(e)[:100]}"


def check_page_html(html_path):
    """Check if page.html exists and has real content (not error page)"""
    if not html_path.exists():
        return None, "FILE_MISSING"

    try:
        file_size = html_path.stat().st_size
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(5000)  # Read first 5000 chars

        # Check for error indicators
        error_indicators = ['403', 'ERROR', 'Forbidden', 'Access Denied', 'robots.txt']
        has_error = any(ind in content for ind in error_indicators)

        has_title = '<title>' in content
        has_body = '<body>' in content
        has_content = len(content) > 500 and file_size > 1000

        return {
            'fileSize': file_size,
            'hasTitle': has_title,
            'hasBody': has_body,
            'hasContent': has_content,
            'hasErrorIndicators': has_error,
        }, None
    except Exception as e:
        return None, f"ERROR: {str(e)[:100]}"


def classify_page(spatial_data, html_data):
    """Classify page as VALID, DEGRADED, or BLOCKED"""
    if spatial_data is None and html_data is None:
        return "MISSING", "Both spatial_v9.json and page.html missing"

    if spatial_data is None:
        return "MISSING", "spatial_v9.json missing"

    if html_data is None:
        return "MISSING", "page.html missing"

    # Check for blocked pages
    if html_data.get('hasErrorIndicators', False):
        return "BLOCKED", "Error indicators in HTML (403, Forbidden, etc.)"

    if spatial_data['totalHeight'] < 300 and spatial_data['numElements'] < 20:
        return "BLOCKED", "Very small page (height < 300px, elements < 20)"

    # Check completeness
    completeness = spatial_data.get('completeness', 0)
    if completeness < 0.5:
        return "DEGRADED", f"Low completeness: {completeness:.2f}"

    if completeness < 0.8:
        return "DEGRADED", f"Partial completeness: {completeness:.2f}"

    # Check for HTML content
    if not html_data.get('hasContent', False):
        return "DEGRADED", "HTML file too small (< 1KB)"

    # Check for errors in spatial data
    if spatial_data.get('errors', []):
        error_str = "; ".join(spatial_data['errors'][:2])
        return "DEGRADED", f"Errors detected: {error_str}"

    return "VALID", "Real content captured"


def audit_golden_dataset():
    """Main audit function"""
    if not GOLDEN_DIR.exists():
        print(f"ERROR: Golden directory not found: {GOLDEN_DIR}")
        return

    results = defaultdict(lambda: defaultdict(dict))
    summary = {"VALID": [], "DEGRADED": [], "BLOCKED": [], "MISSING": []}

    # Walk through all site/pageType directories
    for site_dir in sorted(GOLDEN_DIR.iterdir()):
        if not site_dir.is_dir() or site_dir.name.startswith('_'):
            continue

        site_label = site_dir.name

        for page_dir in sorted(site_dir.iterdir()):
            if not page_dir.is_dir():
                continue

            page_type = page_dir.name

            # Check files
            spatial_file = page_dir / "spatial_v9.json"
            html_file = page_dir / "page.html"

            spatial_data, spatial_err = check_spatial_file(spatial_file)
            html_data, html_err = check_page_html(html_file)

            # Classify
            status, reason = classify_page(spatial_data, html_data)

            # Store results
            entry = {
                'status': status,
                'reason': reason,
                'spatial': spatial_data or {'error': spatial_err},
                'html': html_data or {'error': html_err},
            }
            results[site_label][page_type] = entry
            summary[status].append(f"{site_label}/{page_type}")

    return results, summary


def print_audit_report(results, summary):
    """Print formatted audit report"""
    print("=" * 100)
    print("GOLDEN DATASET AUDIT REPORT")
    print("=" * 100)
    print()

    # Summary statistics
    total_pages = sum(len(pages) for pages in results.values())
    print(f"SUMMARY:")
    print(f"  Total pages checked: {total_pages}")
    print(f"  VALID (real content):    {len(summary['VALID']):3d}")
    print(f"  DEGRADED (partial/suspect): {len(summary['DEGRADED']):3d}")
    print(f"  BLOCKED (403/error):     {len(summary['BLOCKED']):3d}")
    print(f"  MISSING (no files):      {len(summary['MISSING']):3d}")
    print()

    # Detailed breakdown by status
    for status in ['VALID', 'DEGRADED', 'BLOCKED', 'MISSING']:
        if not summary[status]:
            continue

        print("-" * 100)
        print(f"{status} PAGES ({len(summary[status])}):")
        print("-" * 100)

        for site_label in sorted(set(item.split('/')[0] for item in summary[status])):
            print(f"\n{site_label.upper()}:")
            site_pages = [item.split('/')[1] for item in summary[status] if item.startswith(site_label + '/')]

            for page_type in sorted(site_pages):
                entry = results[site_label][page_type]
                spatial = entry['spatial']
                html = entry['html']

                reason = entry['reason']

                # Print details
                print(f"  {page_type:20s} | {reason}")

                if spatial and 'error' not in spatial:
                    comp = spatial.get('completeness', 'N/A')
                    height = spatial.get('totalHeight', 'N/A')
                    elems = spatial.get('numElements', 'N/A')
                    sects = spatial.get('numSections', 'N/A')
                    print(f"                         | spatial: completeness={comp:.2f}, height={height}px, elements={elems}, sections={sects}")

                if html and 'error' not in html:
                    size = html.get('fileSize', 'N/A')
                    print(f"                         | html: {size:,} bytes")

    print()
    print("=" * 100)
    print("END AUDIT REPORT")
    print("=" * 100)


if __name__ == '__main__':
    results, summary = audit_golden_dataset()
    print_audit_report(results, summary)

    # Exit with error code if any BLOCKED or too many MISSING
    blocked_count = len(summary['BLOCKED']) + len(summary['MISSING'])
    if blocked_count > 5:
        print(f"\nWARNING: {blocked_count} pages with issues (BLOCKED or MISSING)")
        sys.exit(1)
