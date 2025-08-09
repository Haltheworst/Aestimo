const monthEl = document.getElementById('month');
const targetEl = document.getElementById('target');
const statusEl = document.getElementById('status');

function note(msg, isErr=false){ statusEl.textContent = msg; statusEl.style.color = isErr ? '#c00' : '#0a6'; }
function norm(m){ return /^\d{4}-\d{2}$/.test(m) ? m : null; }

async function loadTarget(){
  const m = norm(monthEl.value); if(!m) return note('Pick YYYY-MM', true);
  const r = await fetch(`/api/targets?month=${encodeURIComponent(m)}`);
  if(!r.ok) return note('Load failed', true);
  const d = await r.json();
  targetEl.value = d?.target ?? '';
  note(d?.target!=null ? `Loaded ${m}: ${d.target}` : `No target saved for ${m}`);
}

async function saveTarget(){
  const m = norm(monthEl.value); if(!m) return note('Pick YYYY-MM', true);
  const v = parseFloat(targetEl.value); if(isNaN(v) || v<0) return note('Enter non-negative amount', true);
  const r = await fetch('/api/targets', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({month:m, target:v})});
  if(!r.ok) return note('Save failed', true);
  const d = await r.json(); note(`Saved ${d.month}: ${d.target}`);
  alert("Budget saved!")
}

async function clearTarget(){
  const m = norm(monthEl.value); if(!m) return note('Pick YYYY-MM', true);
  if(!confirm(`Clear target for ${m}?`)) return;
  const r = await fetch(`/api/targets?month=${encodeURIComponent(m)}`, {method:'DELETE'});
  if(!r.ok) return note('Clear failed', true);
  targetEl.value = '';
  note(`Cleared ${m}`);
}

document.getElementById('loadBtn').onclick = loadTarget;
document.getElementById('saveBtn').onclick = saveTarget;
document.getElementById('clearBtn').onclick = clearTarget;

// default month = current + auto-load
(function(){
  const now = new Date(), y = now.getFullYear(), m = String(now.getMonth()+1).padStart(2,'0');
  monthEl.value = `${y}-${m}`;
  loadTarget();
})();