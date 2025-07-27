import argparse
import sys

from pressure_monitor.config import load_config
from pressure_monitor.sensor import SensorManager
from pressure_monitor.sensor_sim import SimulatedSensorManager
from pressure_monitor.controller import Controller
from pressure_monitor.outputs.mqtt import MqttPublisher
from pressure_monitor.outputs.console import ConsolePublisher

def parse_args():
    parser = argparse.ArgumentParser(description="Sprinkler Pressure Monitor")
    parser.add_argument("--simulate-sensor", action="store_true", help="Use simulated sensor input")
    parser.add_argument("--simulate-output", action="store_true", help="Use console output instead of MQTT")
    parser.add_argument("--site", type=str, default="main_site", help="Select configuration site (default: main_site)")
    return parser.parse_args()

def main():
    args = parse_args()
    config = load_config("config.yaml", site=args.site)

    sim_sensor = args.simulate_sensor if args.simulate_sensor else config.get("simulation", {}).get("sensor", False)
    sim_output = args.simulate_output if args.simulate_output else config.get("simulation", {}).get("output", False)

    SensorClass = SimulatedSensorManager if sim_sensor else SensorManager
    OutputClass = ConsolePublisher if sim_output else MqttPublisher

    sensor_manager = SensorClass(config)
    output = OutputClass(config)

    controller = Controller(config, sensor_manager, output)
    controller.run()

if __name__ == "__main__":
    main()