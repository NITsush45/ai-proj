"""Web UI: python -m uvicorn app:app --port 8000."""
import uuid
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from worker.config import load_config
from worker.agent import Agent

app = FastAPI(title="Centralign AI Worker")
EVENTS: list = []
LAST: dict = {}

PAGE = """<html><head><title>Centralign AI Worker</title>
<style>
body{font-family:-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#24292f;background:#fff;max-width:960px;margin:0 auto;padding:0 20px 60px}
nav{border-bottom:1px solid #d0d7de;padding:14px 0;margin-bottom:20px;font-size:14px;color:#57606a}
nav b{color:#24292f;font-size:15px;margin-right:8px}
h1{font-size:22px;margin:0 0 4px}
p.sub{color:#57606a;margin:0 0 20px;font-size:14px}
.card{border:1px solid #d0d7de;border-radius:6px;margin-bottom:16px}
.card h3{margin:0;padding:10px 14px;font-size:13px;background:#f6f8fa;border-bottom:1px solid #d0d7de;color:#57606a;font-weight:600}
.card .in{padding:14px}
#task{width:100%;padding:8px 10px;border:1px solid #d0d7de;border-radius:6px;font-size:14px}
.row{display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap}
button{padding:7px 16px;font-size:14px;border-radius:6px;border:1px solid #1f883d;background:#1f883d;color:#fff;cursor:pointer}
button:disabled{opacity:.6;cursor:wait}
button.sec{background:#f6f8fa;color:#24292f;border-color:#d0d7de}
label.ap{font-size:13px;color:#57606a}
#st{font-size:12px;padding:3px 10px;border:1px solid #d0d7de;border-radius:12px;background:#f6f8fa;color:#57606a}
#st.ok{background:#dafbe1;border-color:#1f883d;color:#1a7f37}
#st.run{background:#ddf4ff;border-color:#0969da;color:#0969da}
#st.need{background:#fff8c5;border-color:#9a6700;color:#9a6700}
#log{background:#0d1117;color:#c9d1d9;padding:12px 14px;height:320px;overflow:auto;white-space:pre-wrap;font:12px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;border-radius:0 0 6px 6px}
pre#sum{margin:0;padding:14px;white-space:pre-wrap;font-size:13px;background:#fff}
table{width:100%;border-collapse:collapse;font-size:13px;margin:0}
td{padding:6px 14px;border-bottom:1px solid #eee}
td.k{color:#57606a;width:120px}
a.ex{font-size:12px;color:#0969da;cursor:pointer;margin-right:12px}
.spin{display:inline-block;width:12px;height:12px;border:2px solid #d0d7de;border-top-color:#0969da;border-radius:50%;animation:sp 0.8s linear infinite;vertical-align:-2px}
@keyframes sp{to{transform:rotate(360deg)}}
.mut{color:#57606a;font-size:12px}
</style></head><body>
<nav><b>centralign</b> task worker <span id=runid style="float:right"></span></nav>
<h1>Run a task</h1>
<p class=sub>Describe the goal in plain English. The worker plans, uses the tools, verifies the result, and logs evidence.</p>
<div class=card><h3>1 &middot; Task</h3><div class=in>
<input id=task value="Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done.">
<div class=row>
<a class=ex data-t="Find the latest invoice from Acme Corp, extract the amount and due date, enter it into our internal system, and tell me once it is done.">invoice booking</a>
<a class=ex data-t="List all overdue invoices and summarize total due">overdue summary</a>
</div>
<form id=f style="margin:0"><div class=row>
<button id=go>Run</button>
<label class=ap><input type=checkbox id=auto checked> auto-approve bookings &ge; $5,000</label>
<span id=st>idle</span>
</div></form>
<p class=mut style="margin:10px 0 0">Reads run freely. Money movement above the threshold needs approval unless auto-approve is on.</p>
</div></div>
<div class=card><h3>2 &middot; Live trace</h3><div id=log>No run yet. Submit a task above.</div></div>
<div class=card><h3>3 &middot; Result</h3><table id=kv><tr><td class=k>status</td><td>—</td></tr></table><h3 style="border-top:1px solid #d0d7de">Summary</h3><pre id=sum>—</pre></div>
<script>
var log=document.getElementById('log');
var st=document.getElementById('st');
var exs=document.querySelectorAll('.ex');
for(var i=0;i<exs.length;i++){exs[i].onclick=function(){document.getElementById('task').value=this.getAttribute('data-t');};}
function poll(){
  fetch('/events').then(function(r){return r.json();}).then(function(j){
    log.innerText=(j.events||[]).join('\n');log.scrollTop=1e6;
  });
  fetch('/status').then(function(r){return r.json();}).then(function(s){
    if(!s.done)return;
    fetch('/result').then(function(r){return r.json();}).then(function(k){
    if(!k.summary)return;
    try {
      document.getElementById('sum').innerText = k.summary;
      var f = k.facts || {};
      var h = '<tr><td class=k>status</td><td>' + (k.needs_user ? 'needs approval' : (k.ok ? 'done - verified' : 'not done')) + '</td></tr>';
      h += '<tr><td class=k>vendor</td><td>' + (f.vendor || '-') + '</td></tr>';
      h += '<tr><td class=k>amount</td><td>' + (f.amount != null ? ('$' + f.amount) : '-') + '</td></tr>';
      h += '<tr><td class=k>due</td><td>' + (f.due_date || '-') + '</td></tr>';
      h += '<tr><td class=k>invoice</td><td>' + (f.invoice_id || '-') + '</td></tr>';
      if (f.summary_total != null) h += '<tr><td class=k>overdue total</td><td>$' + f.summary_total + '</td></tr>';
      if (k.needs_user) h += '<tr><td class=k>approval</td><td>' + k.needs_user + '</td></tr>';
      document.getElementById('kv').innerHTML = h;
      document.getElementById('go').disabled = false;
      st.className = k.needs_user ? 'need' : (k.ok ? 'ok' : '');
      st.innerText = k.needs_user ? 'needs approval' : (k.ok ? 'done' : 'not done');
    } catch (err) {
      document.getElementById('sum').innerText = k.summary;
      document.getElementById('go').disabled = false;
    }
  });
  });
}
document.getElementById('f').onsubmit=function(e){
  e.preventDefault();
  if(e.stopPropagation)e.stopPropagation();
  log.innerText='working... (server is running the task, wait ~10s)';
  document.getElementById('go').disabled=true;
  st.className='run';st.innerText='running';
  fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({task:document.getElementById('task').value,
                         auto:document.getElementById('auto').checked})}).then(function(r){
    return r.json();
  }).then(function(j){
    if(j.busy){
      log.innerText='server busy — a run is already in progress, wait and retry.';
      document.getElementById('go').disabled=false;
      st.className='need';st.innerText='busy';
      return;
    }
    poll();
  }).catch(function(err){
    log.innerText='request failed: '+err+' — is uvicorn still running? restart: python -m uvicorn app:app --port 8000 --reload';
    document.getElementById('go').disabled=false;
    st.className='';st.innerText='error';
  });
};
setInterval(poll,1500);
</script></body></html>"""

@app.get("/", response_class=HTMLResponse)
def index():
    return PAGE

@app.post("/run")
def run(body: dict):
    global LAST
    if BUSY["running"]:
        return {"ok": False, "busy": True}
    EVENTS.clear(); LAST = {}
    BUSY["running"] = True
    run_dir = "runs/%s" % uuid.uuid4().hex[:8]
    LAST = {"run_dir": run_dir}
    t = threading.Thread(target=_run_agent,
                         args=(body.get("task", ""), body.get("auto", True), run_dir),
                         daemon=True)
    t.start()
    return {"ok": True, "run_dir": run_dir}

@app.get("/status")
def status():
    return {"running": BUSY["running"], "events": len(EVENTS),
            "done": bool(LAST.get("summary"))}

@app.get("/events")
def events():
    return {"events": EVENTS}

@app.get("/result")
def result():
    return {"summary": LAST.get("summary", ""), "ok": LAST.get("ok"),
            "facts": LAST.get("facts", {}), "needs_user": LAST.get("needs_user")}
