"""Web UI: python -m uvicorn app:app --port 8000."""
import uuid
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from worker.config import load_config
from worker.agent import Agent

app = FastAPI(title="Centralign AI Worker")
EVENTS: list = []
LAST: dict = {}

PAGE = """<html><head><title>Centralign AI Worker</title>
<style>body{font-family:-apple-system,"Segoe UI",Roboto,Arial,sans-serif;max-width:860px;margin:32px auto;padding:0 20px;color:#1f2328;line-height:1.5}
.header{border-bottom:1px solid #d0d7de;padding-bottom:12px;margin-bottom:8px}
.header h1{font-size:20px;margin:0}
.header p{margin:4px 0 0;color:#57606a;font-size:13px}
.panel{border:1px solid #d0d7de;border-radius:6px;margin:16px 0}
.panel h3{margin:0;padding:8px 12px;background:#f6f8fa;border-bottom:1px solid #d0d7de;font-size:13px;color:#57606a}
.panel .body{padding:12px}
#task{width:100%;box-sizing:border-box;padding:8px;border:1px solid #d0d7de;border-radius:6px;font-size:14px}
.row{margin-top:10px;display:flex;gap:12px;align-items:center}
button{padding:6px 16px;background:#1f883d;color:#fff;border:1px solid #1f883d;border-radius:6px;cursor:pointer}
label.small{font-size:13px;color:#57606a}</style></head><body>
<div class=header><h1>Centralign — Task Worker</h1>
<p>Type a goal, click Run, watch the trace. Evidence lands in runs/&lt;id&gt;/.</p></div>
<div class=panel><h3>Task</h3><div class=body>
<form id=f style="margin:0"><input id=task value="Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done.">
<div class=row><button>Run</button>
<label class=small><input type=checkbox id=auto checked> auto-approve bookings</label></div></form>
</div></div>
<div class=panel><h3>Live trace</h3><div class=body style="padding:0"><div id=log></div></div></div>
<div class=panel><h3>Summary</h3><div class=body><pre id=sum style="margin:0;white-space:pre-wrap"></pre></div></div>
<div class=panel><h3>Evidence</h3><div class=body>
<div class=row><button id=bErp type=button>View erp.json</button><button id=bLed type=button>View ledger.jsonl</button>
<span class=small id=evhint></span></div>
<pre id=evi style="margin-top:10px;max-height:240px;overflow:auto;background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:10px;font-size:12px;white-space:pre-wrap"></pre>
</div></div>
<script>
var log=document.getElementById('log');
function poll(){
  fetch('/events').then(function(r){return r.json();}).then(function(j){
    log.innerText=(j.events||[]).join(String.fromCharCode(10));log.scrollTop=1e6;
  });
  fetch('/result').then(function(r){return r.json();}).then(function(k){
    document.getElementById('sum').innerText=k.summary||'';
  });
}
document.getElementById('f').onsubmit=function(e){
  e.preventDefault();
  log.innerText='working...';
  fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({task:document.getElementById('task').value,
                         auto:document.getElementById('auto').checked})}).then(poll);
};
setInterval(poll,1500);
document.getElementById('bErp').onclick=function(){fetch('/erp').then(function(r){return r.json();}).then(function(j){document.getElementById('evi').innerText=JSON.stringify(j,null,2);document.getElementById('evhint').innerText='data/erp.json';});};
document.getElementById('bLed').onclick=function(){fetch('/ledger').then(function(r){return r.json();}).then(function(j){var L=j.lines||[];document.getElementById('evi').innerText=L.slice(-40).join(String.fromCharCode(10))||'(no ledger yet)';document.getElementById('evhint').innerText=(L.length||0)+' lines';});};
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE

@app.post("/run")
def run(body: dict):
    global LAST
    EVENTS.clear(); LAST = {}
    cfg = load_config()
    run_dir = "runs/%s" % uuid.uuid4().hex[:8]
    agent = Agent(cfg, run_dir, auto_approve=body.get("auto", True), ui_events=EVENTS)
    LAST = agent.run(body.get("task", ""))
    LAST["run_dir"] = run_dir
    return {"ok": LAST["ok"]}

@app.get("/events")
def events():
    return {"events": EVENTS}

@app.get("/erp")
def erp():
    import json as _j
    p = Path("data/erp.json")
    if not p.exists():
        return {"entries": []}
    return _j.loads(p.read_text(encoding="utf-8"))

@app.get("/ledger")
def ledger():
    rd = LAST.get("run_dir", "")
    p = Path(rd) / "ledger.jsonl" if rd else None
    lines = p.read_text(encoding="utf-8").splitlines() if p and p.exists() else []
    return {"lines": lines}

@app.get("/result")
def result():
    return {"summary": LAST.get("summary", ""), "ok": LAST.get("ok")}
