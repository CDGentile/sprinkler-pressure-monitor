import time

def build_payload(readings, stable=False):
    payloads = []
    ts = time.time()
    for r in readings:
        payloads.append({
            "timestamp": ts,
            "name": r["name"],
            "value": r["value"],
            "stable": stable,
            "status": {"ok": True, "note": "stub"}
        })
    return payloads