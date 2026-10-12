# Centralign — Autonomous AI Task Worker (Prototype)
Narrow but real: NL task -> plan -> act -> observe -> verify -> summary + evidence.
Example: "Find latest invoice from Acme Corp, extract amount/due date, book in ERP."

## Quickstart (no install, no API key)

```powershell
cd c:\Users\Sushant Kumar\Desktop\centralign
python demo.py
python run.py --task "Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done." --auto-approve
python run_tests.py
```

Web UI (needs fastapi + uvicorn — note: use `python -m`, bare `pip`/`uvicorn` may be broken on Windows):

```powershell
python -m pip install fastapi "uvicorn[standard]"
python -m uvicorn app:app --port 8000
# open http://127.0.0.1:8000
```

Optional LLM planning (better plans for open-ended tasks; heuristic is used otherwise):

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:LLM_MODEL="gpt-4o-mini"   # any OpenAI-compatible chat model
python run.py --task "Find the latest invoice from Acme Corp and book it in ERP" --auto-approve
```

## Architecture

User task -> Planner (LLM or heuristic) -> Agent ReAct loop -> Tool Registry
(inbox.search, invoice.parse, erp.lookup/book, browser.open, files.*) ->
Simulated enterprise (data/inbox, data/erp.json, data/web) ->
Verifier (ground-truth ERP vs source) -> summary.md + ledger.jsonl evidence.

Key files: worker/planner.py, worker/agent.py, worker/tools/, worker/verifier.py,
worker/human.py (approval gate), worker/memory.py, worker/ledger.py.

## Design decisions

1. Narrow but real: one domain (invoice->ERP) executed for real on files, not mocked clicks.
2. LLM optional: heuristic planner handles finance intents offline; same tool schema when key is set.
3. Verification first-class: verifier re-reads ERP independently; no DONE without match.
4. Reliability: classified retries + fallback map (inbox.search->files.scan->browser.open), idempotent erp.book.
5. Human gate only for money: reads auto-run; erp.book >= $5000 needs --auto-approve or UI approval.

## Known limitations / assumptions / next steps

Limits: simulated inbox/ERP/portal only; heuristic covers finance intents; single-user file DB; no cross-run memory.
Assumes: invoices as JSON in data/inbox, ERP = data/erp.json keyed by invoice_id, USD/ISO dates, $5000 threshold.
Next: real Gmail/Playwright/SAP connectors, vector memory, policy engine, eval harness.
Models: stdlib only by default; optional OpenAI-compatible chat via OPENAI_API_KEY.

## Demo video

`DEMO_SCRIPT.txt` has the 90-second script (empty ERP → `python demo.py` → evidence → overdue task → approval gate).
Video link: _TODO — add YouTube/Loom URL here after recording._

Troubleshooting: if `uvicorn` says port 8000 is in use, an old server is still running.
`netstat -ano | findstr :8000` then `taskkill /PID <num> /F`, or use `--port 8001`.
After UI edits, hard-refresh the browser (`Ctrl+Shift+R`) — old JS caches aggressively.

