# utils/daily_log.py
import os, json, time, gzip, glob
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs", "mc")
os.makedirs(LOG_DIR, exist_ok=True)

def _day_path(ts:int)->str:
    return os.path.join(LOG_DIR, time.strftime("%Y-%m-%d.ndjson.gz", time.gmtime(ts)))

def append_log(evt: dict) -> None:
    ts = int(evt.get("ts") or time.time())
    line = json.dumps(evt, separators=(",",":")) + "\n"
    with gzip.open(_day_path(ts), "ab") as f:
        f.write(line.encode())

def cleanup_logs(days:int=31)->None:
    cutoff = time.time() - days*86400
    for p in glob.glob(os.path.join(LOG_DIR, "*.ndjson.gz")):
        try:
            d = os.path.basename(p).split(".")[0]
            ts = time.mktime(time.strptime(d, "%Y-%m-%d"))
            if ts < cutoff: os.remove(p)
        except: pass
