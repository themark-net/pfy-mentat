
function show(v){
  view=v;
  document.querySelectorAll('.view').forEach(el=>el.classList.toggle('on', el.id==='view-'+v));
  document.querySelectorAll('.navbtn').forEach(b=>b.classList.toggle('on', b.dataset.go===v));
  paintAttach();
}
document.querySelectorAll('.navbtn').forEach(b=>b.addEventListener('click',()=>show(b.dataset.go)));
function bindAttach(id, hid){
  const el=document.getElementById(id);
  if(el) el.addEventListener('click',()=>attach(hid));
}
bindAttach('btngrok','grok');
bindAttach('btnopen','opencode');
bindAttach('att-grok','grok');
bindAttach('att-open','opencode');
document.getElementById('btnrefresh').addEventListener('click',()=>refreshNow());
document.getElementById('btncopy').addEventListener('click',()=>copyStub());
document.getElementById('btnstage').addEventListener('click',()=>runStage());
document.getElementById('btnlaunch').addEventListener('click',()=>runEnv());
document.getElementById('btncopyendpoint')&&document.getElementById('btncopyendpoint').addEventListener('click',()=>copyLaunchEndpoint());
document.getElementById('btncopystatus')&&document.getElementById('btncopystatus').addEventListener('click',()=>copyLaunchStatus());
document.getElementById('btnpull').addEventListener('click',()=>runPull());
document.getElementById('btntest').addEventListener('click',()=>runEval());
function paintTools(text, kind){
  const el=document.getElementById('toolsmsg');
  if(!el) return;
  el.textContent=text;
  el.className='attach-result'+(kind?(' '+kind):'');
}
function toolOn(s, id){
  const tools=(s&&s.tools)||{};
  if(id==='mcp') return !!tools.mcp;
  if(id==='write-guard') return !!tools.write_guard;
  if(id==='extra-tools') return (tools.tools_mode||'')==='local_tools';
  return !!((tools.skills||{})[id]);
}
function paintToolRow(s){
  ['one-shot','investigate','agent-loops','hermes-feedback','mcp','write-guard','extra-tools'].forEach(id=>{
    const el=document.getElementById('tool-'+id);
    if(!el) return;
    const on=toolOn(s,id);
    el.textContent=on?'on':'off';
    el.className='live '+(on?'ready':'missing');
  });
}
async function postTool(id, on){
  try{
    if(isTauri()){
      try{
        const v=await window.__TAURI__.core.invoke('set_tool',{id, on});
        return typeof v==='string'?JSON.parse(v):v;
      }catch(e){
        return {ok:false,error:String(e),copy:'FAIL tools',live:'FAIL'};
      }
    }
    if(noLiveApi()) return {ok:false,error:'FAIL',copy:'FAIL tools',live:'FAIL'};
    const r=await fetch(apiRoot()+'/tools',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,on})});
    try{return await r.json();}catch(e){return {ok:false,error:String(e),copy:'FAIL tools',live:'FAIL'};}
  }catch(e){
    return {ok:false,error:String(e),copy:'FAIL tools',live:'FAIL'};
  }
}
async function runTool(id){
  const on=!toolOn(lastSnap,id);
  paintTools('toggling…','');
  try{
    const j=await postTool(id,on);
    if(j && j.ok){
      paintTools(j.copy||('PASS '+id),'ok');
      if(j.tools) lastSnap.tools=j.tools;
      paintToolRow(lastSnap);
    }else{
      paintTools('FAIL '+(j && (j.copy||j.error)||id),'fail');
    }
    await tick();
  }catch(e){
    paintTools('FAIL tools','fail');
  }
}
document.querySelectorAll('[data-tool]').forEach(el=>el.addEventListener('click',()=>runTool(el.getAttribute('data-tool'))));
function chipHtml(c){
  const lv=live(c.live);
  return '<div class=chip><b>'+c.id+'</b> <span class="live '+cls(lv)+'">'+lv+'</span><div class=muted>'+c.role+' · '+c.name+'</div></div>';
}
function setLive(id, val){
  const el=document.getElementById(id);
  const lv=live(val);
  el.textContent=lv;
  el.className='live '+cls(lv);
}
async function tick(){
  try{
    const s=await getSnapshot();
    lastSnap=s||{};
    if(s.error && !(s.chips||[]).length){
      document.getElementById('meta').textContent=s.error;
      document.getElementById('fail').textContent='FAIL  '+(s.blocked_copy||GROK_USE);
      attachMsg=attachMsg||('FAIL  '+(s.blocked_copy||GROK_USE));
      attachKind='fail';
      paintAttach();
      return;
    }
    document.getElementById('meta').textContent=[s.host,s.profile,s.ts].filter(Boolean).join(' · ');
    const d=s.detector||{}, r=s.status_runtime||{};
    const engLive=live(s.engine_live||d.status||'missing');
    const g=(s.chips||[]).find(c=>c.id==='grok')||{};
    const stub=!!(s.active_stub || s.active==='continue' || s.active==='agent-cage');
    ['btngrok','btnopen','att-grok','att-open','btnsi'].forEach(id=>{
      const el=document.getElementById(id);
      if(el) el.disabled=stub;
    });
    document.getElementById('fail').textContent=stub?('FAIL  '+(s.blocked_copy||GROK_USE)):'';
    if(stub && attachKind!=='fail'){
      attachMsg='FAIL  '+(s.blocked_copy||GROK_USE);
      attachKind='fail';
    }else if(!attachMsg && stub){
      attachMsg='FAIL  '+(s.blocked_copy||GROK_USE);
      attachKind='fail';
    }
    paintAttach();
    const showOrg=!s.agent_lane_collapsed && (s.org_messages||[]).length;
    document.getElementById('orgnav').style.display=showOrg?'block':'none';
    if(!showOrg && view==='org') show('loop');
    const attached=s.active||'(none)';
    const verb=lastVerbLabel((s.last_verb&&s.last_verb.verb)||'(none)');
    const when=(s.last_verb&&s.last_verb.when)||'';
    const pid=s.sidecar_pid || '';
    document.getElementById('loop-attached').textContent=attached+(pid?(' pid '+pid):'');
    document.getElementById('loop-last').textContent=verb;
    const elv=envLive(s);
    const envEl=document.getElementById('loop-env');
    envEl.textContent=elv;
    envEl.className='live '+cls(elv.toLowerCase());
    document.getElementById('loop-when').textContent=when;
    const mon=document.getElementById('loop-monitor');
    if(mon){
      const note=s.monitor_note||'';
      const mpid=s.monitor_pid||'';
      mon.textContent=note||(mpid?('pid '+mpid):'(none)');
    }
    const gpath=s.grok_path||g.live||'missing';
    const gEl=document.getElementById('loop-grok');
    if(gEl) setLive('loop-grok', gpath);
    document.getElementById('eng-name').textContent=d.engine||r.engine||'none';
    setLive('eng-live', engLive);
    setLive('eng-grok', g.live);
    const models=s.models||[];
    document.getElementById('eng-models').textContent=models.length?models.join(' · '):'(none)';
    paintToolRow(s);
    const tape=s.tape||[];
    const stage=tape.find(t=>t.id==='env-stage'||t.label==='env-stage')||{};
    const sl=stage.live||'SKIP';
    const stageEl=document.getElementById('stage-live');
    stageEl.textContent=sl;
    stageEl.className='live '+cls((sl||'').toLowerCase());
    document.getElementById('att-now').textContent=attached;
    document.getElementById('att-last').textContent=verb;
    document.getElementById('att-rail').innerHTML=(s.chips||[]).map(chipHtml).join('');
    document.querySelectorAll('[data-start]').forEach(el=>el.addEventListener('click',e=>{e.preventDefault();attach(el.getAttribute('data-start'));}));
    document.querySelectorAll('a.inspect').forEach(el=>el.addEventListener('click',e=>{e.preventDefault(); const t=el.textContent||''; if(t){ copyText(t).then(ok=>paintCopy(ok?'copied':'FAIL clipboard — select the one-liner', ok?'ok':'fail')); } else { paintCopy('FAIL no stub one-liner','fail'); }}));
    if(showOrg){
      const rows=(s.org_messages||[]).map(m=>'<tr><td>'+m.from+' → '+m.to+'</td><td>'+(m.pr||m.issue||'')+'</td><td>'+(m.state||'')+'</td></tr>').join('');
      document.getElementById('org-body').innerHTML='<table>'+rows+'</table>';
    } else {
      document.getElementById('org-body').textContent='no org loop';
    }
  }catch(e){
    document.getElementById('fail').textContent='FAIL  '+GROK_USE;
    attachMsg='FAIL  '+GROK_USE;
    attachKind='fail';
    paintAttach();
  }
}
tick(); setInterval(tick, REFRESH);
