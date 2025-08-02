import json
from unittest.mock import MagicMock, patch
from pressure_monitor.sensor import SensorManager
from pressure_monitor.payload import build_payload
from pressure_monitor.outputs.mqtt import MqttPublisher
import tempfile
import yaml
from pressure_monitor.config import load_config

def mock_config():
    return {
        "sensor": {
            "channels": {
                "0": {
                    "enabled": True,
                    "name": "house_branch",
                    "max_voltage": 5.0,
                    "max_value": 100.0
                },
                "1": {
                    "enabled": False,
                    "name": "unused_sensor",
                    "max_voltage": 5.0,
                    "max_value": 100.0
                }
            }
        },
        "mqtt": {
            "enabled": True,
            "host": "localhost",
            "port": 1883,
            "topic": "home/test/integration",
            "qos": 1
        }
    }

@patch("pressure_monitor.outputs.mqtt.mqtt.Client")
def test_sensor_to_mqtt_flow(mock_mqtt_client):
    cfg = mock_config()

    # Set up SensorManager
    sensor = SensorManager(cfg)
    # Ensure read_adc_channel outputs 2.5 volts for normalization
    sensor.read_adc_channel = lambda ch: 2.5

    readings = sensor.read_all()
    assert isinstance(readings, list)
    assert any(
        r[0] == "house_branch" and round(r[1], 2) == 50.0
        for r in readings
    )
    payload = build_payload(readings)

    # Publish to MQTT
    pub = MqttPublisher(cfg)
    pub.publish(payload)

    # Assertions
    instance = mock_mqtt_client.return_value
    instance.connect.assert_called_once_with("localhost", 1883)
    instance.publish.assert_called_once_with(
        "home/test/integration",
        json.dumps(payload),
        qos=1
    )

def test_load_config_for_specific_site():
    config_data = {
        "sites": {
            "main_site": {
                "sensor": {
                    "channels": {
                        0: {
                            "enabled": True,
                            "name": "house_branch",
                            "max_voltage": 5.0,
                            "max_value": 100.0
                        }
                    }
                }
            },
            "aux_site": {
                "sensor": {
                    "channels": {
                        1: {
                            "enabled": True,
                            "name": "shop_well",
                            "max_voltage": 5.0,
                            "max_value": 100.0
                        }
                    }
                }
            }
        },
        "sampling": {},
        "simulation": {},
        "mqtt": {}
    }

    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        yaml.dump(config_data, tmp)
        tmp.flush()
        loaded_config = load_config(tmp.name, site="aux_site")
        assert loaded_config["sensor"]["channels"][1]["name"] == "shop_well"