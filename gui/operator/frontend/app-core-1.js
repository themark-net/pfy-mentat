
function paintStage(text, kind){
  const el=document.getElementById('stagemsg');
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
async function postEval(){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('test_model');
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL eval',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL eval',live:'FAIL'};
    const r=await fetch(apiRoot()+'/eval',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL eval',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL eval',live:'FAIL'};
  }
}
async function runEval(){
  const btn=document.getElementById('btntest');
  btn.disabled=true;
  paintEval('testing…','');
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postEval();
    if(j && j.ok){
      const c=j.copy||'PASS eval';
      paintEval(c, c.indexOf('SKIP')===0?'muted':(c.indexOf('PASS')===0?'ok':''));
    }else{
      paintEval('FAIL '+(j && (j.copy||j.error)||'eval'),'fail');
    }
    await tick();
    const ts=(lastSnap&&lastSnap.ts)?lastSnap.ts:'';
    if(ts) document.getElementById('meta').textContent=[lastSnap.host,lastSnap.profile,ts].filter(Boolean).join(' · ');
  }catch(e){
    paintEval('FAIL eval','fail');
  }finally{
    btn.disabled=false;
  }
}