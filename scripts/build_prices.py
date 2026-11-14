import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data' / 'reviewed_offers.json'
PRODUCTS = ROOT / 'data' / 'products.json'
OUTPUT = ROOT / 'prices.json'
ALLOWED = {
    'mercator.si', 'spar.si', 'tus.si', 'lidl.si', 'hofer.si',
    'eurospin.si', 'trgovinejager.com', 'jager.si'
}

def valid_source(url):
    try:
        u = urlparse(url)
        host = (u.hostname or '').lower()
        return u.scheme == 'https' and any(host == domain or host.endswith('.' + domain) for domain in ALLOWED)
    except (TypeError, ValueError):
        return False

def main():
    today = datetime.now(ZoneInfo("Europe/Ljubljana")).date()
    data = json.loads(INPUT.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('offers'), list):
        raise ValueError('Input must be object with offers array')
    output = []
    seen = set()
    for idx, o in enumerate(data['offers'], 1):
        if not isinstance(o, dict):
            print(f'SKIP {idx}: not an object')
            continue
        try:
            required = ['id','name','quantity','store','unitPrice','validUntil','checkedAt','sourceUrl','region','loyalty']
            if any(not isinstance(o.get(k), str) or not o[k].strip() for k in required):
                raise ValueError('missing required text')
            if type(o.get('price')) not in (float, int) or not (0 < o['price'] < 100000):
                raise ValueError('invalid price')
            if o['id'] in seen:
                raise ValueError('duplicate id')
            checked = date.fromisoformat(o['checkedAt'])
            until = date.fromisoformat(o['validUntil'])
            if checked > today or checked < today - timedelta(days=7):
                raise ValueError('check date not within last 7 days')
            start = date.fromisoformat(o['validFrom']) if 'validFrom' in o else checked
            if start > today or until < max(today, checked, start):
                raise ValueError('expired or inconsistent validity')
            if not valid_source(o['sourceUrl']):
                raise ValueError('source must be official HTTPS merchant domain')
            if o.get('publishable', True) is not True or o.get('reviewStatus') != 'approved' or not isinstance(o.get('reviewedBy'), str) or not o['reviewedBy'].strip():
                raise ValueError('not explicitly reviewed')
            # Review is a human assertion; this script cannot independently verify a merchant's live price.
            output.append({k: o[k] for k in required + ['price']})
            seen.add(o['id'])
        except (ValueError, TypeError) as exc:
            print(f'SKIP {idx} ({o.get("id", "unknown")}): {exc}')
    catalog = json.loads(PRODUCTS.read_text(encoding='utf-8'))['products']
    products = {}
    fields = ('store', 'name', 'quantity', 'sourceUrl')
    for item in catalog + output:
        if not isinstance(item, dict) or any(
            not isinstance(item.get(field), str) or not item[field].strip()
            for field in fields
        ) or not valid_source(item['sourceUrl']):
            continue
        key = tuple(item[field].strip().casefold() for field in fields[:3])
        products[key] = {field: item[field] for field in fields}
    result = {'offers': output, 'products': list(products.values())}
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Published {len(output)} reviewed offers; {len(data["offers"])-len(output)} excluded')

if __name__ == '__main__':
    main()
