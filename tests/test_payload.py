import time
from pressure_monitor.payload import build_payload

def test_payload_structure():
    mock_readings = [
        {"channel": 0, "voltage": 2.5, "value": 50.0},
        {"channel": 2, "voltage": 2.0, "value": 80.0},
    ]

    payload = build_payload(mock_readings)

    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], float)
    assert abs(payload["timestamp"] - time.time()) < 5  # close to now

    assert "readings" in payload
    assert len(payload["readings"]) == 2

    assert payload["readings"][0]["channel"] == 0
    assert payload["readings"][1]["channel"] == 2

    assert "status" in payload
    assert payload["status"]["ok"] is True