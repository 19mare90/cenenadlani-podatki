# SPAR PDF import (manual review only)

This workflow is separate from the existing SPAR catalogue monitor and does not publish prices.

1. Add the legally obtained catalogue PDF at `input/spar_katalog.pdf` (if distribution is permitted).
2. In GitHub Actions run **SPAR PDF - prepare review candidates**.
3. Download the `spar-review-candidates` artifact containing `data/spar_prices.json`.
4. Review each candidate against the PDF, including product name, amount, unit, SPAR plus terms and validity.
5. Only manually approved offers should enter the application's published `prices.json`.

The JSON is deliberately marked `draft_not_for_app`. A numeric candidate is not a verified product-price pair. No automated publication is implemented.
