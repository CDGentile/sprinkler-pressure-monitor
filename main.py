import os
import sys
import traceback

from pressure_monitor.config import load_config
from pressure_monitor.sensor import SensorManager
from pressure_monitor.sensor_sim import SimulatedSensorManager
from pressure_monitor.outputs.mqtt import MqttPublisher
from pressure_monitor.outputs.console import ConsolePublisher
from pressure_monitor.controller import Controller

def main():
    try:
        print("Loading configuration...")
        config = load_config("config.yaml")

        USE_SIMULATION = os.getenv("SIMULATE", "false").lower() == "true"

        print("Initializing sensor manager...")
        sensor = SimulatedSensorManager(config) if USE_SIMULATION else SensorManager(config)

        print("Initializing output...")
        if USE_SIMULATION:
            output = ConsolePublisher(config)
        else:
            if config.get("mqtt", {}).get("enabled", False):
                output = MqttPublisher(config)
            else:
                print("MQTT output disabled in config.")
                sys.exit(1)

        print("Starting controller...")
        controller = Controller(config, sensor, output)
        controller.run()

    except Exception:
        print("\n[CRITICAL] Unhandled exception during startup:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()