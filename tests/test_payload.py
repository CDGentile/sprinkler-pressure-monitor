import time
from pressure_monitor.payload import build_payload

def test_payload_structure():
    mock_readings = [
        ("house_branch", 50.0),
        ("irrigation_branch", 80.0),
    ]

    payload = build_payload(mock_readings)

    assert "timestamp" in payload
    assert isinstance(payload["timestamp"], float)
    assert abs(payload["timestamp"] - time.time()) < 5  # close to now

    assert "readings" in payload
    assert len(payload["readings"]) == 2

    assert payload["readings"][0]["name"] == "house_branch"
    assert payload["readings"][1]["name"] == "irrigation_branch"

    assert "status" in payload
    assert payload["status"]["ok"] is True