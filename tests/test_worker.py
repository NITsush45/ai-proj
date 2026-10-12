import json
from pathlib import Path
from worker.config import load_config
from worker.agent import Agent

def fresh(run="runs/t1"):
    Path("data/erp.json").write_text(json.dumps({"entries": []}))
    p = Path(run)
    import shutil
    shutil.rmtree(p, ignore_errors=True)
    return Agent(load_config(), run, auto_approve=True)

def test_invoice_books_and_verifies():
    r = fresh().run("Find the latest invoice from Acme Corp and book it in ERP")
    assert r["ok"], r["summary"]
    db = json.loads(Path("data/erp.json").read_text())
    assert db["entries"], "ERP should have entry"
    assert db["entries"][0]["invoice_id"] == "ACME-2026-10-131"

def test_idempotent_rebook():
    a = fresh("runs/t2")
    a.run("Find the latest invoice from Acme Corp and book it in ERP")
    r2 = a.run("Find the latest invoice from Acme Corp and book it in ERP")
    db = json.loads(Path("data/erp.json").read_text())
    ids = [e["invoice_id"] for e in db["entries"]]
    assert len(ids) == len(set(ids)), "no duplicates"

def test_overdue_summary_generalizes():
    r = fresh("runs/t3").run("List all overdue invoices and summarize total due")
    assert r["ok"] and "Overdue total" in r["summary"]
    assert r["facts"]["summary_total"] >= 950.0, r["facts"]
