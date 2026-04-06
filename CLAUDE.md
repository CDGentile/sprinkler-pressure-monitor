# CLAUDE.md - Ragsdale Home Monitoring Infrastructure

## Project Overview

This project migrates pressure monitoring from a defunct Karbon 300 server to a RasPi5, consolidating with an existing Powerwall-Dashboard deployment.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RasPi5 (192.168.0.18)                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Powerwall-Dashboard Stack (existing)       │   │
│  │   InfluxDB 1.8 (:8086) │ Grafana (:9000)            │   │
│  │   Databases: powerwall, sensors (new)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Mosquitto MQTT (new)                       │   │
│  │   Port 1883 - for power monitors, future sensors    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
              ▲                           ▲
              │ Direct InfluxDB writes    │ MQTT (future devices)
              │                           │
┌─────────────┴───────────┐   ┌──────────┴────────────┐
│  Sprinkler1             │   │  Sprinkler2           │
│  192.168.0.100          │   │  192.168.0.7          │
│  Site: main_site        │   │  Site: aux_site       │
│  Sensors: house_branch  │   │  Sensors: main_well,  │
│                         │   │  shop_well, irrigation│
│                         │   │  runway_well          │
└─────────────────────────┘   └───────────────────────┘
```

### Current State (Broken)
- Karbon 300 (192.168.0.119): InfluxDB broken, disk full, MQTT down
- Sprinkler Pis: Running Python scripts, trying to send to defunct MQTT
- Telegraf: Running on sprinkler Pis, collecting system metrics (to be disabled)
- RasPi5: Powerwall-Dashboard working, isolated

### Target State
- RasPi5: Unified hub with sensors database + MQTT broker
- Sprinkler Pis: Direct InfluxDB writes (MQTT retained as option)
- Telegraf: Disabled on sprinkler Pis (re-enable after stable)
- Grafana: New dashboard for pressure data

## Network & Devices

| Device | IP | User | Role |
|--------|-----|------|------|
| RasPi5 | 192.168.0.18 | pi | Main hub, InfluxDB, Grafana, MQTT |
| Sprinkler1 | 192.168.0.100 | pi | Pressure monitor (main_site) |
| Sprinkler2 | 192.168.0.7 | pi | Pressure monitor (aux_site) |
| Karbon 300 | 192.168.0.119 | - | Legacy, do not modify |

## Technology Stack

### RasPi5 Services
- **InfluxDB 1.8** (containerized via Powerwall-Dashboard)
  - Port: 8086
  - Existing DB: `powerwall`
  - New DB: `sensors`
  - No authentication (local network only)
- **Grafana** (containerized)
  - Port: 9000
  - Default creds: admin/admin (likely changed)
- **Mosquitto MQTT** (to be installed)
  - Port: 1883
  - No authentication initially

### Sprinkler Monitors
- **Python 3.11.2**
- **Hardware**: ADS1115 ADC reading pressure transducers
- **Repo**: sprinkler-pressure-monitor (on GitHub)
- **Service**: systemd unit `sprinkler-monitor.service`

## Code Repository

**GitHub**: https://github.com/CDGentile/sprinkler-pressure-monitor

### Key Files
```
sprinkler-pressure-monitor/
├── main.py                 # Entry point
├── config.yaml             # Site configuration
├── requirements.txt        # Dependencies
├── pressure_monitor/       # Sprinkler Pi Python code
│   ├── __init__.py
│   ├── controller.py       # Main loop
│   ├── config.py           # Config loading
│   ├── sensor.py           # ADS1115 interface
│   ├── sensor_sim.py       # Simulated sensor for testing
│   ├── payload.py          # Data structure
│   └── outputs/
│       ├── __init__.py
│       ├── console.py      # Console output
│       ├── mqtt.py         # MQTT publisher
│       ├── influxdb_v1.py  # Direct InfluxDB writer
│       └── publisher_manager.py  # Output router
├── infrastructure/         # RasPi5 service configs
│   ├── grafana/
│   │   └── grafana-dashboard-pressure.json
│   └── mqtt-broker/
│       ├── docker-compose.yml
│       └── mosquitto.conf
├── configs/                # Device-specific env files
│   ├── sprinkler1.env
│   └── sprinkler2.env
└── tests/
    └── ...
```

## Configuration

### Environment Variables (.env file, gitignored)
```bash
# InfluxDB connection
INFLUXDB_URL=http://192.168.0.18:8086
INFLUXDB_DATABASE=sensors

# MQTT connection (optional)
MQTT_HOST=192.168.0.18
MQTT_PORT=1883

# Device identity
SITE_NAME=main_site          # or aux_site
CLIENT_ID=sprinkler1         # or sprinkler2
```

### config.yaml Structure
```yaml
sites:
  main_site:
    sensor:
      type: ads1115
      channels:
        0:
          enabled: true
          name: house_branch
          # ... calibration settings

outputs:
  console: false
  mqtt: false           # Disabled by default
  influxdb: true        # Primary output method

influxdb:
  url: ${INFLUXDB_URL:-http://192.168.0.18:8086}
  database: ${INFLUXDB_DATABASE:-sensors}
  measurement: pressure

mqtt:
  host: ${MQTT_HOST:-192.168.0.18}
  port: ${MQTT_PORT:-1883}
  topic: home/sensors/pressure
```

## InfluxDB Schema

### Database: sensors
### Measurement: pressure

**Tags** (indexed):
- `sensor`: Channel name (house_branch, main_well, etc.)
- `location`: Site name (main_site, aux_site)

**Fields**:
- `value`: Pressure reading (float, PSI)
- `voltage`: Raw voltage (float, V)
- `status_ok`: Health status (boolean)

**Example line protocol**:
```
pressure,sensor=house_branch,location=main_site value=52.4,voltage=2.62,status_ok=true 1711130400000000000
```

## Git Workflow

### Branches
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `deploy/configs`: Device-specific configuration templates

### Commit Convention
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation
- `refactor:` Code restructuring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

## Deployment

### Sprinkler Pi Deployment Steps
1. SSH to device
2. `cd ~/sprinkler-pressure-monitor`
3. `git pull origin main`
4. `cp .env.example .env` (first time only)
5. Edit `.env` with device-specific values
6. `pip install -r requirements.txt`
7. `sudo systemctl restart sprinkler-monitor`

### Testing Locally (Simulated Sensor)
```bash
# On laptop with network access to RasPi5
cd sprinkler-pressure-monitor
cp .env.example .env
# Edit .env: INFLUXDB_URL=http://192.168.0.18:8086
python main.py --simulate-sensor --site main_site --verbose
```

## Commands Reference

### RasPi5 (192.168.0.18)
```bash
# InfluxDB commands
docker exec influxdb influx -execute 'SHOW DATABASES'
docker exec influxdb influx -execute 'CREATE DATABASE sensors'
docker exec influxdb influx -database=sensors -execute 'SELECT * FROM pressure LIMIT 10'

# Mosquitto commands
docker exec mosquitto mosquitto_sub -t '#' -v
docker logs mosquitto

# Grafana
# Access at http://192.168.0.18:9000
```

### Sprinkler Pis
```bash
# Service management
sudo systemctl status sprinkler-monitor
sudo systemctl restart sprinkler-monitor
journalctl -u sprinkler-monitor -f

# Disable Telegraf
sudo systemctl stop telegraf
sudo systemctl disable telegraf

# Test script manually
cd ~/sprinkler-pressure-monitor
source venv/bin/activate
python main.py --site main_site --verbose
```

## DO NOT MODIFY

- **Powerwall-Dashboard**: Working, leave untouched
- **Karbon 300**: Legacy system, ignore
- **InfluxDB `powerwall` database**: Contains Powerwall data

## Testing Checklist

Before deploying to production:
- [ ] Unit tests pass: `pytest tests/`
- [ ] Simulated sensor writes to InfluxDB successfully
- [ ] Data visible in Grafana
- [ ] Service starts on boot
- [ ] Handles network interruptions gracefully

## Troubleshooting

### InfluxDB Connection Failed
```bash
# Check InfluxDB is running
docker ps | grep influxdb
# Test connection
curl -I http://192.168.0.18:8086/ping
```

### No Data in Grafana
```bash
# Verify data in InfluxDB
docker exec influxdb influx -database=sensors -execute 'SELECT * FROM pressure ORDER BY time DESC LIMIT 5'
# Check data source in Grafana
# Configuration → Data Sources → Test
```

### Service Won't Start
```bash
journalctl -u sprinkler-monitor -n 50
# Check for missing dependencies, config errors
```
