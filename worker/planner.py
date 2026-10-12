"""Goal -> Plan. LLM when available, deterministic heuristic otherwise."""
import re, json
from worker.schemas import Plan, Step
from worker.llm import LLM

SYS = ("You turn a business request into a JSON plan. "
       "Tools: inbox.search(vendor), invoice.parse(file), erp.lookup(invoice_id), "
       "erp.book(vendor,amount,due_date,invoice_id), browser.open(url), files.scan(keyword). "
       "Return JSON list of {goal,tool,args,why}. Max 7 steps.")

def _heuristic(task: str) -> Plan:
    t = task.lower()
    vendor = "Acme Corp"
    m = re.search(r"from\s+([A-Za-z0-9 .&'\-]+?)(?:,|\s+extract|\s+and|\s*$)", task, re.I)
    if m:
        vendor = m.group(1).strip().rstrip(".")
    steps = []
    if "overdue" in t or "list all" in t or "summar" in t or "total" in t:
        steps = [
            Step(1, f"Search inbox for all invoices", "inbox.search", {"vendor": ""}, "gather candidates"),
            Step(2, "Summarize overdue totals", "files.scan", {"keyword": "due_date"}, "aggregate"),
        ]
    else:
        steps = [
            Step(1, f"Find latest invoice from {vendor}", "inbox.search", {"vendor": vendor}, "locate source doc"),
            Step(2, "Extract amount/due date", "invoice.parse", {"file": "__LATEST__"}, "parse fields"),
            Step(3, "Check ERP for duplicate", "erp.lookup", {"invoice_id": "__INVOICE_ID__"}, "idempotency"),
            Step(4, "Book into internal system", "erp.book",
                 {"vendor": "__VENDOR__", "amount": "__AMOUNT__", "due_date": "__DUE__", "invoice_id": "__INVOICE_ID__"},
                 "complete user goal"),
        ]
    return Plan(goal=task, steps=steps)

def make_plan(task: str, llm: LLM = None) -> Plan:
    llm = llm or LLM()
    if llm.available:
        try:
            raw = llm.chat(SYS, task)
            m = re.search(r"\[.*\]", raw, re.S)
            arr = json.loads(m.group(0) if m else raw)
            steps = [Step(i + 1, s.get("goal", s.get("tool", "")), s.get("tool", ""),
                          s.get("args", {}), s.get("why", "")) for i, s in enumerate(arr)]
            return Plan(goal=task, steps=steps)
        except Exception:
            pass
    return _heuristic(task)
