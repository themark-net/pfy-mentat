
async function postRecommend(){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('recommend_models');
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL recommend',live:'FAIL',ranked:[]};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL recommend',live:'FAIL',ranked:[],next_step:'Launch env or ./pfy up'};
    const r=await fetch(apiRoot()+'/models/recommend',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL recommend',live:'FAIL',ranked:[]};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL recommend',live:'FAIL',ranked:[]};
  }
}
async function runRecommend(){
  const btn=document.getElementById('btnreco');
  if(btn) btn.disabled=true;
  paintReco('ranking…','');
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postRecommend();
    if(j && j.ok){
      const names=(j.ranked||[]).map(x=>x.name||x).filter(Boolean);
      if(lastSnap){ lastSnap.recommend=names; lastSnap.recommend_ok=true; lastSnap.recommend_copy=j.copy||''; lastSnap.recommend_next=j.next_step||''; lastSnap.recommend_top=j.top||''; }
      paintReco(j.copy||'PASS recommend','ok');
    }else{
      const nxt=(j && j.next_step)||'Launch env or ./pfy up';
      let msg=(j && (j.copy||j.error))||'recommend';
      if(String(msg).indexOf(nxt)<0) msg=msg+' · next: '+nxt;
      if(lastSnap){ lastSnap.recommend=[]; lastSnap.recommend_ok=false; lastSnap.recommend_copy=msg; lastSnap.recommend_next=nxt; }
      paintReco(String(msg).indexOf('FAIL')===0?msg:('FAIL '+msg),'fail');
    }
    await tick();
  }catch(e){
    paintReco('FAIL recommend','fail');
  }finally{
    if(btn) btn.disabled=false;
  }
}
async function postTry(name){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('try_recommended_model',{name});
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL try',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL try',live:'FAIL',next_step:'Launch env or ./pfy up'};
    const r=await fetch(apiRoot()+'/models/try',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name||''})});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL try',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL try',live:'FAIL'};
  }
}
async function runTry(){
  const btn=document.getElementById('btntry');
  const name=((document.getElementById('pullname')||{}).value||'').trim();
  if(btn) btn.disabled=true;
  paintTry('trying…','');
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postTry(name);
    if(j && j.ok){
      if(lastSnap && j.pinned) lastSnap.pinned_model=j.pinned;
      paintTry(j.copy||'PASS try','ok');
    }else{
      const nxt=(j && j.next_step)||'Launch env or ./pfy up (engine pin) · Attach re-probe · TUI reload';
      let msg=(j && (j.copy||j.error))||'try';
      if(String(msg).indexOf('engine pin')<0 && String(msg).indexOf(nxt)<0) msg=msg+' · next: '+nxt;
      paintTry(String(msg).indexOf('FAIL')===0?msg:('FAIL '+msg),'fail');
    }
    await tick();
  }catch(e){
    paintTry('FAIL try','fail');
  }finally{
    if(btn) btn.disabled=false;
  }
}
async function postPull(name){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('pull_model',{name});
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL pull',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL pull',live:'FAIL'};
    const r=await fetch(apiRoot()+'/models/pull',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL pull',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL pull',live:'FAIL'};
  }
}
async function runPull(){
  const btn=document.getElementById('btnpull');
  const name=(document.getElementById('pullname').value||'').trim();
  if(!name){
    paintPull('FAIL pull','fail');
    return;
  }
  btn.disabled=true;
  paintPull('pulling…','');
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postPull(name);
    if(j && j.ok){
      const c=j.copy||'PASS pull';
      paintPull(c, c.indexOf('SKIP')===0?'muted':(c.indexOf('PASS')===0?'ok':''));
    }else{
      // #173: FAIL + next (Launch env / ./pfy up) — no false success
      const nxt=(j && j.next_step)||'Launch env or ./pfy up';
      let msg=(j && (j.copy||j.error))||'pull';
      if(String(msg).indexOf('Launch env')<0 && String(msg).indexOf('./pfy up')<0) msg=msg+' · next: '+nxt;
      paintPull(String(msg).indexOf('FAIL')===0?msg:('FAIL '+msg),'fail');
    }
    await tick();
    const ts=(lastSnap&&lastSnap.ts)?lastSnap.ts:'';
    if(ts) document.getElementById('meta').textContent=[lastSnap.host,lastSnap.profile,ts].filter(Boolean).join(' · ');
  }catch(e){
    paintPull('FAIL pull','fail');
  }finally{
    btn.disabled=false;
  }
}
async function postEnv(){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('launch_env');
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL env',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL env',live:'FAIL'};
    const r=await fetch(apiRoot()+'/env',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL env',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL env',live:'FAIL'};
  }
}
function paintLaunchWhat(j){
  const el=document.getElementById('launchwhat');
  if(!el) return;
  const what=(j&&j.what)||'';
  const base=(j&&j.base_url)||'';
  el.textContent=what||(base?('engine '+base):'');
  el.dataset.base=base||'';
  el.dataset.status='./pfy status';
  const steps=(j&&j.next_steps)||[];
  steps.forEach(function(s){
    if(s&&s.id==='endpoint'&&s.value) el.dataset.base=s.value;
    if(s&&s.id==='status'&&s.value) el.dataset.status=s.value;
  });
  window.__pfyLaunchNext=j||{};
}
function paintLaunchCopy(text, kind){
  const cls='attach-result'+(kind?(' '+kind):'');
  const el=document.getElementById('launchcopymsg');
  if(el){ el.textContent=text||''; el.className=cls; }
  const eng=document.getElementById('engcopymsg');
  if(eng){ eng.textContent=text||''; eng.className=cls; }
}
async function copyLaunchEndpoint(){
  // #175: FreeToken-first live base — not Launch env pin
  const nxt='Launch env or ./pfy up';
  const s=lastSnap||{};
  const u=(s.usage&&typeof s.usage==='object'&&!Array.isArray(s.usage))?s.usage:{};
  let val='';
  if(u && u.ok===false){
    const n=u.next_step||nxt;
    paintLaunchCopy('FAIL copy · next: '+n,'fail');
    return;
  }
  if(u && u.ok!==false && u.endpoint){
    val=String(u.endpoint||'').trim();
  }
  if(!val || val==='(none)'){
    const d=s.detector||{};
    const sr=s.status_runtime||{};
    const st=String(d.status||sr.status||'').trim().toLowerCase();
    let base=String(d.base_url||sr.base_url||sr.endpoint||'').trim();
    if(st==='ready' && base && base!=='(none)'){
      val=base;
    }
  }
  if(!val || val==='(none)'){
    const epEl=document.getElementById('eng-endpoint');
    const ep=(epEl&&epEl.textContent||'').trim();
    if(ep && ep!=='(none)') val=ep;
  }
  if(!val || val==='(none)'){
    paintLaunchCopy('FAIL copy · next: '+nxt,'fail');
    return;
  }
  val=val.replace(/\/+$/,'');
  if(!val.endsWith('/v1')) val=val+'/v1';
  const ok=await copyText(val);
  paintLaunchCopy(ok?'PASS copied':'FAIL copy', ok?'ok':'fail');
}
async function copyLaunchStatus(){
  const el=document.getElementById('launchwhat');
  const j=window.__pfyLaunchNext||{};
  let val='./pfy status';
  if(j.next_steps){
    const s=(j.next_steps||[]).find(x=>x&&x.id==='status');
    if(s&&s.value) val=s.value;
  }else if(el&&el.dataset.status) val=el.dataset.status;
  const ok=await copyText(val);
  paintLaunchCopy(ok?'PASS Copy ./pfy status':'FAIL clipboard — select status', ok?'ok':'fail');
}
async function runEnv(){
  const btn=document.getElementById('btnlaunch');
  btn.disabled=true;
  paintLaunch('launching env…','');
  paintLaunchWhat({});
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postEnv();
    paintLaunchWhat(j||{});
    if(j && j.ok){
      const c=j.copy||((j.live||'')==='SKIP'?'SKIP env':'PASS env');
      paintLaunch(c, c.indexOf('SKIP')===0?'muted':(c.indexOf('PASS')===0?'ok':''));
      if(j.session_reach) paintSessionReach(j.session_reach);
    }else{
      paintLaunch('FAIL '+(j && (j.copy||j.error)||'env'),'fail');
    }
    await tick();
    const ts=(lastSnap&&lastSnap.ts)?lastSnap.ts:'';
    if(ts) document.getElementById('meta').textContent=[lastSnap.host,lastSnap.profile,ts].filter(Boolean).join(' · ');
  }catch(e){
    paintLaunch('FAIL env','fail');
    document.getElementById('fail').textContent='FAIL  env';
  }finally{
    btn.disabled=false;
  }
}
function paintWizard(s){
  s=s||lastSnap||{};
  const rt=s.wizard_runtime||'';
  const rtEl=document.getElementById('wiz-runtime');
  if(rtEl){
    const live=rt?((String(rt).indexOf('ready')>=0||String(s.wizard_live||'').toUpperCase()==='READY')?'READY':'SKIP'):'SKIP';
    rtEl.textContent=rt||live;
    rtEl.className='live '+cls((live||'skip').toLowerCase());
  }
  const lane=document.getElementById('wiz-lane');
  if(lane) lane.textContent=s.wizard_lane_label||s.wizard_lane||'(none)';
  const ts=document.getElementById('wiz-toolsets');
  if(ts) ts.textContent=s.wizard_toolsets||'(none)';
  const en=document.getElementById('wiz-enabled');
  if(en) en.textContent=s.wizard_enabled||'(none)';
  const hs=document.getElementById('wiz-harness');
  if(hs) hs.textContent=s.wizard_harness||'(none)';
  const dec=document.getElementById('wiz-decision');
  if(dec) dec.textContent=s.wizard_decision||s.decision_paint||'○ off';
  const dchip=document.getElementById('wiz-decision-chip');
  if(dchip){
    const bits=[s.decision_chip||'', s.decision_conf||'', s.decision_honesty||'decision ≠ gab auto ≠ local'].filter(Boolean);
    dchip.textContent=bits.join(' · ');
  }
  const rv=document.getElementById('wiz-review');
  if(rv) rv.textContent=s.wizard_review||'(none)';
  const engd=document.getElementById('eng-decision');
  if(engd) engd.textContent=s.decision_core||'compact context · choose model/tool';
  const engh=document.getElementById('eng-decision-honest');
  if(engh) engh.textContent=s.decision_honesty||'decision ≠ gab auto ≠ local';
  document.querySelectorAll('[data-lane]').forEach(b=>b.classList.toggle('on', b.getAttribute('data-lane')===(s.wizard_lane||'')));
  document.querySelectorAll('[data-toolset]').forEach(b=>b.classList.toggle('on', b.getAttribute('data-toolset')===(s.wizard_toolsets||'')));
  document.querySelectorAll('[data-harness]').forEach(b=>b.classList.toggle('on', b.getAttribute('data-harness')===(s.wizard_harness||'')));
  document.querySelectorAll('[data-decision]').forEach(b=>b.classList.toggle('on', b.getAttribute('data-decision')===(s.wizard_decision_path||s.decision_path||'off')));
}
async function postWizard(step, value){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('wizard',{step, value:value||''});
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL wizard',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL wizard',live:'FAIL',next_step:'Launch env or ./pfy up'};
    const r=await fetch(apiRoot()+'/wizard',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({step,value:value||''})});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL wizard',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL wizard',live:'FAIL'};
  }
}
async function postLaunchSession(){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('launch_session');
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL launch',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL launch',live:'FAIL',next_step:'complete wizard review (runtime · lane · toolsets · harness)'};
    const r=await fetch(apiRoot()+'/launch',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL launch',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL launch',live:'FAIL'};
  }
}
async function runWizard(step, value){
  paintLaunch('wizard '+step+'…','');
  try{
    const j=await postWizard(step, value);
    if(j && j.ok){
      paintLaunch(j.copy||('READY '+step),'ok');
      if(lastSnap){
        if(j.runtime) lastSnap.wizard_runtime=j.runtime;
        if(j.lane) lastSnap.wizard_lane=j.lane;
        if(j.lane_label||j.wizard_lane_label) lastSnap.wizard_lane_label=j.lane_label||j.wizard_lane_label;
        if(j.toolsets) lastSnap.wizard_toolsets=j.toolsets;
        if(j.enabled||j.wizard_enabled) lastSnap.wizard_enabled=j.enabled||j.wizard_enabled;
        if(j.harness) lastSnap.wizard_harness=j.harness;
        if(j.review) lastSnap.wizard_review=j.review;
        if(j.path||j.wizard_decision_path) lastSnap.wizard_decision_path=j.path||j.wizard_decision_path;
        if(j.paint||j.wizard_decision) lastSnap.wizard_decision=j.paint||j.wizard_decision;
        if(j.chip_conf||j.decision_conf) lastSnap.decision_conf=j.chip_conf||j.decision_conf;
        if(j.honesty||j.decision_honesty) lastSnap.decision_honesty=j.honesty||j.decision_honesty;
        if(j.chip_decision||j.decision_chip) lastSnap.decision_chip=j.chip_decision||j.decision_chip;
        paintWizard(lastSnap);
      }
    }else{
      const nxt=(j && j.next_step)||'Launch env or ./pfy up';
      let msg=(j && (j.copy||j.error))||step;
      if(String(msg).indexOf(nxt)<0) msg=msg+' · next: '+nxt;
      const skip=String((j&&j.live)||msg).indexOf('SKIP')>=0;
      paintLaunch(skip?msg:(String(msg).indexOf('FAIL')===0?msg:('FAIL '+msg)), skip?'muted':'fail');
    }
    await tick();
  }catch(e){
    paintLaunch('FAIL wizard','fail');
  }
}
async function runLaunchSession(){
  const btn=document.getElementById('btnlaunchsess');
  if(btn) btn.disabled=true;
  paintLaunch('Launch session…','');
  try{
    const j=await postLaunchSession();
    if(j && j.ok && j.usable!==false){
      const reach=(j.session_reach||'').trim();
      paintLaunch(j.copy||('READY Launch session'+(reach?(' · '+reach):'')),'ok');
      if(reach) paintSessionReach(reach);
      attachMsg=j.copy||('attached '+(j.id||j.harness||''));
      attachKind='ok';
      paintAttach();
    }else{
      const nxt=(j && j.next_step)||'complete wizard review (runtime · lane · toolsets · harness)';
      let msg=(j && (j.copy||j.error))||'launch';
      if(String(msg).indexOf(nxt)<0) msg=msg+' · next: '+nxt;
      const skip=String((j&&j.live)||msg).indexOf('SKIP')>=0;
      paintLaunch(skip?msg:(String(msg).indexOf('FAIL')===0?msg:('FAIL '+msg)), skip?'muted':'fail');
      attachMsg=String(msg);
      attachKind=skip?'':'fail';
      paintAttach();
    }
    await tick();
  }catch(e){
    paintLaunch('FAIL Launch session','fail');
  }finally{
    if(btn) btn.disabled=false;
  }
}
async function postStage(){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('run_stage');
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL env-stage',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL env-stage',live:'FAIL'};
    const r=await fetch(apiRoot()+'/stage',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL env-stage',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL env-stage',live:'FAIL'};
  }
}