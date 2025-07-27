import time

def build_payload(readings):
    return {
        "timestamp": time.time(),
        "readings": [{"name": name, "value": value} for name, value in readings],
        "status": {"ok": True, "note": "stub"}
    }