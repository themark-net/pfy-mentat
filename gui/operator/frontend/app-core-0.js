const REFRESH=2000;
const LIVE=new Set(['ready','partial','stub','detected-stub','missing','skip']);
const GROK_USE='pfy harness use grok';
let attachMsg="";
let attachKind="";
let view='loop';
let lastSnap={};
let refreshing=false;
function cls(s){return (s||'').replace(/[^a-z-]/g,'');}
function live(s){s=(s||'').toLowerCase(); return LIVE.has(s)?s:'missing';}
function isTauri(){return !!(window.__TAURI__ && window.__TAURI__.core && window.__TAURI__.core.invoke);}
function apiRoot(){
  if(isTauri()) return '';
  if(location.protocol==='http:'||location.protocol==='https:') return '';
  return null;
}
function noLiveApi(){ return apiRoot()===null; }
function lastVerbLabel(v){
  v=(v||'').trim();
  if(v==='env'||v==='launch-env') return 'Launch env';
  return v||'(none)';
}
function envLive(s){
  const tape=(s&&s.tape)||[];
  const inf=((tape.find(t=>t.id==='inference')||{}).live||'SKIP')+'';
  const st=((tape.find(t=>t.id==='env-stage')||{}).live||'SKIP')+'';
  const a=[inf,st].map(x=>x.toUpperCase());
  if(a.includes('FAIL')) return 'FAIL';
  if(a.includes('READY')) return 'READY';
  return 'SKIP';
}
function paintEval(text, kind){
  const el=document.getElementById('evalmsg');
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
function paintPull(text, kind){
  const el=document.getElementById('pullmsg');
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
function paintRefresh(text, kind){
  const el=document.getElementById('refreshmsg');
  if(!el) return;
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
function paintLaunch(text, kind){
  const el=document.getElementById('launchmsg');
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
function paintAttach(){
  const kind=attachKind?(' '+attachKind):'';
  ['attachmsg','attresult'].forEach(id=>{
    const el=document.getElementById(id);
    if(!el) return;
    el.textContent=attachMsg;
    el.className='attach-result'+kind;
  });
}
function paintCopy(text, kind){
  const el=document.getElementById('copymsg');
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
function stubLine(s){
  s=s||lastSnap||{};
  if(s.active_stub || s.active==='continue' || s.active==='agent-cage'){
    return s.blocked_copy || GROK_USE;
  }
  const chips=s.chips||[];
  const active=chips.find(c=>c.id===s.active);
  const c=active && ['stub','detected-stub','missing'].includes(live(active.live))
    ? active
    : chips.find(x=>['stub','detected-stub','missing'].includes(live(x.live)) && (x.one_liner||x.startable===false));
  if(!c) return '';
  return c.one_liner || ('./pfy start '+c.id);
}
async function getSnapshot(){
  try{
    if(isTauri()){
      const v=await window.__TAURI__.core.invoke('snapshot');
      return typeof v==='string'?JSON.parse(v):v;
    }
    if(noLiveApi()) return {error:'FAIL',chips:[],tape:[],blocked_copy:GROK_USE};
    const r=await fetch(apiRoot()+'/snapshot',{cache:'no-store'});
    if(!r.ok) throw new Error('snapshot '+r.status);
    return await r.json();
  }catch(e){
    return {error:String(e),chips:[],tape:[],blocked_copy:GROK_USE};
  }
}
async function postStart(id){
  try{
    if(isTauri()){
      const v=await window.__TAURI__.core.invoke('start_sidecar',{id});
      return typeof v==='string'?JSON.parse(v):v;
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:GROK_USE,live:'FAIL'};
    const r=await fetch(apiRoot()+'/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:GROK_USE,live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:GROK_USE,live:'FAIL'};
  }
}
function paintSessionReach(reach){
  const r=(reach||'').trim()||'(none)';
  ['loop-session','att-session'].forEach(id=>{
    const el=document.getElementById(id);
    if(el) el.textContent=r;
  });
}
async function attach(id){
  attachMsg='attaching '+id+'…';
  attachKind='';
  paintAttach();
  try{
    const j=await postStart(id);
    if(j && j.ok){
      const kind=(j.role==='monitor')?'monitor':id;
      const reach=(j.session_reach||'').trim();
      attachMsg='attached '+kind+(j.pid?(' pid '+j.pid):'')+(reach?(' · '+reach):'');
      attachKind='ok';
      if(reach) paintSessionReach(reach);
      else if(id==='opencode') paintSessionReach('FAIL');
    }else{
      const detail=(j && (j.copy||j.error))||GROK_USE;
      attachMsg='FAIL Attach '+id+' — '+detail;
      attachKind='fail';
      if(id==='opencode') paintSessionReach((j&&j.session_reach)||'FAIL');
    }
  }catch(e){
    attachMsg='FAIL Attach '+id+' — '+GROK_USE;
    attachKind='fail';
    if(id==='opencode') paintSessionReach('FAIL');
  }
  paintAttach();
  await tick();
  paintAttach();
}
async function refreshNow(){
  const btn=document.getElementById('btnrefresh');
  if(refreshing){
    paintRefresh('SKIP refresh','muted');
    return;
  }
  refreshing=true;
  btn.disabled=true;
  document.getElementById('meta').textContent='refreshing…';
  paintRefresh('refreshing…','');
  try{
    await tick();
    const err=lastSnap&&lastSnap.error&&!(lastSnap.chips||[]).length;
    if(err){
      paintRefresh('FAIL refresh','fail');
      document.getElementById('meta').textContent='FAIL refresh';
    }else{
      const ts=(lastSnap&&lastSnap.ts)?lastSnap.ts:'';
      const host=(lastSnap&&lastSnap.host)||'';
      const line=ts?('PASS refresh · '+[host,ts].filter(Boolean).join(' · ')):'PASS refresh · refreshed';
      paintRefresh(line,'ok');
      if(ts) document.getElementById('meta').textContent=[host,lastSnap.profile,ts].filter(Boolean).join(' · ');
      else document.getElementById('meta').textContent=(document.getElementById('meta').textContent||'')+' · refreshed';
    }
  }catch(e){
    document.getElementById('fail').textContent='FAIL  '+GROK_USE;
    document.getElementById('meta').textContent='FAIL refresh';
    paintRefresh('FAIL refresh','fail');
  }finally{
    refreshing=false;
    btn.disabled=false;
  }
}
async function copyText(t){
  try{
    if(navigator.clipboard && navigator.clipboard.writeText){
      await navigator.clipboard.writeText(t);
      return true;
    }
  }catch(e){}
  try{
    const ta=document.createElement('textarea');
    ta.value=t; ta.setAttribute('readonly',''); ta.style.position='fixed'; ta.style.left='-9999px';
    document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, t.length);
    const ok=document.execCommand('copy');
    ta.remove();
    return !!ok;
  }catch(e){ return false; }
}
async function copyStub(){
  paintCopy('copying…','');
  attachMsg='copying…';
  attachKind='';
  paintAttach();
  const line=stubLine(lastSnap);
  if(!line){
    paintCopy('FAIL no stub one-liner','fail');
    attachMsg='FAIL no stub one-liner';
    attachKind='fail';
    paintAttach();
    return;
  }
  const ok=await copyText(line);
  if(ok){
    paintCopy('PASS copied','ok');
    attachMsg='PASS copied';
    attachKind='ok';
  }else{
    paintCopy('FAIL clipboard — select the one-liner','fail');
    attachMsg='FAIL clipboard — select the one-liner';
    attachKind='fail';
  }
  paintAttach();
}