"""ReAct loop: think -> act -> observe -> remember -> verify -> recover."""
import time, json
from pathlib import Path
from worker.schemas import Observation
from worker.memory import Memory
from worker.ledger import Ledger
from worker.planner import make_plan
from worker.tools.registry import call, FALLBACKS
from worker.human import check, UserNeeded
from worker import verifier as V

def _resolve(args: dict, mem: Memory) -> dict:
    out = {}
    for k, v in args.items():
        if v == "__LATEST__":
            items = mem.facts.get("search_results", [])
            out["file"] = items[0]["_file"] if items else ""
        elif v == "__INVOICE_ID__":
            out[k] = mem.facts.get("invoice_id", "")
        elif v == "__VENDOR__":
            out[k] = mem.facts.get("vendor", "")
        elif v == "__AMOUNT__":
            out[k] = mem.facts.get("amount", 0)
        elif v == "__DUE__":
            out[k] = mem.facts.get("due_date", "")
        else:
            out[k] = v
    return out

def _learn(obs: Observation, mem: Memory, tool: str):
    if not obs.success:
        return
    d = obs.data
    if tool == "inbox.search" and isinstance(d, list) and d:
        mem.remember("search_results", d)
        mem.remember("latest_file", d[0].get("_file", ""))
    if tool == "invoice.parse" and isinstance(d, dict):
        for k in ("vendor", "amount", "due_date", "invoice_id"):
            if k in d:
                mem.remember(k, d[k])
    if tool == "browser.open" and isinstance(d, dict) and d.get("embedded"):
        try:
            inv = json.loads(d["embedded"])
            for k in ("vendor", "amount", "due_date", "invoice_id"):
                if k in inv:
                    mem.remember(k, inv[k])
        except Exception:
            pass
    if tool == "files.scan" and isinstance(d, list):
        mem.remember("scan_hits", d)
        # normalize filename hits into search_results so downstream parse works
        try:
            import json as _j
            from pathlib import Path as _P
            results = []
            for name in d:
                p = _P("data/inbox") / name
                if p.exists():
                    r = _j.loads(p.read_text(encoding="utf-8"))
                    r["_file"] = name
                    results.append(r)
            if results:
                results.sort(key=lambda x: x.get("date", ""), reverse=True)
                mem.remember("search_results", results)
        except Exception:
            pass

class Agent:
    def __init__(self, cfg: dict, run_dir: str, auto_approve=False, ui_events=None):
        self.cfg = cfg
        self.mem = Memory()
        self.ledger = Ledger(run_dir)
        self.auto_approve = auto_approve
        self.run_dir = Path(run_dir)
        self.ui = ui_events

    def emit(self, msg: str):
        self.ledger.log({"type": "thought", "msg": msg})
        if self.ui is not None:
            self.ui.append(msg)

    def run(self, task: str) -> dict:
        plan = make_plan(task)
        self.emit(f"Goal understood: {task}")
        self.emit(f"Plan: {' -> '.join(s.tool for s in plan.steps)}")
        self.ledger.log({"type": "plan", "steps": [s.__dict__ for s in plan.steps]})
        tries = 0
        max_steps = self.cfg.get("max_steps", 12)
        for step in plan.steps:
            if tries >= max_steps:
                break
            args = _resolve(step.args, self.mem)
            if step.tool == "files.scan" and ("overdue" in task.lower() or "total" in task.lower()):
                if self._summarize(task):
                    break
            try:
                check(step.tool, args, self.cfg, self.auto_approve)
            except UserNeeded as u:
                self.ledger.log({"type": "human_gate", "question": u.question})
                if self.auto_approve:
                    self.emit(f"Auto-approved: {u.question}")
                else:
                    return self._finish(task, False, f"Needs approval: {u.question}", needs_user=u.question)
            obs = self._act_with_retry(step.tool, args)
            _learn(obs, self.mem, step.tool)
            if step.tool == "inbox.search" and obs.success and obs.data:
                latest = obs.data[0]["_file"]
                self.emit(f"Found latest invoice: {latest}")
                pobs = self._act_with_retry("invoice.parse", {"file": latest})
                _learn(pobs, self.mem, "invoice.parse")
                if not pobs.success:
                    obs = pobs
            step.done = obs.success
            tries += 1
        ok, vmsg = V.verify_summary(task, self.mem)
        self.emit(vmsg)
        return self._finish(task, ok, vmsg)

    def _act_with_retry(self, tool: str, args: dict, retries=2) -> Observation:
        attempt = 0
        while True:
            self.emit(f"Act: {tool} {args}")
            obs = call(tool, args)
            self.ledger.log({"type": "action", "tool": tool, "args": args,
                             "ok": obs.success, "evidence": obs.evidence, "error": obs.error})
            self.emit(f"Observed: {obs.evidence or obs.error}")
            if obs.success:
                return obs
            fbs = FALLBACKS.get(tool, [])
            if attempt < len(fbs):
                fb = fbs[attempt]
                self.emit(f"Failed, trying alternative: {fb}")
                if fb == "files.scan":
                    obs2 = call(fb, {"keyword": str(args.get("vendor", "INV"))})
                elif fb == "browser.open":
                    obs2 = call(fb, {"url": "vendor-portal/latest-invoice"})
                    if obs2.success:
                        _learn(obs2, self.mem, fb)
                        return obs2
                else:
                    obs2 = call(fb, {})
                self.ledger.log({"type": "fallback", "tool": fb, "ok": obs2.success})
                if obs2.success:
                    return obs2
            attempt += 1
            if attempt > retries:
                return obs
            time.sleep(0.3 * attempt)

    def _summarize(self, task: str) -> bool:
        from worker.tools.inbox import tool_inbox_search
        import datetime
        obs = tool_inbox_search()
        if not obs.success:
            return False
        today = datetime.date.today().isoformat()
        over = [i for i in obs.data if i.get("due_date", "") < today]
        total = round(sum(float(i["amount"]) for i in over), 2)
        self.mem.remember("overdue", over)
        self.mem.remember("summary_total", total)
        self.emit(f"Summary: {len(over)} overdue, total ${total}")
        return True

    def _finish(self, task, ok, vmsg, needs_user=None) -> dict:
        facts = self.mem.facts
        summary = (f"Task: {task}\nResult: {'DONE' if ok else 'NOT DONE'}\n"
                   f"Vendor: {facts.get('vendor', '-')}\nAmount: {facts.get('amount', '-')}\n"
                   f"Due: {facts.get('due_date', '-')}\nInvoice: {facts.get('invoice_id', '-')}\n"
                   f"Verification: {vmsg}\n")
        if facts.get("summary_total") is not None:
            summary += f"Overdue total: ${facts['summary_total']} across {len(facts.get('overdue', []))} invoices\n"
        (self.run_dir / "summary.md").write_text(summary, encoding="utf-8")
        self.ledger.log({"type": "result", "ok": ok, "summary": summary})
        return {"ok": ok, "summary": summary, "facts": facts, "needs_user": needs_user}

