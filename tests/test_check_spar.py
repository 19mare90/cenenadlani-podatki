import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from scripts import check_spar


class SparMonitorTests(unittest.TestCase):
    def test_network_failure_keeps_previous_state_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            output = Path(directory) / "result.json"
            state.write_text('{"sha256": "previous"}', encoding="utf-8")
            with patch.object(check_spar, "STATE", state), patch.object(
                check_spar, "OUTPUT", output
            ), patch.object(check_spar, "urlopen", side_effect=URLError("offline")):
                with self.assertRaises(SystemExit) as failure:
                    check_spar.main()
            self.assertEqual(failure.exception.code, 1)
            self.assertEqual(json.loads(state.read_text())["sha256"], "previous")
            result = json.loads(output.read_text())
            self.assertEqual(result["status"], "unavailable")
            self.assertFalse(result["pricesVerified"])
