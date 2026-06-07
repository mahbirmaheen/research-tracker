/* main.js — Research Tracker */

// ── Sidebar toggle ────────────────────────────────────────────────
(function(){
  const toggle=document.getElementById('sb-toggle');
  const sb=document.querySelector('.sidebar');
  const bg=document.getElementById('sb-bg');
  if(!toggle||!sb) return;
  toggle.addEventListener('click',()=>{sb.classList.toggle('open');bg&&bg.classList.toggle('open');});
  bg&&bg.addEventListener('click',()=>{sb.classList.remove('open');bg.classList.remove('open');});
})();

// ── Flash auto-dismiss ────────────────────────────────────────────
document.querySelectorAll('.flash').forEach(el=>{
  setTimeout(()=>{el.style.transition='opacity .4s';el.style.opacity='0';},4000);
  setTimeout(()=>el.remove(),4500);
});

// ── Modal helpers ─────────────────────────────────────────────────
function openModal(id){const m=document.getElementById(id);if(m){m.classList.add('open');document.body.style.overflow='hidden';}}
function closeModal(id){const m=document.getElementById(id);if(m){m.classList.remove('open');document.body.style.overflow='';}}
document.addEventListener('click',e=>{if(e.target.classList.contains('modal-ov'))closeModal(e.target.id);});
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.modal-ov.open').forEach(m=>closeModal(m.id));});

// ── Progress sliders ──────────────────────────────────────────────
document.querySelectorAll('input[type=range][data-lbl]').forEach(sl=>{
  const lbl=document.getElementById(sl.dataset.lbl);
  if(lbl){lbl.textContent=sl.value+'%';sl.addEventListener('input',()=>lbl.textContent=sl.value+'%');}
});

// ── Tab switcher ──────────────────────────────────────────────────
window.switchTab=function(name,btn){
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  const p=document.getElementById('panel-'+name);if(p)p.classList.add('active');
  if(btn)btn.classList.add('active');
};

// ── Confirm delete ────────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(btn=>{
  btn.addEventListener('click',e=>{if(!confirm(btn.dataset.confirm))e.preventDefault();});
});

// ── AJAX stage change (paper detail) ─────────────────────────────
document.querySelectorAll('.stg-btn[data-sid]').forEach(btn=>{
  btn.addEventListener('click',async()=>{
    const pid=document.getElementById('pid-holder')?.value;
    const ns=btn.dataset.sid;
    if(!pid||!ns) return;
    document.querySelectorAll('.stg-btn').forEach(b=>{b.classList.remove('active');});
    btn.classList.add('active');
    try{
      const r=await fetch(`/api/paper/${pid}/stage`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({stage:ns})});
      const d=await r.json();
      if(d.ok){
        const fill=document.getElementById('prog-fill');
        const val=document.getElementById('prog-val');
        if(fill)fill.style.width=d.progress+'%';
        if(val)val.textContent=d.progress+'%';
        toast('Stage updated!','success');
        setTimeout(()=>location.reload(),900);
      } else toast('Error: '+d.error,'error');
    } catch(e){toast('Network error','error');}
  });
});

// ── Inline progress slider (paper detail) ────────────────────────
const ipSlider=document.getElementById('inline-prog');
if(ipSlider){
  ipSlider.addEventListener('change',async()=>{
    const pid=document.getElementById('pid-holder')?.value;
    if(!pid) return;
    const prog=parseInt(ipSlider.value);
    const fill=document.getElementById('prog-fill');
    const val=document.getElementById('prog-val');
    if(fill)fill.style.width=prog+'%';
    if(val)val.textContent=prog+'%';
    try{
      const r=await fetch(`/api/paper/${pid}/progress`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({progress:prog})});
      const d=await r.json();
      if(d.ok)toast('Progress saved','success');
    } catch(e){toast('Save failed','error');}
  });
  // live label
  const lbl=document.getElementById('inline-prog-lbl');
  ipSlider.addEventListener('input',()=>{if(lbl)lbl.textContent=ipSlider.value+'%';});
}

// ── Toast ─────────────────────────────────────────────────────────
function toast(msg,type='info'){
  let c=document.getElementById('toasts');
  if(!c){c=document.createElement('div');c.id='toasts';document.body.appendChild(c);}
  const icons={success:'✓',error:'✗',info:'ℹ'};
  const el=document.createElement('div');
  el.className=`toast ${type}`;
  el.innerHTML=`<span style="font-size:15px">${icons[type]||'ℹ'}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(()=>{el.style.transition='opacity .3s';el.style.opacity='0';},3000);
  setTimeout(()=>el.remove(),3400);
}
