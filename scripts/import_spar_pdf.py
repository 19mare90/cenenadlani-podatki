#!/usr/bin/env python3
"""Extract possible SPAR catalogue prices for manual review; never publish directly."""
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import fitz

TOKEN = re.compile(r'(?<![\d.,])(?:\d{1,3}[,.]\d{2}|\d{3,4})(?![\d.,])')
EXCLUDE = re.compile(r'^(?:redna cena|PC\b|cena za|CENEJE|GRATIS|PRIHRANITE|DO TORKA|OD SREDE|\d+\s*%|\d+\s*točk)', re.I)

def price(token):
    if ',' in token or '.' in token:
        return round(float(token.replace(',', '.')), 2)
    return int(token[:-2]) + int(token[-2:]) / 100

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/spar_prices.json'))
    parser.add_argument('--source-url', default='https://www.spar.si/letak/katalog-4626')
    args = parser.parse_args()
    doc = fitz.open(args.pdf)
    candidates = []
    for page_index, page in enumerate(doc):
        blocks = [(fitz.Rect(b[:4]), b[4].strip()) for b in page.get_text('blocks', sort=True)
                  if len(b) >= 5 and isinstance(b[4], str) and b[4].strip()]
        for rect, content in blocks:
            if EXCLUDE.match(content.strip()) or 'redna cena' in content.lower() or 'cena za kg' in content.lower():
                continue
            for match in TOKEN.finditer(content):
                token = match.group()
                value = price(token)
                if not 0 < value <= 999:
                    continue
                near = sorted(blocks, key=lambda b: abs(b[0].x0 - rect.x0) + abs(b[0].y0 - rect.y0))[:6]
                context = ' | '.join(t.replace('\n', ' ')[:110] for _, t in near)
                candidates.append({
                    'id': f'spar-4626-p{page_index+1:02d}-{len(candidates)+1:04d}',
                    'page': page_index + 1, 'priceCandidateEur': value,
                    'rawToken': token, 'context': context[:450],
                    'productName': None, 'unit': None, 'cardRequired': None,
                    'validFrom': None, 'validUntil': None,
                    'reviewStatus': 'needs_manual_review',
                    'reviewReasons': ['product_price_pairing_unverified',
                                      'promotion_terms_unverified', 'validity_unverified']
                })
    result = {
        'schemaVersion': 1, 'catalogue': 'SPAR 46/26',
        'sourceUrl': args.source_url, 'sourceFile': args.pdf.name,
        'processedAt': datetime.now(timezone.utc).isoformat(),
        'pageCount': len(doc), 'publicationStatus': 'draft_not_for_app',
        'notice': 'Candidates are NOT verified offers. Never publish without manual review.',
        'candidateCount': len(candidates), 'candidates': candidates
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Extracted {len(candidates)} UNVERIFIED candidates from {len(doc)} pages -> {args.output}")

if __name__ == '__main__':
    main()
