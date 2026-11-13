import json
import tempfile
import unittest
from pathlib import Path

import fitz

from scripts.import_spar_pdf import import_pdf


class SparImportTests(unittest.TestCase):
    def test_extracts_all_pages_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "catalogue.pdf"
            destination = source.with_suffix(".json")
            with fitz.open() as document:
                document.new_page().insert_text((50, 50), "SPAR 1,99 EUR")
                document.new_page()
                document.save(source)
            import_pdf(source, destination)
            result = json.loads(destination.read_text(encoding="utf-8"))
            self.assertFalse(result["publishable"])
            self.assertNotIn("offers", result)
            self.assertIn("1,99", result["pages"][0]["text"])
            self.assertTrue(result["pages"][1]["needsVisualReview"])
            with self.assertRaises(ValueError):
                import_pdf(source, source.with_name("prices.json"))
