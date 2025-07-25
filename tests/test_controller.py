import time
from pressure_monitor.controller import Controller

def make_controller_with_config():
    config = {
        "sampling": {
            "high_rate_hz": 20.0,
            "low_rate_hz": 0.2,
            "stability_threshold_pct": 1.0,
            "stability_window_sec": 5
        }
    }
    dummy_sensor = None
    dummy_output = None
    return Controller(config, dummy_sensor, dummy_output)

def test_update_history_trims_old_data():
    c = make_controller_with_config()
    now = time.time()

    # Fake readings at t = now - 10 (outside window)
    c._update_history(now - 10, [{"channel": 0, "value": 42.0}])
    # Then current time
    c._update_history(now, [{"channel": 0, "value": 43.0}])

    # Should only keep the recent one
    assert len(c.history[0]) == 1
    assert c.history[0][0][1] == 43.0

def test_is_stable_true_for_flat_readings():
    c = make_controller_with_config()
    now = time.time()

    # Inject steady values
    for i in range(10):
        c._update_history(now - i * 0.1, [{"channel": 0, "value": 50.0}])

    assert c._is_stable() is True

def test_is_stable_false_for_fluctuations():
    c = make_controller_with_config()
    now = time.time()

    # Inject fluctuation above threshold (e.g. 50 to 60 → 20%)
    for i in range(5):
        val = 50.0 if i % 2 == 0 else 60.0
        c._update_history(now - i * 0.1, [{"channel": 0, "value": val}])

    assert c._is_stable() is False