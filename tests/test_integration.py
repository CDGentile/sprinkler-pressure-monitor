import json
from unittest.mock import MagicMock, patch
from pressure_monitor.sensor import SensorManager
from pressure_monitor.payload import build_payload
from pressure_monitor.outputs.mqtt import MqttPublisher

def mock_config():
    return {
        "sensor": {
            "channels": {
                "0": {"enabled": True, "max_voltage": 5.0, "max_value": 100.0},
                "1": {"enabled": False, "max_voltage": 5.0, "max_value": 100.0}
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
    sensor.read_adc_channel = lambda ch: 2.5  # Simulate voltage

    # Get readings → payload
    readings = sensor.read_all()
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