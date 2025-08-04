

import pytest
from unittest.mock import MagicMock, patch
from pressure_monitor.outputs.publisher_manager import PublisherManager

def test_enables_console_and_mqtt_publishers():
    mock_config = {
        "outputs": {"console": True, "mqtt": True, "verbose": True},
        "mqtt": {"enabled": True, "host": "localhost", "port": 1883, "topic": "test"}
    }

    with patch("pressure_monitor.outputs.publisher_manager.ConsolePublisher") as MockConsole, \
         patch("pressure_monitor.outputs.publisher_manager.MqttPublisher") as MockMqtt:
        
        manager = PublisherManager(mock_config)

        # Both publishers should be instantiated
        MockConsole.assert_called_once_with(mock_config["outputs"], verbose=True)
        MockMqtt.assert_called_once_with(mock_config["mqtt"])
        assert len(manager.publishers) == 2

def test_publish_forwards_to_all_publishers():
    mock_config = {"outputs": {"console": True}}
    mock_payload = {"readings": [{"name": "sensor0", "value": 42.0}]}

    with patch("pressure_monitor.outputs.publisher_manager.ConsolePublisher") as MockConsole:
        mock_console = MagicMock()
        MockConsole.return_value = mock_console

        manager = PublisherManager(mock_config)
        manager.publish(mock_payload)

        # Ensure publish() is forwarded
        mock_console.publish.assert_called_once_with(mock_payload)