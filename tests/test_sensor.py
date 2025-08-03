import pytest
from pressure_monitor.sensor import SensorManager

@pytest.fixture
def mock_config():
    return {
        "sensor": {
            "channels": {
                "0": {"enabled": True,  "name": "sensor0", "max_voltage": 5.0, "max_value": 100.0},
                "1": {"enabled": False, "name": "sensor1", "max_voltage": 5.0, "max_value": 100.0},
                "2": {"enabled": True,  "name": "sensor2", "max_voltage": 5.0, "max_value": 200.0},
                "3": {"enabled": False, "name": "sensor3", "max_voltage": 5.0, "max_value": 100.0}
            }
        }
    }

def test_enabled_channels_only(mock_config):
    sm = SensorManager(mock_config)
    assert sm.enabled_channels == [0, 2], "Should include only enabled channels"

def test_voltage_to_value_conversion(mock_config):
    sm = SensorManager(mock_config)

    # Patch the read_adc_channel method to return 2.5V for all
    sm.read_adc_channel = lambda ch: 2.5

    readings = sm.read_all()
    assert len(readings) == 2

    # Channel 0: 2.5V → 50.0
    assert readings[0]["name"] == "sensor0"
    assert readings[0]["value"] == pytest.approx(50.0)

    # Channel 2: 2.5V → 100.0 (based on max_value = 200.0)
    assert readings[1]["name"] == "sensor2"
    assert readings[1]["value"] == pytest.approx(100.0)
from unittest.mock import patch, MagicMock

@patch("pressure_monitor.sensor.AnalogIn")
@patch("pressure_monitor.sensor.ADS")
@patch("pressure_monitor.sensor.busio.I2C")
@patch("pressure_monitor.sensor.board")
def test_ads1115_integration(mock_board, mock_i2c, mock_ads, mock_analogin, mock_config):
    # Mock AnalogIn to always return 2.5V
    mock_channel = MagicMock()
    mock_channel.voltage = 2.5
    mock_analogin.return_value = mock_channel

    sm = SensorManager(mock_config)
    readings = sm.read_all()

    # Verify names and scaled values
    assert readings[0]["name"] == "sensor0"
    assert readings[0]["value"] == pytest.approx(50.0)
    assert readings[1]["name"] == "sensor2"
    assert readings[1]["value"] == pytest.approx(100.0)