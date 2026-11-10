#!/usr/bin/env python3
"""Capture exact-part live JLCPCB page records, excluding related products.

Usage: python3 scripts/review_jlcpcb.py C81598 C41430893 ... --output FILE
Stock is a dated observation, never a reservation or lifecycle guarantee.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.request


def review(code):
    url = 'https://jlcpcb.com/partdetail/' + code
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(request, timeout=90) as response:
        html = response.read().decode()
        resolved = response.url
    chunks = [json.loads(s) for s in re.findall(
        r'self\.__next_f\.push\((\[.*?\])\)</script>', html)]
    text = ''.join(c[1] for c in chunks if len(c) > 1 and isinstance(c[1], str))
    decoder = json.JSONDecoder()
    objects = []
    for match in re.finditer(r'\{', text):
        try:
            obj, _ = decoder.raw_decode(text[match.start():])
        except ValueError:
            continue
        if isinstance(obj, dict) and obj.get('componentCode') == code:
            objects.append(obj)
    info = next(o for o in objects if 'assemblyMode' in o and 'componentModelEn' in o)
    stock = next(o for o in objects if 'overseasStockCount' in o and 'isBuyComponent' in o)
    return dict(code=code, fetched_utc=datetime.now(timezone.utc).isoformat(),
                url=url, resolved_url=resolved, component=info, inventory=stock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('codes', nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    def capture(code):
        try:
            result = review(code)
            print(code, result['component']['componentModelEn'],
                  result['inventory']['overseasStockCount'], flush=True)
            return result
        except Exception as error:
            print(code, str(error), flush=True)
            return dict(code=code, error=str(error))
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(capture, args.codes))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + '\n')
    if any('error' in r for r in results):
        raise SystemExit('Some catalog lookups failed; see output')


if __name__ == '__main__':
    main()
