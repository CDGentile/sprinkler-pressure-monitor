import time

def build_payload(readings):
    return {
        "timestamp": time.time(),
        "readings": readings,
        "status": {"ok": True, "note": "stub"}
    }