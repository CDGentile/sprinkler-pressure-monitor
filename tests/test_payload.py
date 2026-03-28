import time
from pressure_monitor.payload import build_payload

def test_payload_structure():
    mock_readings = [
        {"name": "house_branch", "value": 50.0},
        {"name": "irrigation_branch", "value": 80.0},
    ]

    payloads = build_payload(mock_readings)

    assert isinstance(payloads, list)
    assert len(payloads) == 2

    for p, expected in zip(payloads, mock_readings):
        assert "timestamp" in p
        assert isinstance(p["timestamp"], float)
        assert abs(p["timestamp"] - time.time()) < 5  # close to now
        assert p["name"] == expected["name"]
        assert p["value"] == expected["value"]
        assert "status" in p
        assert p["status"]["ok"] is True
        assert "stable" in p
        assert p["stable"] is False  # default

def test_payload_stable_flag():
    mock_readings = [{"name": "sensor0", "value": 42.0}]

    payloads_stable = build_payload(mock_readings, stable=True)
    assert payloads_stable[0]["stable"] is True

    payloads_unstable = build_payload(mock_readings, stable=False)
    assert payloads_unstable[0]["stable"] is False