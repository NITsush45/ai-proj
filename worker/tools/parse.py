import json, re
from pathlib import Path
from worker.schemas import Observation

def tool_invoice_parse(file: str = "", text: str = ""):
    """Extract vendor/amount/due_date/invoice_id from a file or raw text."""
    try:
        raw = text
        if file:
            p = Path("data/inbox") / file
            if not p.exists():
                p = Path(file)
            raw = p.read_text(encoding="utf-8")
        try:
            d = json.loads(raw)
            inv = {"vendor": d["vendor"], "amount": float(d["amount"]),
                   "due_date": d["due_date"], "invoice_id": d.get("invoice_id", d.get("id", "")),
                   "date": d.get("date", "")}
            return Observation(True, inv, evidence=f"parsed {file or 'text'} -> {inv['invoice_id']}")
        except Exception:
            pass
        amt = re.search(r"\$?\s?([\d,]+\.\d{2})", raw)
        due = re.search(r"due[^0-9]*(\d{4}-\d{2}-\d{2})", raw, re.I)
        ven = re.search(r"(?:from|vendor)\s*[:\-]?\s*([A-Za-z0-9 .&]+)", raw, re.I)
        inv_id = re.search(r"(?:invoice\s*(?:id|no|#)\s*[:\-]?\s*([A-Za-z0-9\-]+))", raw, re.I)
        if not (amt and due):
            return Observation(False, None, "could not extract amount/due_date",
                               evidence=f"parse failed on {file or 'text'}")
        inv = {"vendor": ven.group(1).strip() if ven else "Unknown",
               "amount": float(amt.group(1).replace(",", "")),
               "due_date": due.group(1),
               "invoice_id": inv_id.group(1) if inv_id else "INV-UNK",
               "date": ""}
        return Observation(True, inv, evidence=f"regex-parsed -> {inv['invoice_id']}")
    except Exception as e:
        return Observation(False, None, f"parse error: {e}")
