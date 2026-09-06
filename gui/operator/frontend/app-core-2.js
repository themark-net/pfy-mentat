
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
  const el=document.getElementById('launchcopymsg');
  if(!el) return;
  el.textContent=text||'';
  el.className='attach-result'+(kind?(' '+kind):'');
}
async function copyLaunchEndpoint(){
  const el=document.getElementById('launchwhat');
  const j=window.__pfyLaunchNext||{};
  let val=(j.base_url)||(el&&el.dataset.base)||'';
  if(!val && j.next_steps){
    const s=(j.next_steps||[]).find(x=>x&&x.id==='endpoint');
    if(s) val=s.value||'';
  }
  if(!val){ paintLaunchCopy('FAIL no endpoint','fail'); return; }
  const ok=await copyText(val);
  paintLaunchCopy(ok?'PASS Copy endpoint':'FAIL clipboard — select endpoint', ok?'ok':'fail');
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