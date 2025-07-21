# Sprinkler Pressure Monitor

A native Python script to read pressure sensor input via the ADS1115 ADC on an OpenSprinkler Pi system (Raspberry Pi 4) and publish measurements to an MQTT broker.  
The system is designed to run alongside the OpenSprinkler Unified Firmware without interfering with its operation.

---

## Features

- Reads analog input from a 5V 100psi pressure sensor connected to ADS1115 on OSPi v2.0.
- Converts voltage to estimated pressure (PSI).
- Publishes pressure readings to MQTT topic for use with Home Assistant, Grafana, or other consumers.
- Outputs logs to console for troubleshooting.

---

## Dependencies

Python 3 required.

### Python libraries:

- `adafruit-circuitpython-ads1x15`
- `paho-mqtt`

These are listed in `requirements.txt`.

---

## Installation

Clone the repository:

```
git clone https://github.com/yourusername/sprinkler-pressure-monitor.git
cd sprinkler-pressure-monitor
```

Set up a Python virtual environment:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Configuration

By default, the script is configured for:

- MQTT broker: `localhost`
- MQTT topic: `home/sprinkler/pressure`
- Pressure sensor: 0-100 PSI, 0-5V output range.
- ADC channel: A0 on ADS1115.

You can adjust these constants directly in `pressure_monitor.py`.

---

## Usage

Run the script manually:

```
source venv/bin/activate
python pressure_monitor.py
```

Pressure readings will print to the console and publish to MQTT every 5 seconds.

---

## Deployment

When ready for persistent deployment on the Raspberry Pi:

1. Clone this repository to the Pi  
2. Install dependencies using a virtual environment  
3. Run as a background service using `systemd` (sample unit file can be provided later) for auto-start on boot.

---

## Future improvements

- Docker containerization (optional for future isolation).
- Retry/backoff behavior on MQTT disconnect.
- Enhanced sensor calibration logic.

---

## License

MIT License — free to use, modify, and distribute.

---

## Notes

The OpenSprinkler Unified Firmware does **not currently use the ADS1115 ADCs** on OSPi v2.0, so this script is safe to run concurrently without conflict as long as I2C bus access is correctly managed.