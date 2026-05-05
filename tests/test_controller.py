import time
from unittest.mock import MagicMock, patch
from pressure_monitor.controller import Controller


def make_config(**overrides):
    config = {
        "sampling": {
            "rate_hz": 0.5,
            "channel_offset_ms": 250,
        },
        "sensor": {
            "channels": {
                "0": {"enabled": True, "max_voltage": 4.5, "max_value": 100.0, "name": "sensor0"}
            }
        },
        "outputs": {"verbose": False},
    }
    config["sampling"].update(overrides)
    return config


def test_controller_init_defaults():
    config = make_config()
    c = Controller(config, sensor=None, output=None)
    assert c.rate_hz == 0.5
    assert c.channel_offset_ms == 250


def test_controller_init_custom_rate():
    config = make_config(rate_hz=1.0, channel_offset_ms=100)
    c = Controller(config, sensor=None, output=None)
    assert c.rate_hz == 1.0
    assert c.channel_offset_ms == 100


def test_controller_calls_staggered_read():
    config = make_config()
    mock_sensor = MagicMock()
    mock_sensor.read_all_staggered.return_value = [{"name": "sensor0", "value": 50.0}]
    mock_output = MagicMock()

    c = Controller(config, mock_sensor, mock_output)

    # Run one cycle by patching time.sleep to raise after first call
    with patch("pressure_monitor.controller.time.sleep", side_effect=KeyboardInterrupt):
        c.run()

    mock_sensor.read_all_staggered.assert_called_once_with(0.25)
    mock_output.publish.assert_called_once()


def test_controller_publishes_payload():
    config = make_config()
    mock_sensor = MagicMock()
    mock_sensor.read_all_staggered.return_value = [
        {"name": "sensor0", "value": 42.0},
        {"name": "sensor1", "value": 55.0},
    ]
    mock_output = MagicMock()

    c = Controller(config, mock_sensor, mock_output)

    with patch("pressure_monitor.controller.time.sleep", side_effect=KeyboardInterrupt):
        c.run()

    payloads = mock_output.publish.call_args[0][0]
    assert len(payloads) == 2
    assert payloads[0]["name"] == "sensor0"
    assert payloads[0]["value"] == 42.0
    assert payloads[1]["name"] == "sensor1"
    assert "stable" not in payloads[0]
