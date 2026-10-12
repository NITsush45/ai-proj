
var log=document.getElementById('log');
var st=document.getElementById('st');
var exs=document.querySelectorAll('.ex');
for(var i=0;i<exs.length;i++){exs[i].onclick=function(){document.getElementById('task').value=this.getAttribute('data-t');};}
function poll(){
  fetch('/events').then(function(r){return r.json();}).then(function(j){
    log.innerText=(j.events||[]).join('
');log.scrollTop=1e6;
  });
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
}
document.getElementById('f').onsubmit=function(e){
  e.preventDefault();
  log.innerText='working...';
  document.getElementById('go').disabled=true;
  st.className='run';st.innerText='running';
  fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({task:document.getElementById('task').value,
                         auto:document.getElementById('auto').checked})}).then(poll);
};
setInterval(poll,1500);
