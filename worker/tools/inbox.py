import json, re
from pathlib import Path
from worker.schemas import Observation

DATA = Path("data")

def tool_inbox_search(vendor: str = "", latest: bool = True):
    """Search simulated inbox for invoices."""
    try:
        files = sorted((DATA / "inbox").glob("*.json"))
        items = []
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            if vendor and vendor.lower() not in d.get("vendor", "").lower():
                continue
            d["_file"] = f.name
            items.append(d)
        if not items:
            return Observation(False, None, f"no invoices for vendor '{vendor}'",
                              evidence="inbox search: 0 hits")
        items.sort(key=lambda x: x.get("date", ""), reverse=latest)
        return Observation(True, items, evidence=f"inbox search: {len(items)} hits, top={items[0]['_file']}")
    except Exception as e:
        return Observation(False, None, f"inbox error: {e}")
