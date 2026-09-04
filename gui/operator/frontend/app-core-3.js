
async function runStage(){
  const btn=document.getElementById('btnstage');
  btn.disabled=true;
  paintStage('running env-stage…','');
  document.getElementById('meta').textContent='refreshing…';
  try{
    const j=await postStage();
    if(j && j.ok){
      const c=j.copy||'PASS env-stage';
      paintStage(c, c.indexOf('SKIP')===0?'muted':(c.indexOf('PASS')===0?'ok':''));
    }else{
      paintStage('FAIL '+(j && (j.copy||j.error)||'env-stage'),'fail');
    }
    await tick();
    const ts=(lastSnap&&lastSnap.ts)?lastSnap.ts:'';
    if(ts) document.getElementById('meta').textContent=[lastSnap.host,lastSnap.profile,ts].filter(Boolean).join(' · ');
  }catch(e){
    paintStage('FAIL env-stage','fail');
    document.getElementById('fail').textContent='FAIL  env-stage';
  }finally{
    btn.disabled=false;
  }
}
