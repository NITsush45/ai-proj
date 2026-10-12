# Centralign — Autonomous AI Task Worker (Prototype)

Narrow but real: NL task → plan → act → observe → verify → summary + evidence.
Example: *"Find latest invoice from Acme Corp, extract amount/due date, book in ERP, tell me when done."*

## Setup & run

No install and no API key required — core worker is Python stdlib only (3.10+).

```powershell
# from the repo root
python demo.py        # 10-second end-to-end demo (books an invoice, verifies it)
python run_tests.py   # 3 tests: book+verify, idempotent rebook, task generalization
python run.py --task "Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done." --auto-approve
```

Web UI (optional; needs fastapi + uvicorn — use `python -m`, bare `pip`/`uvicorn` may be broken on Windows):

```powershell
python -m pip install fastapi "uvicorn[standard]"
python -m uvicorn app:app --port 8000
# open http://127.0.0.1:8000
```

Optional LLM planning (better plans for open-ended tasks; heuristic planner is used otherwise):

```powershell
$env:OPENAI_API_KEY="sk-..."
$env:LLM_MODEL="gpt-4o-mini"   # any OpenAI-compatible chat model
python run.py --task "Find the latest invoice from Acme Corp and book it in ERP" --auto-approve
```

Troubleshooting: if `uvicorn` says port 8000 is in use, an old server is still running —
`netstat -ano | findstr :8000` then `taskkill /PID <num> /F`, or use `--port 8001`.
After UI edits, hard-refresh the browser (`Ctrl+Shift+R`) — old JS caches aggressively.

## Architecture

```
User task → Planner (LLM or heuristic) → Agent ReAct loop → Tool Registry
  (inbox.search, invoice.parse, erp.lookup/book, browser.open, files.*)
    → Simulated enterprise (data/inbox, data/erp.json, data/web)
      → Verifier (re-reads ground-truth ERP vs source) → summary.md + ledger.jsonl evidence
```

Key files: `worker/planner.py` (plan), `worker/agent.py` (think→act→observe→verify→recover loop),
`worker/tools/` (capability layer), `worker/verifier.py` (independent outcome check),
`worker/human.py` (approval gate for money actions), `worker/memory.py` (facts across steps),
`worker/ledger.jsonl` via `worker/ledger.py` (append-only evidence trail).

## Important technical / design decisions

1. **Narrow but real** — one domain (invoice→ERP) executed for real on files, not mocked clicks. Depth over feature count.
2. **LLM optional** — heuristic planner handles finance intents offline with the same tool schema an LLM would target; set `OPENAI_API_KEY` to upgrade planning, no other change.
3. **Verification is first-class** — the verifier re-reads the ERP independently and compares against the source document; no `DONE` without a match.
4. **Reliability** — classified retries + fallback chain (`inbox.search → files.scan → browser.open`), idempotent `erp.book` (re-book doesn't duplicate), bounded `max_steps`.
5. **Human gate only for money** — reads auto-run; `erp.book` ≥ $5000 requires `--auto-approve` or an explicit UI approval.
6. **Evidence over claims** — every run writes `runs/<id>/ledger.jsonl` (all actions, args, results) and `runs/<id>/summary.md`.

## Demo

`DEMO_SCRIPT.txt` has the 90-second script (empty ERP → `python demo.py` → evidence → overdue task → approval gate).
Video link: _TODO — add YouTube/Loom URL here after recording._

## Known limitations

- Simulated inbox/ERP/vendor portal only (no real Gmail/SAP/Playwright connectors).
- Heuristic planner covers finance intents; arbitrary open-ended tasks need the LLM path.
- Single-user file-backed "DB"; no cross-run memory; in-process concurrency only (single-user demo).

## What I'd build next

- Real connectors (Gmail, Playwright browser, SAP/ERP API) behind the existing tool registry.
- Persistent/vector memory across runs; policy engine instead of the hard-coded $5000 rule.
- Eval harness: golden task set + pass/fail metrics for autonomy, recovery, verification.

## Assumptions

- Invoices arrive as JSON in `data/inbox`; ERP state lives in `data/erp.json` keyed by `invoice_id`.
- USD amounts, ISO `YYYY-MM-DD` dates; approval threshold $5000 (`config.yaml`).
- One agent run at a time; approval is a binary ask, not a negotiation.

## Models, APIs, frameworks & external services

- **Models:** none required — stdlib-only heuristic planner by default; optional OpenAI-compatible chat completions (`OPENAI_API_KEY`, `LLM_MODEL`, default `gpt-4o-mini`).
- **Frameworks:** FastAPI + Uvicorn (web UI only), PyYAML (config), pytest (tests, optional).
- **External services:** none — enterprise systems are simulated locally in `data/`.
- **Pre-built components:** Python standard library only for the core worker.

