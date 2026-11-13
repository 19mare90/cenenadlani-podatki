"""Regression tests for publication safety. No network required."""
import importlib.util
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_prices", ROOT / "scripts/build_prices.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class PublicationSafetyTests(unittest.TestCase):
    def offer(self):
        today = date.today()
        return dict(id="test-1", name="Test item", quantity="1 l", store="SPAR",
                    price=1.25, unitPrice="1,25 €/l",
                    validUntil=(today + timedelta(days=2)).isoformat(),
                    checkedAt=today.isoformat(), sourceUrl="https://www.spar.si/letak",
                    region="Slovenija", loyalty="Brez kartice",
                    reviewStatus="approved", reviewedBy="Manual review")

    def publish(self, offers):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "reviewed.json"
            output = Path(directory) / "prices.json"
            source.write_text(json.dumps({"offers": offers}), encoding="utf-8")
            with patch.object(build, "INPUT", source), patch.object(build, "OUTPUT", output):
                build.main()
            return json.loads(output.read_text(encoding="utf-8"))["offers"]

    def test_approved_current_offer(self):
        self.assertEqual(len(self.publish([self.offer()])), 1)

    def test_pending_is_not_published(self):
        offer = self.offer()
        offer["reviewStatus"] = "needs_manual_review"
        self.assertEqual(self.publish([offer]), [])

    def test_expired_is_not_published(self):
        offer = self.offer()
        offer["validUntil"] = (date.today() - timedelta(days=1)).isoformat()
        self.assertEqual(self.publish([offer]), [])

    def test_nonofficial_source_is_not_published(self):
        offer = self.offer()
        offer["sourceUrl"] = "https://example.com/spar"
        self.assertEqual(self.publish([offer]), [])

    def test_future_check_is_not_published(self):
        offer = self.offer()
        offer["checkedAt"] = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual(self.publish([offer]), [])

    def test_duplicate_id_is_not_published_twice(self):
        self.assertEqual(len(self.publish([self.offer(), self.offer()])), 1)

if __name__ == "__main__":
    unittest.main()
