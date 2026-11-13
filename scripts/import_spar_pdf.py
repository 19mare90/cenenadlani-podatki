#!/usr/bin/env python3
"""Extract page text from a SPAR catalogue for manual review."""
import argparse
import hashlib
import json
from pathlib import Path

import fitz


def import_pdf(source, destination):
    destination = destination.resolve()
    if destination in {
        source.resolve(),
        (Path(__file__).resolve().parents[1] / "prices.json").resolve(),
        (Path(__file__).resolve().parents[1] / "data/reviewed_offers.json").resolve(),
    } or destination.name in {"prices.json", "reviewed_offers.json"}:
        raise ValueError("Choose a separate review output file.")
    raw = source.read_bytes()
    with fitz.open(stream=raw, filetype="pdf") as document:
        pages = []
        for number, page in enumerate(document, start=1):
            text = page.get_text(sort=True).strip()
            pages.append({"page": number, "text": text, "needsVisualReview": not text})
        if not pages:
            raise ValueError("Catalogue contains no pages.")
    result = {
        "schemaVersion": 2,
        "sourceFile": source.name,
        "sourceSha256": hashlib.sha256(raw).hexdigest(),
        "reviewStatus": "needs_manual_review",
        "publishable": False,
        "pages": pages,
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(pages)} pages for manual review.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/spar_prices.json"))
    args = parser.parse_args()
    import_pdf(args.pdf, args.output)
