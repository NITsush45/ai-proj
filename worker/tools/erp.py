import json
from pathlib import Path
from worker.schemas import Observation

ERP = Path("data/erp.json")

def _load():
    if not ERP.exists():
        return {"entries": []}
    return json.loads(ERP.read_text(encoding="utf-8"))

def _save(db):
    ERP.write_text(json.dumps(db, indent=2), encoding="utf-8")

def tool_erp_lookup(invoice_id: str = "", vendor: str = ""):
    try:
        db = _load()
        hits = [e for e in db["entries"]
                if (invoice_id and e.get("invoice_id") == invoice_id)
                or (vendor and vendor.lower() in e.get("vendor", "").lower())]
        return Observation(True, hits, evidence=f"erp lookup: {len(hits)} hits")
    except Exception as e:
        return Observation(False, None, f"erp lookup error: {e}")

def tool_erp_book(vendor: str, amount: float, due_date: str, invoice_id: str):
    try:
        db = _load()
        if any(e.get("invoice_id") == invoice_id for e in db["entries"]):
            return Observation(True, {"duplicate": True, "invoice_id": invoice_id},
                               evidence=f"erp: {invoice_id} already booked (idempotent)")
        entry = {"vendor": vendor, "amount": float(amount), "due_date": due_date,
                 "invoice_id": invoice_id, "status": "booked"}
        db["entries"].append(entry)
        _save(db)
        return Observation(True, entry, evidence=f"erp booked {invoice_id} ${amount} due {due_date}")
    except Exception as e:
        return Observation(False, None, f"erp book error: {e}")
