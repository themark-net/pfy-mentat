// #159 Space Invaders verify (Attach view) — cite #159
function paintSI(text, kind){
  const el=document.getElementById('simsg');
  if(!el) return;
  el.textContent=text||'';
  el.className='attach-result'+(kind?(' '+kind):'');
}
function paintSIOpen(text, kind){
  const el=document.getElementById('siopenmsg');
  if(!el) return;
  el.textContent=text||'';
  el.className='attach-result'+(kind?(' '+kind):'');
}
function paintSIPaths(j){
  const abs=document.getElementById('siabs');
  const rel=document.getElementById('sirel');
  const prev=document.getElementById('sipreview');
  const note=document.getElementById('sinote');
  if(abs) abs.textContent=(j&&(j.abs_path||''))||'';
  if(rel) rel.textContent=(j&&(j.rel||j.path||''))||'';
  const task=(j&&(j.task_text||j.task_md||''))||'';
  if(prev) prev.textContent=task;
  if(note) note.textContent=(j&&j.note)||'Session proof: Attach OpenCode + disk artifact — not a board-hosted game';
}
async function postSI(path, body){
  try{
    if(noLiveApi()){ return {ok:false,copy:'FAIL · '+GROK_USE,error:GROK_USE}; }
    const r=await fetch(apiRoot()+path,{method:'POST',headers:{'Content-Type':'application/json'},body:body||'{}'});
    try{return await r.json();}catch(e){return {ok:false,copy:'FAIL',error:String(e)};}
  }catch(e){
    return {ok:false,copy:'FAIL',error:String(e)};
  }
}
async function spaceInvaders(){
  paintSI('invaders…','');
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('space_invaders');
        const j=typeof v==='string'?JSON.parse(v):v;
        if(j && j.ok){ paintSI(j.copy||('PASS invaders · '+(j.path||'')), 'ok'); paintSIPaths(j); }
        else { paintSI((j && (j.copy||j.error))||'FAIL invaders','fail'); }
        await tick();
        return;
      }catch(e){ /* fall through to HTTP */ }
    }
    if(noLiveApi()){ paintSI('FAIL invaders · '+GROK_USE,'fail'); return; }
    const r=await fetch(apiRoot()+'/space-invaders',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    let j={};
    try{j=await r.json();}catch(e){j={ok:false,copy:'FAIL invaders',error:String(e)};}
    if(j && j.ok){ paintSI(j.copy||('PASS invaders · '+(j.path||'')),'ok'); paintSIPaths(j); }
    else paintSI((j && (j.copy||j.error))||'FAIL invaders','fail');
  }catch(e){
    paintSI('FAIL invaders · '+String(e),'fail');
  }
  await tick();
}
async function openSIGame(){
  paintSIOpen('opening game…','');
  try{
    const j=await postSI('/space-invaders/open-game','{}');
    if(j && j.ok){ paintSIOpen(j.copy||'PASS Open game','ok'); paintSIPaths(j); }
    else paintSIOpen((j && (j.copy||j.error))||'FAIL Open game','fail');
  }catch(e){
    paintSIOpen('FAIL Open game · '+String(e),'fail');
  }
}
async function openSIFolder(){
  paintSIOpen('opening folder…','');
  try{
    const j=await postSI('/space-invaders/open-folder','{}');
    if(j && j.ok){ paintSIOpen(j.copy||'PASS Open folder','ok'); paintSIPaths(j); }
    else paintSIOpen((j && (j.copy||j.error))||'FAIL Open folder','fail');
  }catch(e){
    paintSIOpen('FAIL Open folder · '+String(e),'fail');
  }
}
async function copySITask(){
  paintSIOpen('copying TASK…','');
  try{
    const j=await postSI('/space-invaders/copy-task','{}');
    const text=(j && (j.task_text||j.value||''))||'';
    if(j && j.ok && text){
      paintSIPaths(j);
      const ok=await copyText(text);
      paintSIOpen(ok?(j.copy||'PASS Copy TASK'):'FAIL clipboard — select TASK','ok');
      if(!ok) paintSIOpen('FAIL clipboard — select TASK','fail');
    }else{
      paintSIOpen((j && (j.copy||j.error))||'FAIL Copy TASK','fail');
    }
  }catch(e){
    paintSIOpen('FAIL Copy TASK · '+String(e),'fail');
  }
}
document.getElementById('btnsi')&&document.getElementById('btnsi').addEventListener('click',function(){spaceInvaders();});
document.getElementById('btnsiopen')&&document.getElementById('btnsiopen').addEventListener('click',function(){openSIGame();});
document.getElementById('btnsifold')&&document.getElementById('btnsifold').addEventListener('click',function(){openSIFolder();});
document.getElementById('btnsitask')&&document.getElementById('btnsitask').addEventListener('click',function(){copySITask();});
