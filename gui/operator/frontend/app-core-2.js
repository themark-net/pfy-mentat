
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
      paintPull('FAIL '+(j && (j.copy||j.error)||'pull'),'fail');
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
async function runEnv(){
  const btn=document.getElementById('btnlaunch');
  btn.disabled=true;
  paintLaunch('launching env…','');
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postEnv();
    if(j && j.ok){
      const c=j.copy||((j.live||'')==='SKIP'?'SKIP env':'PASS env');
      paintLaunch(c, c.indexOf('SKIP')===0?'muted':(c.indexOf('PASS')===0?'ok':''));
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