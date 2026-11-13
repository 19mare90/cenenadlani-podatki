# SPAR PDF review import

This importer currently supports **SPAR catalogue 45/26 only** (4–10 November 2026).
It produces five **unverified candidates** from page 7. This is not exhaustive extraction.

## Run locally

```bash
python -m pip install -r requirements-spar.txt
python scripts/import_spar_pdf.py "261104-1-Katalog_4526.pdf"
```

Output: `data/spar_prices.json`. Every item has `publishable: false` and
`reviewStatus: needs_manual_review`.

**Do not feed this file directly to the public `prices.json` endpoint.**
Only independently verified, currently valid offers may be published.
The existing publication workflow is intentionally unchanged.
