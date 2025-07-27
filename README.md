# Sprinkler Pressure Monitor

A modular, test-driven Python system for monitoring water pressure via ADS1115 sensors on Raspberry Pi. Supports dynamic sampling, MQTT publishing, and simulation mode for development without hardware.

---

## 🧱 Architecture Overview

This system reads analog pressure sensors via the ADS1115 ADC and publishes structured payloads over MQTT. Sampling rate is dynamically throttled based on system stability to minimize data volume during steady-state operation. Configuration supports multiple site profiles to enable flexible deployment across different locations, with site-based config selection at runtime.

- 🧠 **SensorManager**: Reads and calibrates pressure from configured ADC channels
- 📦 **PayloadBuilder**: Creates timestamped, structured payloads
- 📤 **OutputManager**: Currently supports MQTT or console
- 🧮 **Controller**: Central loop, manages sampling, stability detection, and publishing
- ⚙️ **Config**: YAML-driven parameters for hardware, timing, output, and site selection
- 🧪 **Test suite**: Pytest coverage across all logic, with integration path validation

---

## 📁 File Structure

```
sprinkler-pressure-monitor/
├── main.py
├── config.yaml
├── requirements.txt
├── pressure_monitor/
│   ├── controller.py
│   ├── config.py
│   ├── sensor.py
│   ├── sensor_sim.py
│   ├── payload.py
│   └── outputs/
│       ├── mqtt.py
│       └── console.py
├── tests/
│   ├── test_sensor.py
│   ├── test_payload.py
│   ├── test_mqtt.py
│   ├── test_controller.py
│   └── test_integration.py
```

---

## 🧪 Simulation Mode

Simulation mode can be enabled or customized via CLI overrides:

- `--simulate-sensor`: Use simulated sensor input instead of real hardware.
- `--simulate-output`: Use console output instead of MQTT publishing.
- `--site`: Select the site configuration to load.

If these flags are not provided, the system defaults to the settings specified in `config.yaml` under the `simulation` section. For example, by default, both sensor simulation and console output can be enabled or disabled according to the config.

---

## 🧾 Example `config.yaml`

```yaml
site: main_site

sites:
  main_site:
    sensor:
      type: ads1115
      channels:
        0:
          enabled: true
          name: house_branch
          max_voltage: 5.0
          max_value: 100.0

  aux_site:
    sensor:
      type: ads1115
      channels:
        0: { enabled: true, name: main_well,         max_voltage: 5.0, max_value: 100.0 }
        1: { enabled: true, name: shop_well,         max_voltage: 5.0, max_value: 100.0 }
        2: { enabled: true, name: irrigation_branch, max_voltage: 5.0, max_value: 100.0 }
        3: { enabled: true, name: runway_well,       max_voltage: 5.0, max_value: 100.0 }

sampling:
  high_rate_hz: 20.0            # Sampling rate during dynamic conditions (Hz)
  low_rate_hz: 0.2              # Sampling rate when stable (Hz)
  stability_threshold_pct: 2.0  # Change threshold to consider data stable (%)
  stability_window_sec: 5       # Time window to evaluate stability (sec)

simulation:
  sensor: true                  # Use simulated sensor input (True/False)
  output: true                  # Use console instead of MQTT (True/False)

mqtt:
  enabled: true
  host: your-broker.local
  port: 1883
  topic: home/sensors/pressure
  qos: 1
```

---

## 🧪 Testing

```bash
pip install -r requirements.txt
pytest
```

Test coverage includes:
- Sensor reading + calibration
- Payload formatting
- MQTT publishing (mocked)
- Stability detection logic
- Full integration path: sensor → payload → output

---

## 🚀 Planned Features

- [ ] Real sensor integration via ADS1115
- [ ] Systemd service definition
- [ ] InfluxDB/Telegraf output (optional backend)
- [ ] Local buffering + replay on reconnect
- [ ] Grafana dashboard templates
- [ ] Multi-device deployment

---

## 🏠 Deployment Targets

This system supports multiple Raspberry Pi devices and deployment scenarios using per-device `config.yaml` entries grouped by site. Site selection is CLI-switchable or defaults to `main_site`. Examples include:

- Main house pressure monitoring (`main_site`)
- Well pump and irrigation system sensors (`aux_site`)
- Shop and remote locations

---

## 📡 Monitoring Stack

This system integrates with a local MQTT + InfluxDB + Grafana stack, optionally including:

- **Mosquitto** (MQTT broker)
- **InfluxDB v2** (time series storage)
- **Grafana** (dashboard interface)
- **Home Assistant** (automation and visibility)

---

## 🧠 Developer Notes

- Designed for resilience and testability
- Simulation allows full dev/test cycle without hardware access
- YAML-driven config enables reuse across devices
- Supports both stdout and MQTT output
- Easily extensible with other outputs (e.g., InfluxDB)

---

## 📜 License

MIT License — free to use, adapt, and build upon.