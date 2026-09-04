// #155 Space Invaders evidence (Attach view)
function paintSI(text, kind){
  const el=document.getElementById('simsg');
  if(!el) return;
  el.textContent=text||'';
  el.className='attach-result'+(kind?(' '+kind):'');
}
async function spaceInvaders(){
  paintSI('invaders\u2026','');
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('space_invaders');
        const j=typeof v==='string'?JSON.parse(v):v;
        if(j && j.ok){ paintSI(j.copy||('PASS invaders \u00b7 '+(j.path||'')), 'ok'); }
        else { paintSI((j && (j.copy||j.error))||'FAIL invaders','fail'); }
        await tick();
        return;
      }catch(e){ /* fall through to HTTP */ }
    }
    if(noLiveApi()){ paintSI('FAIL invaders \u00b7 '+GROK_USE,'fail'); return; }
    const r=await fetch(apiRoot()+'/space-invaders',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    let j={};
    try{j=await r.json();}catch(e){j={ok:false,copy:'FAIL invaders',error:String(e)};}
    if(j && j.ok) paintSI(j.copy||('PASS invaders \u00b7 '+(j.path||'')),'ok');
    else paintSI((j && (j.copy||j.error))||'FAIL invaders','fail');
  }catch(e){
    paintSI('FAIL invaders \u00b7 '+String(e),'fail');
  }
  await tick();
}
document.getElementById('btnsi')&&document.getElementById('btnsi').addEventListener('click',function(){spaceInvaders();});
