"""
Tests for the InfluxDB v1 publisher.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from pressure_monitor.outputs.influxdb_v1 import InfluxDBV1Publisher


@pytest.fixture
def mock_config():
    """Standard test configuration."""
    return {
        "influxdb": {
            "url": "http://localhost:8086",
            "database": "test_sensors",
            "measurement": "pressure",
            "location": "test_site",
            "timeout": 5,
            "max_retries": 2,
        },
        "outputs": {
            "influxdb": True
        }
    }


@pytest.fixture
def sample_payload():
    """Sample sensor payload."""
    return {
        "timestamp": 1711130400.0,
        "name": "test_sensor",
        "value": 52.4,
        "voltage": 2.62,
        "status": {
            "ok": True,
            "note": ""
        }
    }


@pytest.fixture
def sample_payloads(sample_payload):
    """List of sample payloads."""
    return [
        sample_payload,
        {
            "timestamp": 1711130401.456,
            "name": "another_sensor",
            "value": 48.1,
            "voltage": 2.41,
            "status": {
                "ok": True,
                "note": ""
            }
        }
    ]


class TestInfluxDBV1PublisherInit:
    """Tests for publisher initialization."""

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_init_success(self, mock_session_class, mock_config):
        """Test successful initialization."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)

        assert publisher.url == "http://localhost:8086"
        assert publisher.database == "test_sensors"
        assert publisher.measurement == "pressure"
        assert publisher.location == "test_site"

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_init_with_defaults(self, mock_session_class):
        """Test initialization with minimal config uses defaults."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher({"influxdb": {}})

        assert publisher.url == "http://192.168.0.18:8086"
        assert publisher.database == "sensors"
        assert publisher.measurement == "pressure"
        assert publisher.location == "unknown"

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_init_with_auth(self, mock_session_class, mock_config):
        """Test initialization with authentication."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        mock_config["influxdb"]["username"] = "testuser"
        mock_config["influxdb"]["password"] = "testpass"

        publisher = InfluxDBV1Publisher(mock_config)

        assert publisher.auth == ("testuser", "testpass")

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_init_connection_failure(self, mock_session_class, mock_config):
        """Test initialization fails gracefully on connection error."""
        import requests

        mock_session = MagicMock()
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        mock_session_class.return_value = mock_session

        with pytest.raises(ConnectionError):
            InfluxDBV1Publisher(mock_config)


class TestLineProtocolConversion:
    """Tests for payload to line protocol conversion."""

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_basic_conversion(self, mock_session_class, mock_config, sample_payload):
        """Test basic payload conversion."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        line = publisher._payload_to_line_protocol(sample_payload)

        assert line.startswith("pressure,")
        assert "sensor=test_sensor" in line
        assert "location=test_site" in line
        assert "value=52.4" in line
        assert "voltage=2.62" in line
        assert "status_ok=true" in line
        assert "1711130400000000000" in line

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_conversion_with_status_note(self, mock_session_class, mock_config):
        """Test conversion includes status note when present."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)

        payload = {
            "timestamp": 1711130400.0,
            "name": "test_sensor",
            "value": 52.4,
            "status": {
                "ok": False,
                "note": "Sensor reading unstable"
            }
        }

        line = publisher._payload_to_line_protocol(payload)

        assert "status_ok=false" in line
        assert 'status_note="Sensor reading unstable"' in line

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_conversion_escapes_special_chars(self, mock_session_class, mock_config):
        """Test special characters are escaped properly."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)

        payload = {
            "timestamp": 1711130400.0,
            "name": "sensor with spaces",
            "value": 52.4,
            "status": {"ok": True, "note": 'Note with "quotes"'}
        }

        line = publisher._payload_to_line_protocol(payload)

        # Spaces in tags should be escaped
        assert "sensor=sensor\\ with\\ spaces" in line
        # Quotes in fields should be escaped
        assert 'Note with \\"quotes\\"' in line

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_conversion_without_voltage(self, mock_session_class, mock_config):
        """Test conversion handles missing voltage."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)

        payload = {
            "timestamp": 1711130400.0,
            "name": "test_sensor",
            "value": 52.4,
            "status": {"ok": True, "note": ""}
        }

        line = publisher._payload_to_line_protocol(payload)

        assert "voltage=" not in line


class TestPublish:
    """Tests for the publish method."""

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_publish_success(self, mock_session_class, mock_config, sample_payloads):
        """Test successful publish."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session.post.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        result = publisher.publish(sample_payloads)

        assert result is True
        mock_session.post.assert_called_once()

        # Check the data was sent correctly
        call_args = mock_session.post.call_args
        assert "write?db=test_sensors" in call_args[0][0]
        assert call_args[1]["headers"]["Content-Type"] == "text/plain"

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_publish_empty_list(self, mock_session_class, mock_config):
        """Test publish with empty list returns True."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        result = publisher.publish([])

        assert result is True
        mock_session.post.assert_not_called()

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_publish_server_error(self, mock_session_class, mock_config, sample_payloads):
        """Test publish handles server error."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session.post.return_value.status_code = 500
        mock_session.post.return_value.text = "Internal Server Error"
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        result = publisher.publish(sample_payloads)

        assert result is False

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_publish_timeout(self, mock_session_class, mock_config, sample_payloads):
        """Test publish handles timeout."""
        import requests

        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session.post.side_effect = requests.exceptions.Timeout()
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        result = publisher.publish(sample_payloads)

        assert result is False

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_publish_connection_error(self, mock_session_class, mock_config, sample_payloads):
        """Test publish handles connection error."""
        import requests

        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session.post.side_effect = requests.exceptions.ConnectionError()
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        result = publisher.publish(sample_payloads)

        assert result is False


class TestDisconnect:
    """Tests for the disconnect method."""

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_disconnect_closes_session(self, mock_session_class, mock_config):
        """Test disconnect closes the HTTP session."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        publisher = InfluxDBV1Publisher(mock_config)
        publisher.disconnect()

        mock_session.close.assert_called_once()


class TestContextManager:
    """Tests for context manager usage."""

    @patch('pressure_monitor.outputs.influxdb_v1.requests.Session')
    def test_context_manager(self, mock_session_class, mock_config):
        """Test publisher works as context manager."""
        mock_session = MagicMock()
        mock_session.get.return_value.status_code = 204
        mock_session_class.return_value = mock_session

        with InfluxDBV1Publisher(mock_config) as publisher:
            assert publisher is not None

        mock_session.close.assert_called_once()


class TestEscapeFunctions:
    """Tests for escape helper functions."""

    def test_escape_tag_spaces(self):
        """Test tag escaping handles spaces."""
        result = InfluxDBV1Publisher._escape_tag("value with spaces")
        assert result == "value\\ with\\ spaces"

    def test_escape_tag_commas(self):
        """Test tag escaping handles commas."""
        result = InfluxDBV1Publisher._escape_tag("value,with,commas")
        assert result == "value\\,with\\,commas"

    def test_escape_tag_equals(self):
        """Test tag escaping handles equals signs."""
        result = InfluxDBV1Publisher._escape_tag("key=value")
        assert result == "key\\=value"

    def test_escape_field_string_quotes(self):
        """Test field string escaping handles quotes."""
        result = InfluxDBV1Publisher._escape_field_string('value with "quotes"')
        assert result == 'value with \\"quotes\\"'
