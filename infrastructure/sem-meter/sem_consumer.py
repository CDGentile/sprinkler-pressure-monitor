#!/usr/bin/env python3
"""SEM-meter MQTT consumer → InfluxDB writer.

Subscribes to SEM-meter MQTT messages, applies per-circuit scaling,
and writes to InfluxDB 1.8 via HTTP line protocol.
"""

import json
import logging
import os
import signal
import sys
import time

import paho.mqtt.client as mqtt
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from circuit_config import CIRCUITS, MAIN_LEGS

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("sem-consumer")

# Configuration via environment variables
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "SEMMETER/+/HA")

INFLUXDB_URL = os.environ.get("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_DATABASE = os.environ.get("INFLUXDB_DATABASE", "sensors")
INFLUXDB_MEASUREMENT = os.environ.get("INFLUXDB_MEASUREMENT", "power")

# Build a requests session with retry logic
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))

write_url = f"{INFLUXDB_URL}/write?db={INFLUXDB_DATABASE}&precision=s"

running = True


def shutdown(signum, frame):
    global running
    log.info("Shutdown signal received")
    running = False


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)


def scale_circuit(index, raw):
    """Apply scaling factors to raw sense values for a given circuit index."""
    cfg = CIRCUITS[index]
    return {
        "voltage": round(raw[0] * cfg["voltage_scale"], 1),
        "current": round(raw[1] * cfg["current_scale"], 2),
        "power_w": round(raw[2] * cfg["power_scale"], 2),
        "energy_in_kwh": round(raw[3] * cfg["energy_scale"], 3),
        "energy_out_kwh": round(raw[4] * cfg["energy_scale"], 3),
    }


def build_line_protocol(device_id, timestamp_s):
    """Called by on_message after parsing; returns None. Actual work is in on_message."""
    pass  # placeholder — logic is in on_message directly


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        log.info(f"Subscribed to {MQTT_TOPIC}")
    else:
        log.error(f"MQTT connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse MQTT message: {e}")
        return

    sense = payload.get("sense")
    if not sense or not isinstance(sense, list):
        log.warning("Message missing 'sense' array, skipping")
        return

    # Extract device ID from topic: SEMMETER/<device_id>/HA
    topic_parts = msg.topic.split("/")
    device_id = topic_parts[1] if len(topic_parts) >= 2 else "unknown"

    timestamp_s = int(time.time())
    lines = []

    # Process individual circuits
    for idx, raw in enumerate(sense):
        if idx not in CIRCUITS:
            continue
        if len(raw) < 5:
            log.warning(f"Circuit {idx} has {len(raw)} values, expected 5, skipping")
            continue

        cfg = CIRCUITS[idx]
        scaled = scale_circuit(idx, raw)

        # Escape tag values (no spaces/commas in our names, but be safe)
        circuit_name = cfg["name"]
        circuit_type = cfg["type"]

        line = (
            f"{INFLUXDB_MEASUREMENT},"
            f"circuit={circuit_name},"
            f"device={device_id},"
            f"type={circuit_type}"
            f" "
            f"voltage={scaled['voltage']},"
            f"current={scaled['current']},"
            f"power_w={scaled['power_w']},"
            f"energy_in_kwh={scaled['energy_in_kwh']},"
            f"energy_out_kwh={scaled['energy_out_kwh']}"
            f" {timestamp_s}"
        )
        lines.append(line)

    # Compute and write main_total (sum of main legs)
    main_voltage = 0.0
    main_current = 0.0
    main_power = 0.0
    main_energy_in = 0.0
    main_energy_out = 0.0

    for idx in MAIN_LEGS:
        if idx < len(sense) and len(sense[idx]) >= 5:
            scaled = scale_circuit(idx, sense[idx])
            main_current += scaled["current"]
            main_power += scaled["power_w"]
            main_energy_in += scaled["energy_in_kwh"]
            main_energy_out += scaled["energy_out_kwh"]
            main_voltage = max(main_voltage, scaled["voltage"])

    line = (
        f"{INFLUXDB_MEASUREMENT},"
        f"circuit=main_total,"
        f"device={device_id},"
        f"type=main"
        f" "
        f"voltage={round(main_voltage, 1)},"
        f"current={round(main_current, 2)},"
        f"power_w={round(main_power, 2)},"
        f"energy_in_kwh={round(main_energy_in, 3)},"
        f"energy_out_kwh={round(main_energy_out, 3)}"
        f" {timestamp_s}"
    )
    lines.append(line)

    # Write batch to InfluxDB
    body = "\n".join(lines)
    try:
        resp = session.post(write_url, data=body, timeout=10)
        if resp.status_code == 204:
            log.debug(f"Wrote {len(lines)} points to InfluxDB")
        else:
            log.error(f"InfluxDB write failed: {resp.status_code} {resp.text}")
    except requests.RequestException as e:
        log.error(f"InfluxDB connection error: {e}")


def main():
    log.info("SEM-meter consumer starting")
    log.info(f"MQTT: {MQTT_HOST}:{MQTT_PORT} topic={MQTT_TOPIC}")
    log.info(f"InfluxDB: {write_url}")
    log.info(f"Circuits configured: {len(CIRCUITS)} + main_total")

    client = mqtt.Client(client_id="sem-consumer")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    except Exception as e:
        log.error(f"Failed to connect to MQTT broker: {e}")
        sys.exit(1)

    client.loop_start()

    while running:
        time.sleep(1)

    log.info("Shutting down...")
    client.loop_stop()
    client.disconnect()
    log.info("Done")


if __name__ == "__main__":
    main()
