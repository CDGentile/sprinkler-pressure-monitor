import json
import pytest
from unittest.mock import MagicMock, patch
from pressure_monitor.outputs.mqtt import MqttPublisher

@pytest.fixture
def mqtt_config():
    return {
        "mqtt": {
            "enabled": True,
            "host": "test-broker.local",
            "port": 1883,
            "topic": "home/sensors/test",
            "qos": 1
        }
    }

@pytest.fixture
def mock_payload():
    return {
        "timestamp": 1690000000.0,
        "readings": [{"name": "house_branch", "value": 50.0}],
        "status": {"ok": True, "note": "test"}
    }

@patch("pressure_monitor.outputs.mqtt.mqtt.Client")
def test_mqtt_initialization(mock_mqtt_client, mqtt_config):
    instance = mock_mqtt_client.return_value
    pub = MqttPublisher(mqtt_config)

    mock_mqtt_client.assert_called_once()
    instance.connect.assert_called_once_with("test-broker.local", 1883)

@patch("pressure_monitor.outputs.mqtt.mqtt.Client")
def test_mqtt_publish_payload(mock_mqtt_client, mqtt_config, mock_payload):
    instance = mock_mqtt_client.return_value
    pub = MqttPublisher(mqtt_config)

    pub.publish(mock_payload)

    instance.publish.assert_called_once_with(
        "home/sensors/test",
        json.dumps(mock_payload),
        qos=1
    )