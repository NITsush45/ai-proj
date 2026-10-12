"""Independent ground-truth check: did ERP actually match the source invoice?"""
from worker.tools.erp import tool_erp_lookup

def verify_booking(expected: dict):
    """expected: {vendor, amount, due_date, invoice_id}"""
    if not expected or not expected.get("invoice_id") or expected.get("invoice_id", "").startswith("__"):
        return False, "verifier: no concrete invoice extracted; cannot confirm booking"
    obs = tool_erp_lookup(invoice_id=expected["invoice_id"])
    if not obs.success or not obs.data:
        return False, f"verifier: {expected['invoice_id']} NOT found in ERP"
    e = obs.data[0]
    try:
        ok = (abs(float(e["amount"]) - float(expected["amount"])) < 0.01
              and e["due_date"] == expected["due_date"]
              and expected["vendor"].lower() in e["vendor"].lower())
    except Exception:
        return False, f"verifier: field mismatch ERP={e} expected={expected}"
    if ok:
        return True, f"verifier: ERP entry {e['invoice_id']} matches source (${e['amount']} due {e['due_date']})"
    return False, f"verifier: field mismatch ERP={e} expected={expected}"

def verify_summary(task: str, memory) -> tuple:
    t = task.lower()
    if "overdue" in t or "total" in t or "summar" in t or "list all" in t:
        facts = memory.facts
        if facts.get("summary_total") is not None or facts.get("overdue"):
            return True, "verifier: summary produced with totals"
        return False, "verifier: no summary totals in memory"
    exp = {"vendor": memory.facts.get("vendor", ""), "amount": memory.facts.get("amount"),
           "due_date": memory.facts.get("due_date"), "invoice_id": memory.facts.get("invoice_id", "")}
    return verify_booking(exp)
