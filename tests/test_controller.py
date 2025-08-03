import time
from pressure_monitor.controller import Controller

def make_controller_with_config():
    config = {
        "sampling": {
            "high_rate_hz": 20.0,
            "low_rate_hz": 0.2,
            "stability_threshold_pct": 1.0,
            "stability_window_sec": 5
        },
        "sensor": {
            "channels": {
                "0": {"enabled": True, "max_voltage": 5.0, "max_value": 100.0, "name": "sensor0"}
            }
        }
    }
    dummy_sensor = None
    dummy_output = None
    return Controller(config, dummy_sensor, dummy_output)

def test_update_history_trims_old_data():
    c = make_controller_with_config()
    now = time.time()

    # Fake readings at t = now - 10 (outside window)
    c._update_history(now - 10, [{"name": "sensor0", "value": 42.0}])
    # Then current time
    c._update_history(now, [{"name": "sensor0", "value": 43.0}])

    # Should only keep the recent one
    assert len(c.history["sensor0"]) == 1
    assert c.history["sensor0"][0][1] == 43.0

def test_is_stable_true_for_flat_readings():
    c = make_controller_with_config()
    now = time.time()

    # Inject steady values
    for i in range(10):
        c._update_history(now - i * 0.1, [{"name": "sensor0", "value": 50.0}])

    assert c._is_stable() is True

def test_is_stable_false_for_fluctuations():
    c = make_controller_with_config()
    now = time.time()

    # Inject fluctuation above threshold (e.g. 50.0 ↔ 52.0 → 2% of 100)
    for i in range(5):
        val = 50.0 if i % 2 == 0 else 52.0
        c._update_history(now - i * 0.1, [{"name": "sensor0", "value": val}])

    assert c._is_stable() is False

def test_is_stable_true_for_small_fluctuations():
    c = make_controller_with_config()
    now = time.time()

    # Inject small variation (e.g. 50.0 to 50.5 = 0.5% of 100)
    for i in range(10):
        val = 50.0 if i % 2 == 0 else 50.5
        c._update_history(now - i * 0.1, [{"name": "sensor0", "value": val}])

    assert c._is_stable() is True