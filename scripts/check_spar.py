
#!/usr/bin/env python3
"""CeneNaDlani: spremljanje dosegljivosti kataloga SPAR."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = "https://www.spar.si/letak"
STATE = Path("data/spar_catalog_state.json")
OUTPUT = Path("spar_monitor_result.json")


def main():
    result = {
        "checkedAt": datetime.now(timezone.utc).isoformat(),
        "sourceUrl": URL,
        "status": "unavailable",
        "changed": False,
        "pricesVerified": False,
        "note": "Monitoring only; no prices extracted or published."
    }

    try:
        req = Request(
            URL,
            headers={
                "User-Agent": "CeneNaDlaniCatalogueMonitor/0.3",
                "Accept": "text/html"
            }
        )

        with urlopen(req, timeout=25) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")

            raw = response.read(2_000_001)

            if len(raw) > 2_000_000:
                raise RuntimeError("Page too large")

        html = raw.decode("utf-8", errors="replace")

        if "katalog" not in html.lower() and "letak" not in html.lower():
            raise RuntimeError("Unexpected page content")

        digest = hashlib.sha256(raw).hexdigest()

        previous = (
            json.loads(STATE.read_text(encoding="utf-8"))
            if STATE.exists()
            else {}
        )

        changed = bool(
            previous.get("sha256")
            and previous["sha256"] != digest
        )

        result.update({
            "status": "available",
            "changed": changed,
            "sha256": digest,
            "note": "Page changed; manual review required."
                    if changed else "No detected change or first check."
        })

        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(
            json.dumps({
                "sha256": digest,
                "sourceUrl": URL
            }, indent=2) + "\n",
            encoding="utf-8"
        )

    except HTTPError as exc:
        result["error"] = f"HTTP {exc.code}"
        result["note"] = "Source refused access; offers not checked."

    except URLError as exc:
        result["error"] = str(exc.reason)
        result["note"] = "Network error; offers not checked."

    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
        result["note"] = "Unexpected monitoring error; review required."

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print(json.dumps(result, ensure_ascii=False))

    if result["status"] != "available":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
