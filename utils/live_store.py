# utils/live_store.py (in‑memory)
import time, threading
_live = {"ts": 0, "event": None, "players_online": 0, "motd": "", "latency_ms": None, "version": ""}
_series = []  # list of {"t": ts, "v": players}
_lock = threading.Lock()
CAP_SERIES = 3600  # ~1h @ 1/sec; tune to your posting rate

def update_live(evt: dict) -> None:
    ts = int(evt.get("ts") or time.time())
    v  = int(evt.get("players_online") or 0)
    with _lock:
        _live.update({
            "ts": ts,
            "event": evt.get("event") or "unknown",
            "players_online": v,
            "motd": evt.get("motd") or "",
            "latency_ms": evt.get("latency_ms"),
            "version": evt.get("version") or "",
        })
        _series.append({"t": ts, "v": v})
        if len(_series) > CAP_SERIES:
            del _series[:len(_series)-CAP_SERIES]

def get_snapshot() -> dict:
    with _lock:
        return dict(_live)

def get_players_series() -> list[dict]:
    with _lock:
        return list(_series)
