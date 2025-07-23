#!/usr/bin/env python3

import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115, P0, P1, P2, P3
from adafruit_ads1x15.analog_in import AnalogIn
import paho.mqtt.client as mqtt

# MQTT config
MQTT_BROKER = 'localhost'  # Change if broker is elsewhere
MQTT_TOPIC = 'home/sprinkler/pressure'

# Pressure sensor config
PRESSURE_SENSOR_CHANNEL = 0  # Assuming A0

# ADS1115 ref voltage = 3.3V or 5V; confirm wiring on your board.
ADC_VREF = 5.0  # volts
PRESSURE_MAX = 100.0  # psi
SENSOR_VOLTAGE_AT_MAX = 5.0  # volts

channel_map = {
    0: P0,
    1: P1,
    2: P2,
    3: P3
}

def voltage_to_pressure(voltage):
    return (voltage / SENSOR_VOLTAGE_AT_MAX) * PRESSURE_MAX

def main():
    # Initialize I2C bus and ADC
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS1115(i2c)
    
    # If needed: ads.gain = 1

    
    chan = AnalogIn(ads, channel_map[PRESSURE_SENSOR_CHANNEL])

    # MQTT client setup
    #client = mqtt.Client()
    #client.connect(MQTT_BROKER)

    try:
        while True:
            voltage = chan.voltage
            pressure = voltage_to_pressure(voltage)
            payload = {
                'voltage': voltage,
                'pressure_psi': pressure
            }
            print(f"Channel: {PRESSURE_SENSOR_CHANNEL} Pressure: {pressure:.2f} psi (Voltage: {voltage:.2f} V)")
            ##client.publish(MQTT_TOPIC, str(payload))
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == '__main__':
    main()