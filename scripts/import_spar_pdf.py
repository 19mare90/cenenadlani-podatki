#!/usr/bin/env python3
"""Import conservative review candidates from SPAR catalogue 45/26.
No offer is approved or published automatically.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import fitz

SEEDS = [
    ("HRENOVKE NJAMI IK", "200 g", 1.99, 2.49),
    ("PIŠČANČJI FILE IK", "500 g", 5.19, 6.99),
    ("MINI FILETINI IK", "400 g", 4.99, 6.29),
    ("SIR TOLMINC IK", "1 kg", 22.49, 24.99),
    ("SVEŽE POSTREŽNO MESO JAGENJČKA IK", None, 14.99, 17.99),
]

def normalize(value):
    return re.sub(r"\s+", " ", value).strip().upper()

def import_pdf(source, destination):
    raw = source.read_bytes()
    with fitz.open(stream=raw, filetype="pdf") as document:
        if len(document) < 7 or "45/26" not in normalize(document[0].get_text()):
            raise ValueError("Unsupported catalogue: expected SPAR 45/26.")
        page_text = normalize(document[6].get_text())
        items = []
        for index, (name, quantity, price, regular) in enumerate(SEEDS, 1):
            if normalize(name) not in page_text:
                raise ValueError(f"Missing product on page 7: {name}")
            items.append({
                "id": f"spar-4526-{index:03d}",
                "name": name,
                "quantity": quantity,
                "priceEur": price,
                "regularPriceEur": regular,
                "store": "SPAR",
                "validFrom": "2026-11-04",
                "validTo": "2026-11-10",
                "requiresLoyaltyCard": True,
                "sourcePage": 7,
                "reviewStatus": "needs_manual_review",
                "reviewReasons": [
                    "Check price-product association against the PDF artwork",
                    "Check SPAR plus card conditions and availability"
                ],
                "publishable": False
            })
    result = {
        "schemaVersion": 1,
        "source": "SPAR catalogue 45/26",
        "sourceFile": source.name,
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "importedAt": datetime.now(timezone.utc).isoformat(),
        "catalogueValidFrom": "2026-11-04",
        "catalogueValidTo": "2026-11-10",
        "status": "manual_review_required",
        "warning": "Historical catalogue; not exhaustive; never publish without manual verification.",
        "items": items
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(items)} review-only candidates to {destination}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/spar_prices.json"))
    args = parser.parse_args()
    import_pdf(args.pdf, args.output)
