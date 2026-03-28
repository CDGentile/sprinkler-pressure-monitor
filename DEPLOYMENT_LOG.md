# Deployment Log: InfluxDB Migration

## Summary

Migrated pressure monitoring infrastructure from defunct Karbon 300 server (192.168.0.119) to RasPi5 (192.168.0.18), adding direct InfluxDB writes and a Grafana dashboard.

**Date:** 2026-03-28
**Performed by:** cdgentile + Claude Code

---

## Phase 1: RasPi5 Infrastructure Setup

**Device:** RasPi5 (192.168.0.18)

- Created `sensors` database in existing InfluxDB 1.8 container
- Retention policies: `raw_7d` (7-day, default), `downsampled_365d` (365-day)
- Installed Mosquitto MQTT broker via Docker (eclipse-mosquitto:2.0)
  - Ports: 1883 (MQTT), 9001 (WebSocket)
  - Joined `powerwall-dashboard_default` Docker network
  - Anonymous access enabled (local network only)
- Verified: InfluxDB, Mosquitto, and Grafana all operational

## Phase 2: Disable Telegraf

- **Sprinkler1 (192.168.0.100):** Telegraf stopped and disabled. Was spamming errors trying to reach dead Karbon 300. Had consumed 9+ hours CPU on failed writes.
- **Sprinkler2 (192.168.0.7):** Telegraf already dead (5 days), disabled from boot.

## Phase 3: Code Updates

New and modified files committed to `main`:

- `pressure_monitor/outputs/influxdb_v1.py` — New InfluxDB 1.8 publisher using HTTP line protocol with retry logic
- `pressure_monitor/outputs/publisher_manager.py` — Updated to support InfluxDB output, added logging, disconnect(), error handling
- `pressure_monitor/config.py` — Added .env loading via python-dotenv, ${VAR:-default} expansion, type conversion
- `config.yaml` — Added influxdb section, environment variable references, calibration fields
- `.env.example` — Template for device-specific environment configuration
- `configs/sprinkler1.env`, `configs/sprinkler2.env` — Device-specific reference configs
- `requirements.txt` — Added requests, python-dotenv, pytest-cov
- `.gitignore` — Added .env, .DS_Store
- `tests/test_influxdb_publisher.py` — 17 tests for the new publisher

All 38 tests passing.

## Phase 4: Local Testing

- Ran simulated sensor from dev machine targeting RasPi5 InfluxDB
- Confirmed data arrived in `sensors` database with correct tags and fields
- Cleaned up test data afterward

## Phase 5: Device Deployment

### Sprinkler1 (192.168.0.100) — main_site

- Switched git remote from SSH to HTTPS (no deploy key on device)
- Pulled latest code, created .env, installed dependencies
- Manual test confirmed ADS1115 reading house_branch at ~48 PSI
- Created systemd service (`sprinkler-monitor.service`), enabled for boot
- Service running and writing to InfluxDB

### Sprinkler2 (192.168.0.7) — aux_site

- Switched git remote to HTTPS
- Stashed local changes (debug imports in sensor.py), pulled, restored sensor.py
- Fixed requirements.txt (stash conflict resolved by taking pulled version)
- Manual test confirmed all 4 channels: main_well, shop_well, irrigation_branch, runway_well
- Created systemd service, enabled for boot
- Service running and writing to InfluxDB

## Phase 6: Grafana Dashboard

- Added `InfluxDB-Sensors` data source (uid: nI9ZjC5Dz) pointing at sensors database
- Imported "Water Pressure Monitor" dashboard with:
  - Current pressure stat panels (color-coded thresholds)
  - Pressure timeline graph (all sensors)
  - 24h summary table (min/max/avg per sensor)
  - Status overview panel
  - Location and sensor dropdown filters
- Dashboard URL: http://192.168.0.18:9000/d/water-pressure-monitor/water-pressure-monitor

## Phase 7: Final Verification

| Device | sprinkler-monitor | telegraf | Data flowing |
|--------|-------------------|----------|--------------|
| RasPi5 | N/A (hub) | N/A | 19,187 points/hr |
| Sprinkler1 | active | disabled | main_site: 2,347 pts/hr |
| Sprinkler2 | active | disabled | aux_site: 16,840 pts/hr |

All 5 sensors confirmed: house_branch, main_well, shop_well, irrigation_branch, runway_well

---

## Issues Encountered & Resolutions

1. **SSH username:** CLAUDE.md referenced user `pi`, actual username is `cdgentile` on all devices.
2. **GitHub SSH keys:** Sprinkler Pis had SSH git remotes but no deploy keys. Switched to HTTPS.
3. **Sprinkler2 local changes:** Had uncommitted debug imports in sensor.py and RPi.GPIO in requirements.txt. Resolved via stash/restore.
4. **No systemd service existed:** Neither sprinkler Pi had a `sprinkler-monitor.service`. Created on both devices.
5. **Grafana password:** Default admin:admin had been changed. Used actual credentials.
6. **Float precision in tests:** Timestamp conversion to nanoseconds had IEEE 754 drift. Fixed by using integer timestamps in tests and round() in publisher.

---

## Rollback Instructions

### Revert to MQTT-only (pre-migration)

On each sprinkler Pi:
```bash
cd ~/sprinkler-pressure-monitor
sudo systemctl stop sprinkler-monitor
git checkout be6a700  # Last commit before migration
cp config.yaml.backup config.yaml
rm .env
sudo systemctl start sprinkler-monitor
```

Note: MQTT output would need a working broker to send to. The Karbon 300 broker is still down.

### Remove sensors database (if needed)

```bash
ssh cdgentile@192.168.0.18 "docker exec influxdb influx -execute 'DROP DATABASE sensors'"
```

### Remove Mosquitto (if needed)

```bash
ssh cdgentile@192.168.0.18 "cd ~/mqtt-broker && docker compose down && rm -rf ~/mqtt-broker"
```

---

## Next Steps

- [ ] Re-enable Telegraf on sprinkler Pis (pointed at RasPi5 instead of Karbon 300)
- [ ] Configure Python logging module in main.py (currently InfluxDB publisher logs are silent)
- [ ] Add voltage passthrough from sensor.py readings to payload
- [ ] Replace status note "stub" in payload.py with actual sensor health checks
- [ ] Set up Grafana alerts for pressure out-of-range conditions
- [ ] Create InfluxDB continuous queries for downsampled_365d retention policy
- [ ] Add authentication to Mosquitto MQTT broker
- [ ] Consider adding RPi.GPIO to requirements.txt (needed on Sprinkler2)
- [ ] Clean up uncommitted sensor.py debug imports on Sprinkler2
