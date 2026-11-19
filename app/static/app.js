'use strict';
/* Radar product UI, driven by the real API:
     POST /api/check (multipart file, customer_id)      -> result (score, band, level, signals, extracted, tiers_run, advice)
     GET  /api/check/{id}/events (SSE)                  -> tier_start / tier_end / tier_skipped / complete, used to pace the progress panel
     POST /api/check/{id}/chat {message}                -> {score_before, score_after, level, changed, reply, advice, result}
     POST /api/check/{id}/decision {decision}           -> receipt (pay | hold | report)
   The level, score and every finding come from the server. This file only turns them into plain English. */

const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>new Intl.NumberFormat('en-AU',{style:'currency',currency:'AUD'}).format(Number(n)||0);
const CUSTOMER='cust_greenline';

const ICON={
  ok:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/></svg>',
  bell:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 21h4"/></svg>',
  alert:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg>',
  stop:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/></svg>',
  phone:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2"/></svg>',
  vok:'<svg viewBox="0 0 24 24" fill="none" stroke="#1B7F4B" stroke-width="2.4"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l3 3 5-6"/></svg>',
  vno:'<svg viewBox="0 0 24 24" fill="none" stroke="#DA1811" stroke-width="2.4"><circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/></svg>',
  vq:'<svg viewBox="0 0 24 24" fill="none" stroke="#706F7C" stroke-width="2.4"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16v.5"/></svg>',
  rd:'<svg><use href="#radar"/></svg>',
  chev:'<svg><use href="#chev"/></svg>'
};

// Delvin's Radar logo animation. scan=true loops the sonar (loading state); otherwise it plays the intro once.
let RAID=0;
function radarAnim(w,scan){const id='raclip'+(++RAID),sw=(16*w/222).toFixed(2);
  return `<svg class="ra${scan?' scanning':''}" style="width:${w}px;--sw:${sw}px" viewBox="62 -12 222 284" aria-hidden="true">
  <defs><clipPath id="${id}"><rect x="72" y="44" width="156" height="218" rx="22"/><circle cx="228" cy="44" r="80"/></clipPath></defs>
  <path class="doc" d="M94 44 L140 44 A88 88 0 0 0 228 132 L228 240 Q228 262 206 262 L94 262 Q72 262 72 240 L72 66 Q72 44 94 44 Z"/>
  <g clip-path="url(#${id})"><path class="wave p1" d="M228 45 A1 1 0 0 1 227 44"/><path class="wave p2" d="M228 45 A1 1 0 0 1 227 44"/></g>
  <path class="arc" d="M228 94 A50 50 0 0 1 178 44"/>
  <circle class="rip p1" cx="228" cy="44" r="15"/><circle class="rip p2" cx="228" cy="44" r="15"/><circle class="pt" cx="228" cy="44" r="15"/></svg>`;}

// ---------- level copy (docs/brand-kit.md) ----------
const LV={
  low:{cls:'lv-low',css:'low',name:'Low',hex:'#1B7F4B',icon:'ok',title:'Looks good',msg:"Radar checked this invoice and the supplier's details match what we have on file. You're right to go ahead.",next:'You can continue.'},
  lowNew:{cls:'lv-low',css:'low',name:'Low',hex:'#1B7F4B',icon:'ok',title:'Looks good',msg:"With what you've told us, nothing on this invoice looks like a scam. Radar can't confirm a new supplier, so pay the amount you agreed.",next:'You can continue.'},
  medium:{cls:'lv-med',css:'med',name:'Medium',hex:'#F2A900',icon:'bell',title:'Take a quick look',msg:"Something's new or changed on this invoice. Check it with your supplier before you pay.",next:'Have a look before you pay.'},
  high:{cls:'lv-high',css:'high',name:'High',hex:'#DA1811',icon:'alert',title:'Pause before paying',msg:"Radar found serious warning signs on this invoice. Don't pay it until you've checked with the supplier on a number you already have.",next:"Don't pay until you've checked."},
  critical:{cls:'lv-crit',css:'crit',name:'Critical',hex:'#7A0C09',icon:'stop',title:"Don't pay this invoice",msg:'This invoice has been tampered with. This is how invoice scams work. Please report it.',next:'Report it instead of paying.'}
};
const TIERS=['Quick checks','Common red flags','Deeper research','Specialist review'];
const TIERN=['Quick checks','Red flags','Deeper research','Specialist'];

// Plain-English titles for the server's signals. Anything not listed falls back to the server's own name.
const RISK={C1:"Bank details differ from what you've paid before",C2:'Reported by other businesses',C3:"Account name doesn't match",C4:'First time paying this supplier',
  C5:'Seen before on a scam invoice',C6:'Looks like a duplicate invoice',C7:'Unusual amount for this supplier',C8:"The ABN isn't real",C9:"The ACN isn't real",C10:"GST doesn't add up",
  C11:"The BSB doesn't look right",C12:'The PDF was edited in an online editor',C13:'The bank details were edited after the invoice was made',C14:'Hidden instructions in the PDF',
  C15:'New bank details were drawn over the original ones',C16:'The PDF contains hidden code or odd links',C18:'The payment details contradict each other',C19:'"Our bank details have changed"',
  C20:'Pressure to pay fast',C21:"The ABN doesn't match this business",C22:"Charges GST but isn't registered for GST",C23:'Business is very new',C24:'The ABN belongs to someone else',
  C25:"Doesn't match the official payment details",C26:"Email address doesn't match the business",C27:'Looks like a directory or domain-renewal offer',C29:'Spelling and formatting errors',
  C30:'Lookalike email address',C31:'Website or email domain is very new',C32:"The website's owner doesn't match the ABN",C33:"The email domain isn't set up like a real business",
  C34:"Contact details don't match official sources",C35:'Scam reports, or hardly any online presence',C36:"The company isn't registered as active",C39:'Radar found the original bank details',
  C17:"The invoice doesn't add up",C28:"Doesn't fit what your business usually buys",C42:'Payment link or QR code goes somewhere unexpected',C43:'Account is in a personal name, not the business',
  C44:'The invoice dates look wrong',C47:'This account has been used for other, unrelated businesses',C48:'Same invoice template used by unrelated suppliers',C50:'Supplier is emailing from a new address',
  C51:'Unexpected currency or overseas payment',C52:'BPAY details look wrong'};
const GOOD={C1:'Same account you always pay',C8:'ABN is valid',C21:'ABN active and name matches',C13:"Invoice hasn't been edited",C35:'Established online presence'};
// Most telling findings first (tampering and register hits before softer signs).
const PRIORITY=['C15','C13','C39','C2','C47','C5','C14','C8','C24','C43','C25','C24','C3','C1','C30','C19','C20','C35','C18','C10','C31','C23','C26','C4'];
const rank=s=>{const i=PRIORITY.indexOf(s.id);return i<0?99:i;};
const titleOf=s=>{
  if(s.id==='C35'&&s.state==='risk')return /[1-9]\d* scam report/.test(s.evidence)?'Reported as a scam online':'Hardly any online presence';
  return (s.state==='risk'?RISK[s.id]:GOOD[s.id])||s.name;};
// Evidence is shown as the server wrote it, minus internal labels about where demo data came from.
const evidence=s=>String(s.evidence||'').replace(/^(Seed registry|Seeded web evidence|Mock Confirmation of Payee)[: ]\s*/,'').replace(/ in seeded evidence/,'').replace(/; not a registration date/,'');

// ---------- state ----------
let ctx='pay', current=null, checking=false, gen=0, receipt=null, reportPaid='no', chatLog=[], busy=false;
const levelKey=r=>(r.level==='low'&&r.signals.some(s=>s.softened_by))?'lowNew':(r.level in LV?r.level:'medium');
const pm=r=>(r.extracted.payment_methods||[])[0]||{};
const acct=a=>{a=String(a||'').replace(/\s/g,'');return a.length===8?a.slice(0,4)+' '+a.slice(4):a;};
function payTo(r){const p=pm(r);if(p.bsb)return p.bsb+' · '+acct(p.account_number);if(p.payid)return 'PayID '+p.payid;if(p.biller_code)return 'BPAY '+p.biller_code+' · '+p.reference;return '—';}
function verify(r){
  const c3=r.signals.find(s=>s.id==='C3');const m=c3&&String(c3.evidence).match(/(No Match|Close Match|Match)[^;]*;\s*account name\s*(.+)$/i);
  if(!m)return {state:'unknown',head:'Account name not checked',body:'Westpac Verify could not check this account name'};
  const ok=/^match$/i.test(m[1]);
  return ok?{state:'ok',head:'Account name matches',body:m[2]}:{state:'no',head:"Account name doesn't match",body:'Account is held by '+m[2]};
}
function err(where,msg){const e=$('#err-'+where);if(!e)return;e.textContent=msg||'';e.hidden=!msg;}
async function api(url,options={}){
  const res=await fetch(url,options);let body;
  try{body=await res.json();}catch{throw new Error('The server sent an unreadable response. Please try again.');}
  if(!res.ok)throw new Error(typeof body.detail==='string'?body.detail:'Request failed ('+res.status+').');
  return body;
}
function fill(){
  if(!current)return;const r=current,L=LV[levelKey(r)];
  const map={name:r.extracted.supplier_name,amt:money(r.extracted.total),bsbacc:payTo(r),ref:r.extracted.invoice_number||'—',
    lvtext:L.name+' risk · Radar score '+r.score+'/100',hash:r.sha256.slice(0,8)+'…'+r.sha256.slice(-8)+' (SHA-256)',
    receipt:receipt?receipt.receipt_id.slice(0,12).toUpperCase():'—',when:receipt?new Date(receipt.decided_at).toLocaleString('en-AU',{dateStyle:'medium',timeStyle:'short'}):'—'};
  $$('[data-f]').forEach(e=>e.textContent=map[e.dataset.f]??'');
}

// ---------- tier progress ----------
const tierRan=(r,t)=>r.tiers_run.includes(t)||r.signals.some(s=>s.tier===t&&s.disposition==='evidence'&&s.state==='risk');
function tierState(r,t){
  if(!tierRan(r,t))return 'skip';
  const risks=r.signals.filter(s=>s.tier===t&&s.state==='risk');
  if(!risks.length)return 'g';
  return risks.some(s=>s.locked)||r.level==='high'||r.level==='critical'?'r':'w';
}
function tierText(r,t){
  const st=tierState(r,t);
  if(st==='skip'){
    const c1=r.signals.find(s=>s.id==='C1'&&s.state==='reassuring');const n=c1&&String(c1.evidence).match(/(\d+) times/);
    if(r.gate==='hard_stop'&&t>(r.stopped_at??0))return 'Skipped: Radar already found enough to stop';
    return t===2&&n?`Not needed: you've paid this account ${n[1]} times`:'Not needed for this invoice';
  }
  const risks=r.signals.filter(s=>s.tier===t&&s.state==='risk');
  if(!risks.length){const n=r.signals.filter(s=>s.tier===t&&s.state!=='unknown').length;return n?`${n} check${n===1?'':'s'}, nothing found`:'Nothing found';}
  const names=risks.sort((a,b)=>rank(a)-rank(b)).map(titleOf);return names.slice(0,2).join(' · ')+(names.length>2?` · +${names.length-2} more`:'');
}
function stepsHTML(p,r){return TIERS.map((name,t)=>{
  if(!r)return `<div class="step" id="${p}st${t}"><div class="ic">${t+1}</div><div>${name}<div class="d">Waiting</div></div></div>`;
  const st=tierState(r,t);return `<div class="step st-${st}" id="${p}st${t}"><div class="ic">${{g:'✓',w:'!',r:'!',skip:'–'}[st]}</div><div>${name}<div class="d">${esc(tierText(r,t))}</div></div></div>`;}).join('');}
function setStep(p,t,mode,r){
  const e=$('#'+p+'st'+t);if(!e)return;
  if(mode==='run'){e.className='step run';e.querySelector('.ic').textContent=t+1;e.querySelector('.d').textContent='Checking…';return;}
  const st=tierState(r,t);e.className='step st-'+st;e.querySelector('.ic').textContent={g:'✓',w:'!',r:'!',skip:'–'}[st];e.querySelector('.d').textContent=tierText(r,t);
}
function mini(r){const k=levelKey(r),L=LV[k];return `<div class="mini"><div class="t" style="background:${L.hex};${k==='medium'?'color:var(--navy)':''}">${L.name.toUpperCase()} RISK<span>${r.score}/100</span></div><div class="m" style="background:var(--${L.css}-t)"><b>${L.title}.</b> ${L.next} ${ctx==='check'?'':'<a data-go="result" style="text-decoration:underline;cursor:pointer">See what Radar found</a>'}</div></div>`;}
function radarPanel(sel,phase,fileName){
  const el=$(sel),p=sel.slice(1);let body,tag='';
  if(phase==='idle')body=ctx==='pay'
    ?`<div class="idle">Attach the invoice you're paying and Radar checks it before money leaves your account:<ul><li>were the bank details edited after the PDF was made?</li><li>do they match what you've paid this supplier before?</li><li>is the ABN real, the GST right, the sender's website genuine?</li></ul>It takes a few seconds. Westpac Verify still checks the account name as usual.</div>`
    :`<div class="idle">Drop an invoice to start. Radar works outwards, quick checks first, and only digs deeper when something needs a closer look.</div>`;
  else if(phase==='running')body=`<div class="scanning-box">${radarAnim(64,true)}<span id="${p}msg">Reading ${esc(fileName)}…</span></div><div>${stepsHTML(p,null)}</div>`;
  else{body=`<div>${stepsHTML(p,current)}</div>${mini(current)}<button type="button" class="showmap" data-showmap>See how Radar checked it ↗</button>`;tag='<span class="rtag">Checked</span>';}
  el.innerHTML=`<div class="h"><h4 class="ricon">${ICON.rd}Radar invoice check</h4>${tag}</div><div class="b">${body}</div>`;
}
// Evidence checks after a hard stop: show them on the highest tier they belong to.
const evTier=(r,d)=>Math.max(0,...(d.checks||[]).map(id=>(r.signals.find(s=>s.id===id)||{tier:0}).tier));
// Paces the server's SSE tier events so people can follow them; the result itself is already final.
function playProgress(r,p,myGen){return new Promise(resolve=>{
  const q=[];let es=null;
  const done=()=>{try{es&&es.close();}catch{}};
  if(window.EventSource){
    es=new EventSource('/api/check/'+encodeURIComponent(r.check_id)+'/events');
    ['tier_start','tier_end','tier_skipped','evidence_start','evidence_end','complete'].forEach(type=>es.addEventListener(type,ev=>{let d={};try{d=JSON.parse(ev.data);}catch{}q.push([type,d]);if(type==='complete')done();}));
    es.onerror=()=>{done();q.push(['complete',{}]);};
  }else r.tiers_run.forEach(t=>q.push(['tier_start',{tier:t}],['tier_end',{tier:t}])),q.push(['complete',{}]);
  const safety=setTimeout(()=>q.push(['complete',{}]),20000);
  const msg=$('#'+p+'msg');if(msg)msg.textContent='Checking '+r.file_name+'…';
  const loop=()=>{
    if(myGen!==gen){done();clearTimeout(safety);return resolve(false);}
    const e=q.shift();if(!e)return setTimeout(loop,60);
    const [type,d]=e;
    if(type==='tier_start'){setStep(p,d.tier,'run',r);return setTimeout(loop,750);}
    if(type==='evidence_start'){const t=evTier(r,d);setStep(p,t,'run',r);const m=$('#'+p+'msg');if(m)m.textContent='Gathering evidence for the report…';return setTimeout(loop,750);}
    if(type==='evidence_end'){const t=evTier(r,d);setStep(p,t,'done',r);return setTimeout(loop,120);}
    if(type==='tier_end'||type==='tier_skipped'){setStep(p,d.tier,'done',r);return setTimeout(loop,120);}
    clearTimeout(safety);done();TIERS.forEach((_,t)=>setStep(p,t,'done',r));resolve(true);
  };loop();
});}

// ---------- running a check ----------
async function runCheck(file){
  const where=ctx,sel=where==='pay'?'#rpanel':'#rpanel2';err(where,'');
  if(!file)return;
  if(!/\.pdf$/i.test(file.name)||file.size>10*1024*1024){err(where,'Choose a PDF invoice no larger than 10 MB.');return;}
  const myGen=++gen;current=null;receipt=null;chatLog=[];checking=true;
  if(where==='pay')renderPay();
  radarPanel(sel,'running',file.name);
  try{
    const form=new FormData();form.append('file',file);form.append('customer_id',CUSTOMER);
    const [r]=await Promise.all([api('/api/check',{method:'POST',body:form,signal:AbortSignal.timeout(120000)}),new Promise(ok=>setTimeout(ok,600))]);
    if(myGen!==gen)return;
    mapWatch(r.check_id);
    const finished=await playProgress(r,sel.slice(1),myGen);
    if(!finished||myGen!==gen)return;
    current=r;checking=false;radarPanel(sel,'done');
    if(where==='pay')renderPay();else setTimeout(()=>{if(myGen===gen)show('result');},700);
  }catch(e){
    if(myGen!==gen)return;checking=false;radarPanel(sel,'idle');if(where==='pay')renderPay();
    err(where,e.name==='TimeoutError'||e.name==='AbortError'?'The check took too long. Please try again.':'Radar could not check this invoice: '+e.message);
  }
}
async function sample(name){
  if(ctx!=='check'||!$('#v-check').classList.contains('on')){ctx='pay';if(!$('#v-pay').classList.contains('on'))start('pay');}
  try{const res=await fetch('/demo/invoices/'+encodeURIComponent(name));if(!res.ok)throw new Error('Sample invoice not found.');
    await runCheck(new File([await res.blob()],name,{type:'application/pdf'}));}
  catch(e){err(ctx,e.message);}
}

// ---------- Make a payment ----------
function renderPay(){
  const r=current,src='<div><span class="src">From invoice</span></div>';
  $('#attachSlot').innerHTML=r
    ?`<span class="attached" title="${esc(r.file_name)}">${ICON.rd}<b>Invoice attached</b><a id="detach">Remove</a></span>`
    :`<span class="gbtn rbtn" id="attach" role="button" tabindex="0" aria-disabled="${checking}">${ICON.rd}${checking?'Checking…':'Attach invoice'}</span>`;
  $('#attachHint').innerHTML=r?`Radar checked <b>${esc(r.file_name)}</b> and filled in the payee and amount.`:checking?'Radar is checking the invoice. This takes a few seconds.':'<b>Paying an invoice?</b> Attach it and Radar checks it before you pay, then fills in the payee and amount.';
  if(r){
    const p=pm(r),v=verify(r),k=levelKey(r),L=LV[k],ex=r.extracted;
    const how=p.bsb?`<div class="field"><label>I want to pay</label><div class="in sel w60">BSB &amp; account no. ${ICON.chev}</div></div>
        <div class="field"><label>BSB</label><div class="in w25 mono">${esc(p.bsb)}</div>${src}</div>
        <div class="field"><label>Account or Westpac credit card number</label><div class="in w40 mono">${esc(acct(p.account_number))}</div>${src}</div>`
      :p.payid?`<div class="field"><label>I want to pay</label><div class="in sel w60">PayID ${ICON.chev}</div></div><div class="field"><label>PayID</label><div class="in w60">${esc(p.payid)}</div>${src}</div>`
      :`<div class="field"><label>Biller code</label><div class="in w40 mono">${esc(p.biller_code)}</div>${src}</div><div class="field"><label>Customer reference number (CRN)</label><div class="in w40 mono">${esc(p.reference)}</div>${src}</div>`;
    $('#payeeForm').innerHTML=`<div class="newpayee" style="--tip:110px">${how}
      <div class="field"><label>Account name</label><div class="frow"><div class="in w60">${esc(p.account_name||ex.supplier_name)}</div><span class="btn red sm">Check details</span></div>${src}</div>
      <div class="verify ${v.state==='ok'?'ok':'no'}" ${v.state==='unknown'?'style="background:#F3F3F4;border-color:#D5D5DA"':''}>${v.state==='ok'?ICON.vok:v.state==='no'?ICON.vno:ICON.vq}<div><b>${esc(v.head)}</b> · ${esc(v.body)}<div class="s">Westpac Verify · account name checked with the receiving bank</div></div></div>
      <div class="field"><label>Payee nickname <span class="q">?</span></label><div class="in w60">${esc(ex.supplier_name)}</div></div>
      <div class="rban lv-${L.css}">${ICON[L.icon]}<div><b>Radar: ${L.name} risk. ${L.title}.</b> ${L.next} <a data-go="result">See what Radar found</a></div></div></div>`;
    $('#f-amt').textContent=Number(ex.total||0).toLocaleString('en-AU',{minimumFractionDigits:2});
    $('#amtsrc').innerHTML=src;$('#f-ref').textContent=ex.invoice_number||'';
    $('#f-from').innerHTML='Westpac Business One · 032-000 004321 · $12,480.22'+ICON.chev;
  }else{
    $('#payeeForm').innerHTML='';$('#f-amt').textContent='';$('#amtsrc').innerHTML='';$('#f-ref').textContent='';
    $('#f-from').innerHTML='<span style="color:#555">Select an account</span>'+ICON.chev;
  }
  const c=$('#cont');c.disabled=!r;c.textContent=r&&!['low','lowNew'].includes(levelKey(r))?'Review Radar result':'Continue';
  if(!checking)radarPanel('#rpanel',r?'done':'idle');
}

// ---------- Result ----------
function findings(r){
  const risks=r.signals.filter(s=>s.state==='risk'&&s.id!=='C3').sort((a,b)=>(b.locked-a.locked)||(rank(a)-rank(b)));
  const goods=r.signals.filter(s=>s.state==='reassuring'&&GOOD[s.id]);
  return [...risks.map(s=>({ic:s.id==='C39'?'v':s.locked?'r':'w',s})),...goods.map(s=>({ic:'g',s}))];
}
function renderResult(){
  const r=current;if(!r)return show('overview');
  const k=levelKey(r),L=LV[k],score=Math.max(0,Math.min(100,Number(r.score)||0));fill();
  $('#rid').textContent=r.file_name;
  $('#resBack').textContent=ctx==='pay'?'Back to payment':'Back to check';
  const c=2*Math.PI*40;
  $('#level').innerHTML=`<div class="level ${L.cls}"><div class="h">${L.name.toUpperCase()} RISK<small>RADAR</small></div><div class="b">${ICON[L.icon]}<div><h2>${L.title}</h2><p>${L.msg}</p></div><div class="ring"><svg viewBox="0 0 96 96"><circle cx="48" cy="48" r="40" fill="none" stroke="#fff" stroke-width="9"/><circle cx="48" cy="48" r="40" fill="none" stroke="${L.hex}" stroke-width="9" stroke-linecap="round" stroke-dasharray="${Math.max(2,score/100*c)} ${c}"/></svg><div class="n"><div>${score}<small>Radar score</small></div></div></div></div></div>`;
  const v=verify(r);$('#verifyline').innerHTML=`<div class="verifyline">${v.state==='ok'?ICON.vok:v.state==='no'?ICON.vno:ICON.vq}<span><b>Westpac Verify:</b> ${esc(v.head.toLowerCase())} · ${esc(v.body)}</span></div>`;
  const F=findings(r);
  $('#finds').innerHTML=F.length?F.map(({ic,s})=>`<div class="find"><span class="ic ${ic}">${ic==='g'?'✓':ic==='v'?'↺':'!'}</span><div><b>${esc(titleOf(s))}</b><p>${esc(evidence(s))}</p>${s.locked&&s.state==='risk'?'<span class="lock">Confirmed · can\'t be explained away</span>':''}${s.softened_by?'<span class="soft">Explained by your answer</span>':''}</div><span class="tier">${TIERN[s.tier]||''}</span></div>`).join('')
    :'<div class="find"><span class="ic g">✓</span><div><b>No warning signs found</b><p>Every check Radar ran came back clear.</p></div></div>';
  const clear=r.signals.filter(s=>s.state==='neutral').length,skipped=r.signals.filter(s=>s.state==='unknown').length;
  $('#more').textContent=`${clear} other checks found nothing. ${skipped} weren't needed for this invoice or aren't available in this demo.`;
  $('#ctx').innerHTML=ctx==='pay'?`You're in the middle of paying <b>${esc(money(r.extracted.total))}</b>. Nothing has been sent.`:`You're checking this invoice. Nothing will be paid unless you choose to.`;
  const amt=esc(money(r.extracted.total)),kk=L.css==='crit'?'crit':L.css;
  const A=ctx==='pay'?{
    low:`<button class="btn red big" data-modal>Continue to pay ${amt}</button>`,
    med:`<button class="btn red big" data-modal>Continue to pay ${amt}</button><button class="btn ghost big" data-hold>Save for later</button><button class="btn link" data-go="report">Report this invoice</button>`,
    high:`<button class="btn red big" data-go="report">Report this invoice</button><button class="btn ghost big" data-hold>Don't pay for now</button>`,
    crit:`<button class="btn red big" data-go="report">Report this invoice</button><button class="btn ghost big" data-hold>Cancel this payment</button>`}
  :{
    low:`<button class="btn red big" data-topay>Pay this invoice</button><button class="btn ghost big" data-start="overview">Done</button>`,
    med:`<button class="btn red big" data-topay>Pay this invoice</button><button class="btn ghost big" data-hold>Save for later</button><button class="btn link" data-go="report">Report this invoice</button>`,
    high:`<button class="btn red big" data-go="report">Report this invoice</button><button class="btn ghost big" data-hold>Don't pay it</button>`,
    crit:`<button class="btn red big" data-go="report">Report this invoice</button><button class="btn ghost big" data-hold>Don't pay it</button>`};
  $('#actions').innerHTML=A[kk]+(kk==='low'?'':'<button class="btn link" data-payanyway style="font-size:12px;color:var(--muted)">Pay anyway</button>');
  const phone=String(r.advice||'').match(/(0\d[\d ]{7,11}\d)/);
  $('#callout').innerHTML=(kk==='high'||kk==='crit')?`<div class="callout">${ICON.phone}<div><b>Want to check with them? Call first</b><span>${phone?'Only on the number from your earlier invoices:<span class="num">'+esc(phone[1])+'</span>':'Use a number you already have, never one on this invoice.'}</span></div></div>`:'';
  const chatOn=chatLog.length>0||kk==='med'||kk==='high';
  $('#chatbox').style.display=chatOn?'block':'none';
  if(chatOn)renderChat();
}
function renderChat(){
  const r=current,kk=LV[levelKey(r)].css;
  if(!chatLog.length)chatLog.push({who:'bot',text:kk==='med'?'This supplier is new to you. How do you know them?':'Have you spoken to the supplier? Which number did you call?'});
  $('#chat').innerHTML=chatLog.map(m=>`<div class="msg ${m.who}">${esc(m.text)}${m.delta?`<span class="delta">${esc(m.delta)}</span>`:''}</div>`).join('');
  $('#chat').scrollTop=$('#chat').scrollHeight;
  const asked=chatLog.some(m=>m.who==='me');
  const chips=asked?[]:kk==='med'?['Yes, new business. I met the owner at the expo and ordered this.','They emailed me out of the blue']
    :['I called the number on the invoice','I called the number I already had for them','They told me they changed banks'];
  $('#chips').innerHTML=chips.map(c=>`<button class="chip" type="button">${esc(c)}</button>`).join('');
  $$('#chips .chip').forEach(b=>b.onclick=()=>ask(b.textContent));
}
async function ask(message){
  message=String(message||'').trim();if(!current||busy||!message)return;
  busy=true;const myGen=gen,before=LV[levelKey(current)].name;
  chatLog.push({who:'me',text:message});renderChat();$('#msg').value='';$('#chips').innerHTML='';
  try{
    const reply=await api('/api/check/'+encodeURIComponent(current.check_id)+'/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message}),signal:AbortSignal.timeout(45000)});
    if(myGen!==gen)return;
    const names=reply.changed.map(id=>{const s=reply.result.signals.find(x=>x.id===id);return s?titleOf(s).toLowerCase():id;});
    const locked=reply.result.signals.some(s=>s.locked&&s.state==='risk');
    const adv=reply.level==='low'?'':' '+reply.advice;
    const text=names.length?`Thanks. That explains: ${names.join(', ')}.${locked?" Confirmed findings can't be changed by chat.":''}${adv}`:`${reply.reply.replace('Locked findings','Confirmed findings')}${adv}`;
    current=reply.result;const after=LV[levelKey(current)].name;
    chatLog.push({who:'bot',text,delta:`Radar score ${reply.score_before} → ${reply.score_after}`+(before!==after?` · ${before} → ${after}`:' · level unchanged')});
    renderChat();
    if(before!==after)setTimeout(()=>{if(myGen===gen)renderResult();},900);
  }catch(e){if(myGen===gen){chatLog.push({who:'bot',text:'Sorry, that message could not be processed: '+e.message});renderChat();}}
  finally{busy=false;}
}

// ---------- decisions (all recorded by the server with a receipt) ----------
async function decide(decision,where){
  if(!current||busy)return null;busy=true;err(where,'');
  try{receipt=await api('/api/check/'+encodeURIComponent(current.check_id)+'/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision}),signal:AbortSignal.timeout(15000)});fill();return receipt;}
  catch(e){err(where,'Your decision was not saved: '+e.message);return null;}
  finally{busy=false;}
}
function renderReport(){
  const r=current;if(!r)return show('overview');
  $('#repIntro').innerHTML=ctx==='pay'
    ?`This payment of ${esc(money(r.extracted.total))} <b>hasn't been sent</b>. Sending the report cancels it and flags the receiving account so it can't be used against other customers.`
    :'Reporting takes a minute. It helps stop this account being used against other businesses.';
  $('#paidQ').style.display=ctx==='pay'?'none':'block';
}
function renderReported(){
  fill();const paid=ctx==='check'&&reportPaid==='yes';
  $('#repHead').textContent=ctx==='pay'?'Report received · payment cancelled':paid?'Report received · our scams team is on it':'Report received';
  $('#repMoney').textContent=ctx==='pay'?'None. This payment was cancelled.':paid?"You told us you paid it. We'll contact the receiving bank to try to recover it.":'None.';
}
function downloadReceipt(){
  if(!receipt)return;const url=URL.createObjectURL(new Blob([JSON.stringify(receipt,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='radar-receipt-'+receipt.receipt_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}


// ---------- pay anyway: Radar warns, it never blocks ----------
function openWarn(){
  const r=current,L=LV[levelKey(r)],top=findings(r).filter(f=>f.ic!=='g').slice(0,3).map(f=>'<li>'+esc(titleOf(f.s))+'</li>').join('');
  $('#warnBody').innerHTML=`<div class="verdict no" style="margin:0 0 12px;border-color:${L.hex};background:var(--${L.css}-t)">${ICON[L.icon].replace('<svg','<svg style="color:'+L.hex+'"')}<div><h3>Radar: ${L.name} risk</h3>${esc(L.title)}. Radar found:<ul style="margin:6px 0 0">${top}</ul></div></div>
    <p style="font-size:13px;line-height:1.5;margin:0">If this invoice is a scam, the money may not be recoverable once it's sent. If you've confirmed the details with the supplier on a number you already had, you can still pay. Your Radar receipt will record that you chose to pay despite the warning.</p>`;
  $('#warnModal').classList.add('on');
}

// ---------- payments list: Radar receipts and fingerprint comparison ----------
let receiptRows=[],compareId=null;
const LVHEX={low:'#1B7F4B',medium:'#F2A900',high:'#DA1811',critical:'#7A0C09'};
const shortHash=h=>h?h.slice(0,10)+'…'+h.slice(-6):'—';
const longDate=d=>new Date(d).toLocaleDateString('en-AU',{day:'numeric',month:'long',year:'numeric'});
async function renderReceipts(){
  $('#rcList').innerHTML='<div class="emptyrow">Loading…</div>';
  try{receiptRows=await api('/api/receipts?customer_id='+CUSTOMER);}catch(e){$('#rcList').innerHTML='<div class="emptyrow">'+esc(e.message)+'</div>';return;}
  const rows=receiptRows.filter(r=>r.decision==='pay');
  if(!rows.some(r=>r.receipt_id===compareId))compareId=rows.length?rows[0].receipt_id:null;
  $('#rcList').innerHTML=rows.length?`<table class="rct"><tr><th>Date</th><th>Paid to</th><th>Invoice</th><th style="text-align:right">Amount</th><th>Radar check</th><th>Invoice fingerprint</th><th></th></tr>${rows.map(r=>`<tr class="${r.receipt_id===compareId?'sel':''}"><td>${esc(new Date(r.decided_at).toLocaleDateString('en-AU',{day:'numeric',month:'short',year:'numeric'}))}</td><td>${esc(r.payee)}</td><td>${esc(r.invoice_number||'—')}</td><td style="text-align:right">${esc(money(r.amount))}</td><td><span class="lvdot" style="background:${LVHEX[r.level]||'#999'}"></span>${esc((LV[r.level]||{name:r.level}).name)} · ${esc(r.score)}</td><td class="fp">${esc(shortHash(r.sha256))}</td><td><span class="gbtn" data-compare="${esc(r.receipt_id)}">Compare an invoice</span></td></tr>`).join('')}</table>`
    :'<div class="emptyrow">No payments checked by Radar yet. Pay an invoice with <b>Attach invoice</b> and it appears here.</div>';
  renderCompare(null);
}
function renderCompare(res){
  const r=receiptRows.find(x=>x.receipt_id===compareId);
  if(!r){$('#rcCompare').innerHTML='';return;}
  let verdict='';
  if(res){
    verdict=res.match
      ?`<div class="verdict ok">${ICON.ok}<div><h3>Exact match</h3>This is the invoice Radar checked before you paid ${esc(money(r.amount))} to ${esc(r.payee)} on ${esc(longDate(r.decided_at))}.</div></div>`
      :`<div class="verdict no">${ICON.alert}<div><h3>This is not the invoice you paid</h3>The file you dropped is different from the invoice Radar checked before you paid ${esc(money(r.amount))} to ${esc(r.payee)} on ${esc(longDate(r.decided_at))}. Even a one-character change gives a different fingerprint. Your receipt shows exactly which invoice you were sent and paid.</div></div>`;
    verdict+=`<div class="fps"><span>On your receipt</span><code>${esc(res.receipt_sha256)}</code><span>Invoice you dropped</span><code class="${res.match?'':'diff'}">${esc(res.uploaded_sha256)}</code></div>
      <div style="margin-top:12px;display:flex;gap:16px"><span class="gbtn" data-receiptdl="${esc(r.receipt_id)}">Save receipt as proof</span></div>`;
  }
  $('#rcCompare').innerHTML=`<div class="cmp"><div class="h">Compare an invoice with this payment</div><div class="b">
    <p style="margin:0 0 10px;font-size:13px"><b>${esc(r.payee)}</b> · ${esc(r.invoice_number||'')} · ${esc(money(r.amount))}. Got a copy of this invoice that looks different, or a claim that you still owe more? Drop it here. It's only fingerprinted, never stored.</p>
    <div class="drop" id="cmpDrop" role="button" tabindex="0"><h3 style="margin:0 0 4px">Drop the invoice you've been sent</h3><p style="margin:0">or click to choose a PDF</p></div>${verdict}</div></div>`;
  const d=$('#cmpDrop');d.onclick=()=>pickFor('compare');
  ['dragover','dragenter'].forEach(t=>d.addEventListener(t,e=>{e.preventDefault();e.stopPropagation();d.classList.add('over');}));
  ['dragleave','drop'].forEach(t=>d.addEventListener(t,()=>d.classList.remove('over')));
  d.addEventListener('drop',e=>{e.preventDefault();e.stopPropagation();compareFile(e.dataTransfer.files[0]);});
}
async function compareFile(file){
  if(!file||!compareId)return;
  const form=new FormData();form.append('file',file);
  try{renderCompare(await api('/api/receipts/'+encodeURIComponent(compareId)+'/verify',{method:'POST',body:form}));}
  catch(e){$('#rcCompare').insertAdjacentHTML('beforeend','<div class="errbox">'+esc(e.message)+'</div>');}
}
let pickMode='check';
function pickFor(mode){pickMode=mode;$('#file').click();}

// ---------- navigation ----------
const URLS={receipts:'payments/payments-list',overview:'overview',pay:'payments/make-a-payment',check:'payments/check-an-invoice',result:'payments/radar-result',report:'payments/radar-report',reported:'payments/radar-report/confirmation',paid:'payments/confirmation'};
function show(v){
  $('#modal').classList.remove('on');
  $$('.view').forEach(e=>e.classList.toggle('on',e.id==='v-'+v));
  const u=$('#url');if(u)u.textContent='banking.westpac.com.au/secure/banking/'+(URLS[v]||v);
  $('#t-ov').classList.toggle('on',v==='overview');$('#t-pay').classList.toggle('on',v!=='overview');
  $$('.demo [data-start]').forEach(b=>b.classList.toggle('on',['pay','check','overview'].includes(v)&&b.dataset.start===(v==='overview'?'overview':ctx)));
  if(v==='pay')renderPay();
  if(v==='check'){if(!checking)radarPanel('#rpanel2',current?'done':'idle');$('#dropLogo').innerHTML=radarAnim(84,false);}
  if(v==='result')renderResult();
  if(v==='report')renderReport();
  if(v==='reported')renderReported();
  if(v==='paid')fill();
  if(v==='receipts')renderReceipts();
  window.scrollTo(0,0);
}
function start(where){
  gen++;checking=false;current=null;receipt=null;chatLog=[];reportPaid='no';busy=false;
  ['pay','check','result','report','modal'].forEach(w=>err(w,''));
  if(where==='pay'||where==='check')ctx=where;show(where);
}
function openModal(){fill();const L=LV[levelKey(current)];err('modal','');$('#mbar').innerHTML=`<span style="color:${L.hex}">✓</span> Radar check: ${L.name} risk · ${esc(L.title)}`;$('#modal').classList.add('on');}

$('#file').onchange=e=>{const f=e.target.files[0];e.target.value='';if(pickMode==='compare'){pickMode='check';compareFile(f);}else runCheck(f);};
const pick=()=>{if(!checking){pickMode='check';$('#file').click();}};
const drop=$('#checkDrop');
drop.onclick=pick;drop.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();pick();}};
['dragover','dragenter'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('over');}));
['dragleave','drop'].forEach(t=>drop.addEventListener(t,()=>drop.classList.remove('over')));
drop.addEventListener('drop',e=>{e.preventDefault();if(!checking)runCheck(e.dataTransfer.files[0]);});
// Drag an invoice anywhere onto Make a payment to attach it.
let dragDepth=0;
const onPay=()=>$('#v-pay').classList.contains('on')&&!checking;
window.addEventListener('dragenter',e=>{if(!onPay())return;e.preventDefault();dragDepth++;$('#payDrop').classList.add('on');});
window.addEventListener('dragover',e=>{if(onPay())e.preventDefault();});
window.addEventListener('dragleave',()=>{if(--dragDepth<=0){dragDepth=0;$('#payDrop').classList.remove('on');}});
window.addEventListener('drop',e=>{dragDepth=0;$('#payDrop').classList.remove('on');if(!onPay())return;e.preventDefault();const f=e.dataTransfer.files[0];if(f){gen++;current=null;runCheck(f);}});
if(new URLSearchParams(location.search).has('demo'))$('#demobar').hidden=false;
$('#cont').onclick=()=>{if(!current)return;['low','lowNew'].includes(levelKey(current))?openModal():show('result');};
$('#resBack').onclick=()=>show(ctx==='pay'?'pay':'check');
$('#composer').onsubmit=e=>{e.preventDefault();ask($('#msg').value);};
$('#warnGo').onclick=()=>{$('#warnModal').classList.remove('on');if(ctx==='pay')openModal();else{ctx='pay';show('pay');}};
$('#confirmPay').onclick=async()=>{if(await decide('pay','modal'))show('paid');};
$('#sendReport').onclick=async()=>{if(await decide('report','report'))show('reported');};
document.addEventListener('click',async e=>{
  const sm=e.target.closest('[data-sample]');if(sm)return sample(sm.dataset.sample);
  const st=e.target.closest('[data-start]');if(st){e.preventDefault();return start(st.dataset.start);}
  if(e.target.closest('#attach'))return pick();
  if(e.target.closest('#detach')){gen++;current=null;checking=false;chatLog=[];return renderPay();}
  if(e.target.closest('[data-modal]'))return openModal();
  if(e.target.closest('[data-close]'))return $('#modal').classList.remove('on');
  if(e.target.closest('[data-download]'))return downloadReceipt();
  const cmp=e.target.closest('[data-compare]');if(cmp){compareId=cmp.dataset.compare;$$('.rct tr').forEach(t=>t.classList.toggle('sel',!!t.querySelector('[data-compare="'+compareId+'"]')));renderCompare(null);$('#rcCompare').scrollIntoView({behavior:'smooth',block:'start'});return;}
  const rdl=e.target.closest('[data-receiptdl]');if(rdl){const r=receiptRows.find(x=>x.receipt_id===rdl.dataset.receiptdl);if(r){const url=URL.createObjectURL(new Blob([JSON.stringify(r,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='radar-receipt-'+r.receipt_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}return;}
  if(e.target.closest('[data-payanyway]'))return openWarn();
  if(e.target.closest('[data-closewarn]'))return $('#warnModal').classList.remove('on');
  if(e.target.closest('[data-hold]')){if(await decide('hold','result'))start('overview');return;}
  if(e.target.closest('[data-topay]')){ctx='pay';return show('pay');}  // carries the checked invoice into the payment
  const r=e.target.closest('[data-r]');if(r){reportPaid=r.dataset.r;$$('#paidQ .radio').forEach(o=>o.classList.remove('on'));r.classList.add('on');}
  const g=e.target.closest('[data-go]');if(g){e.preventDefault();show(g.dataset.go);}
});
// ---------- Radar map drawer (debug view) ----------
// Embeds /radar?embed=1 beside the app. The iframe loads on first open; each new check is posted to it so the
// map starts at once (it also polls /api/checks/latest as a fallback). Opening after a check replays that check.
let mapLoaded=false,mapLast=null;
function mapWatch(id,replay){mapLast=id;const f=$('#rmapFrame');if(mapLoaded&&f.contentWindow)f.contentWindow.postMessage({radarWatch:id,replay:!!replay},location.origin);}
function mapToggle(force){
  const m=$('#rmap'),open=force===undefined?m.hidden:force;m.hidden=!open;document.body.classList.toggle('rmap-on',open&&!m.classList.contains('wide'));
  if(open&&!mapLoaded){const f=$('#rmapFrame');f.onload=()=>{mapLoaded=true;if(mapLast)mapWatch(mapLast);};f.src='/radar?embed=1';}
}
function mapWide(){const m=$('#rmap');if(m.hidden)mapToggle(true);m.classList.toggle('wide');document.body.classList.toggle('rmap-on',!m.classList.contains('wide'));}
// "See how Radar checked it": open full screen and replay the current check from the start.
function mapShow(){const m=$('#rmap');const wasOpen=!m.hidden;mapToggle(true);m.classList.add('wide');document.body.classList.remove('rmap-on');
  if(wasOpen&&mapLast)mapWatch(mapLast,true);}
$('#mapToggle').onclick=()=>mapToggle();$('#mapClose').onclick=()=>mapToggle(false);$('#mapWide').onclick=mapWide;$('#mapFab').onclick=()=>mapToggle(true);
document.addEventListener('click',e=>{if(e.target.closest('[data-showmap]'))mapShow();});
document.addEventListener('keydown',e=>{if(e.ctrlKey&&e.shiftKey&&(e.key==='X'||e.key==='x')){e.preventDefault();mapToggle();}if(e.ctrlKey&&e.shiftKey&&(e.key==='F'||e.key==='f')){e.preventDefault();mapWide();}});
if(new URLSearchParams(location.search).has('map'))mapToggle(true);

document.addEventListener('keydown',e=>{if(e.key==='Escape'){$('#modal').classList.remove('on');$('#warnModal').classList.remove('on');}if(e.ctrlKey&&e.shiftKey&&(e.key==='D'||e.key==='d')){e.preventDefault();const b=$('#demobar');b.hidden=!b.hidden;}if((e.key==='Enter'||e.key===' ')&&e.target.id==='attach'){e.preventDefault();pick();}});
const q=new URLSearchParams(location.search);
start(['pay','check'].includes(q.get('v'))?q.get('v'):'overview');
