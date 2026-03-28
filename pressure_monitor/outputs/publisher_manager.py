"""
Publisher Manager - Routes sensor data to configured output destinations.

Supports multiple simultaneous outputs:
- Console (for debugging)
- MQTT (for real-time subscriptions, Home Assistant)
- InfluxDB (for time-series storage and Grafana)
"""

import logging
from typing import Dict, List

from .console import ConsolePublisher
from .mqtt import MqttPublisher
from .influxdb_v1 import InfluxDBV1Publisher

logger = logging.getLogger(__name__)


class PublisherManager:
    """
    Manages multiple output publishers based on configuration.

    Initializes enabled publishers and routes data to all of them.
    Handles graceful shutdown of all connections.
    """

    def __init__(self, config: Dict):
        """
        Initialize publishers based on config.

        Args:
            config: Full application config dict with 'outputs' section
        """
        self.publishers = []
        self.config = config
        outputs_cfg = config.get("outputs", {})

        logger.info("Initializing output publishers...")

        # Console publisher (for debugging)
        if outputs_cfg.get("console", False):
            verbose = outputs_cfg.get("verbose", False)
            logger.info(f"  - Console output enabled (verbose={verbose})")
            self.publishers.append(ConsolePublisher(outputs_cfg, verbose=verbose))

        # MQTT publisher (optional, for Home Assistant, etc.)
        if outputs_cfg.get("mqtt", False):
            try:
                logger.info("  - MQTT output enabled")
                self.publishers.append(MqttPublisher(config))
            except Exception as e:
                logger.error(f"  - MQTT initialization failed: {e}")
                if outputs_cfg.get("mqtt_required", False):
                    raise
                logger.warning("  - Continuing without MQTT (not required)")

        # InfluxDB publisher (primary storage)
        if outputs_cfg.get("influxdb", False):
            try:
                logger.info("  - InfluxDB output enabled")
                self.publishers.append(InfluxDBV1Publisher(config))
            except Exception as e:
                logger.error(f"  - InfluxDB initialization failed: {e}")
                if outputs_cfg.get("influxdb_required", True):
                    raise
                logger.warning("  - Continuing without InfluxDB")

        if not self.publishers:
            logger.warning("No output publishers configured! Data will not be stored.")
        else:
            logger.info(f"Initialized {len(self.publishers)} output publisher(s)")

    def publish(self, payloads: List[Dict]) -> Dict[str, bool]:
        """
        Publish payloads to all configured outputs.

        Args:
            payloads: List of sensor reading dictionaries

        Returns:
            Dict mapping publisher name to success status
        """
        results = {}

        for publisher in self.publishers:
            publisher_name = type(publisher).__name__
            try:
                result = publisher.publish(payloads)
                results[publisher_name] = result if result is not None else True
            except Exception as e:
                logger.error(f"Error in {publisher_name}.publish(): {e}")
                results[publisher_name] = False

        return results

    def disconnect(self) -> None:
        """
        Gracefully disconnect all publishers.

        Called during shutdown to ensure clean connection closure.
        """
        logger.info("Disconnecting all publishers...")

        for publisher in self.publishers:
            publisher_name = type(publisher).__name__
            try:
                if hasattr(publisher, "disconnect"):
                    publisher.disconnect()
                    logger.debug(f"  - {publisher_name} disconnected")
            except Exception as e:
                logger.error(f"  - Error disconnecting {publisher_name}: {e}")

        logger.info("All publishers disconnected")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.disconnect()
        return False

    @property
    def publisher_count(self) -> int:
        """Return the number of active publishers."""
        return len(self.publishers)

    @property
    def publisher_names(self) -> List[str]:
        """Return list of active publisher names."""
        return [type(p).__name__ for p in self.publishers]
