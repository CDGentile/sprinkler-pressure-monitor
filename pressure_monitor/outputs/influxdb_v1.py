"""
InfluxDB 1.x Publisher for writing sensor data directly.

Uses HTTP line protocol - no special InfluxDB client library needed.
Compatible with InfluxDB 1.8 running in the Powerwall-Dashboard stack.
"""

import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class InfluxDBV1Publisher:
    """
    Publisher for writing sensor data directly to InfluxDB 1.x.

    Uses the /write endpoint with line protocol format.
    Includes retry logic for transient failures.
    """

    def __init__(self, config: Dict):
        """
        Initialize the InfluxDB publisher.

        Args:
            config: Full application config dict containing 'influxdb' section
        """
        influx_config = config.get("influxdb", {})

        self.url = influx_config.get("url", "http://192.168.0.18:8086")
        self.database = influx_config.get("database", "sensors")
        self.measurement = influx_config.get("measurement", "pressure")
        self.location = influx_config.get("location", "unknown")

        # Optional authentication
        self.username = influx_config.get("username")
        self.password = influx_config.get("password")

        # Retry configuration
        self.max_retries = influx_config.get("max_retries", 3)
        self.retry_delay = influx_config.get("retry_delay", 1.0)
        self.timeout = influx_config.get("timeout", 10)

        # Build write URL
        self.write_url = urljoin(self.url.rstrip("/") + "/", f"write?db={self.database}")

        # Build auth tuple if credentials provided
        self.auth = None
        if self.username and self.password:
            self.auth = (self.username, self.password)

        # Set up session with retry strategy
        self.session = self._create_session()

        # Test connection on init
        self._test_connection()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _test_connection(self) -> None:
        """Test connection to InfluxDB on startup."""
        ping_url = urljoin(self.url.rstrip("/") + "/", "ping")

        try:
            response = self.session.get(
                ping_url,
                auth=self.auth,
                timeout=self.timeout
            )

            if response.status_code == 204:
                logger.info(
                    f"Connected to InfluxDB 1.x at {self.url}, "
                    f"database: {self.database}"
                )
            else:
                logger.warning(
                    f"InfluxDB ping returned unexpected status: {response.status_code}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to InfluxDB at {self.url}: {e}")
            raise ConnectionError(f"Cannot connect to InfluxDB: {e}") from e

    def _payload_to_line_protocol(self, payload: Dict) -> str:
        """
        Convert a sensor payload to InfluxDB line protocol format.

        Line protocol format:
        measurement,tag1=value1,tag2=value2 field1=value1,field2=value2 timestamp

        Example:
        pressure,sensor=house_branch,location=main_site value=52.4,voltage=2.62,status_ok=true 1711130400123000000

        Args:
            payload: Sensor reading dictionary with keys:
                - timestamp: Unix timestamp (float)
                - name: Sensor name (str)
                - value: Pressure reading (float)
                - voltage: Optional raw voltage (float)
                - status: Dict with 'ok' (bool) and 'note' (str)

        Returns:
            Line protocol formatted string
        """
        # Tags (indexed for fast queries)
        tags = f"sensor={self._escape_tag(payload['name'])}"
        tags += f",location={self._escape_tag(self.location)}"

        # Fields (actual data values)
        fields = []
        fields.append(f"value={payload['value']}")

        # Add voltage if present
        if "voltage" in payload and payload["voltage"] is not None:
            fields.append(f"voltage={payload['voltage']}")

        # Add status fields
        status = payload.get("status", {})
        status_ok = status.get("ok", True)
        fields.append(f"status_ok={str(status_ok).lower()}")

        # Add status note if present and non-empty
        status_note = status.get("note", "")
        if status_note:
            fields.append(f'status_note="{self._escape_field_string(status_note)}"')

        fields_str = ",".join(fields)

        # Convert timestamp to nanoseconds (InfluxDB precision)
        # Use round() to avoid floating-point drift (e.g. 1711130400.123 * 1e9)
        timestamp_ns = round(payload["timestamp"] * 1e9)

        return f"{self.measurement},{tags} {fields_str} {timestamp_ns}"

    @staticmethod
    def _escape_tag(value: str) -> str:
        """Escape special characters in tag values."""
        # Tags can't contain spaces, commas, or equals signs
        return str(value).replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")

    @staticmethod
    def _escape_field_string(value: str) -> str:
        """Escape special characters in field string values."""
        # String fields need quotes escaped
        return str(value).replace('"', '\\"')

    def publish(self, payloads: List[Dict]) -> bool:
        """
        Write sensor payloads to InfluxDB.

        Args:
            payloads: List of sensor reading dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not payloads:
            logger.debug("No payloads to publish")
            return True

        try:
            # Convert all payloads to line protocol
            lines = [self._payload_to_line_protocol(p) for p in payloads]
            data = "\n".join(lines)

            logger.debug(f"Writing {len(lines)} points to InfluxDB")

            response = self.session.post(
                self.write_url,
                data=data,
                auth=self.auth,
                headers={"Content-Type": "text/plain"},
                timeout=self.timeout
            )

            if response.status_code == 204:
                logger.debug(f"Successfully wrote {len(lines)} points to InfluxDB")
                return True
            else:
                logger.error(
                    f"InfluxDB write failed: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.Timeout:
            logger.error(f"InfluxDB write timed out after {self.timeout}s")
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"InfluxDB write error: {e}")
            return False

    def disconnect(self) -> None:
        """Clean shutdown - close the session."""
        logger.info("Closing InfluxDB publisher connection")
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
