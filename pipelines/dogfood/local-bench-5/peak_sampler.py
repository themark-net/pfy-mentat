#!/usr/bin/env python3
"""Sample runner RSS + GTT + MemAvailable + swap until stop file appears."""
import json, os, sys, time
from pathlib import Path
pid = int(sys.argv[1])
out = Path(sys.argv[2])
stop = Path(sys.argv[3])
peak = {"rss_kib":0,"gtt_used_gib":0,"swap_used_gb":0,"mem_avail_min_gb":9999,"samples":0,"t0":time.time()}
samples=[]
while not stop.exists():
    try:
        rss=int(Path(f"/proc/{pid}/status").read_text().split("VmRSS:")[1].split()[0])
    except Exception:
        if peak["samples"]>0: break
        time.sleep(0.5); continue
    mem={}
    for ln in open("/proc/meminfo"):
        k,v=ln.split(":",1); parts=v.split()
        if parts and parts[0].isdigit(): mem[k]=int(parts[0])
    gtt=int(Path("/sys/class/drm/card1/device/mem_info_gtt_used").read_text())/1024**3
    avail=mem.get("MemAvailable",0)/1024/1024
    swap=(mem.get("SwapTotal",0)-mem.get("SwapFree",0))/1024/1024
    peak["rss_kib"]=max(peak["rss_kib"], rss)
    peak["gtt_used_gib"]=max(peak["gtt_used_gib"], round(gtt,3))
    peak["swap_used_gb"]=max(peak["swap_used_gb"], round(swap,3))
    peak["mem_avail_min_gb"]=min(peak["mem_avail_min_gb"], round(avail,3))
    peak["samples"]+=1
    if peak["samples"]%10==0:
        samples.append({"t":round(time.time()-peak["t0"],1),"rss_gib":round(rss/1024/1024,3),"gtt":round(gtt,3),"avail":round(avail,3),"swap":round(swap,3)})
    time.sleep(1)
peak["rss_gib"]=round(peak["rss_kib"]/1024/1024,3)
peak["elapsed_s"]=round(time.time()-peak["t0"],1)
peak["trace"]=samples[-30:]
out.write_text(json.dumps(peak, indent=2))
print(json.dumps(peak))
