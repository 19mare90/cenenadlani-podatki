#!/usr/bin/env python3
"""Conservative SPAR catalogue change detector; never extracts or publishes prices."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

URL = 'https://www.spar.si/letak/katalog-4626'
STATE = Path('data/spar_catalog_state.json')
OUTPUT = Path('spar_monitor_result.json')

def main():
    result = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'sourceUrl': URL,
              'status': 'unavailable', 'changed': False,
              'note': 'Monitoring only: no prices are extracted, verified or published.'}
    try:
        req = Request(URL, headers={'User-Agent': 'CeneNaDlaniCatalogueMonitor/0.3 (+manual review; no price scraping)', 'Accept': 'text/html'})
        with urlopen(req, timeout=25) as resp:
            if resp.status != 200:
                raise RuntimeError(f'HTTP {resp.status}')
            raw = resp.read(2_000_001)
            if len(raw) > 2_000_000:
                raise RuntimeError('Page exceeded size limit')
            html = raw.decode('utf-8', errors='replace')
        if 'katalog' not in html.lower() and 'letak' not in html.lower():
            raise RuntimeError('Page does not resemble catalogue index')
        # Record catalogue index digest only; this is NOT a claim that a new catalogue exists.
        digest = hashlib.sha256(raw).hexdigest()
        previous = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
        changed = bool(previous.get('sha256') and previous['sha256'] != digest)
        result.update(status='ok', changed=changed, sha256=digest,
                      note='Index HTML changed; human must verify whether any catalogue or offer changed.' if changed else 'No detected index HTML change (or first baseline).')
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({'sha256': digest, 'sourceUrl': URL}, indent=2) + '\n', encoding='utf-8')
    except Exception as exc:
        result['error'] = str(exc)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    # Source outage is not treated as 'no offers'; preserve last known baseline.
    if result['status'] != 'ok':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
