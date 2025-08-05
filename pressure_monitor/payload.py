import time

def build_payload(readings):
    payloads = []
    ts = time.time()
    for r in readings:
        payloads.append({
            "timestamp": ts,
            "name": r["name"],
            "value": r["value"],
            "status": {"ok": True, "note": "stub"}
        })
    return payloads