# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
### Added
- CLI support for selecting sensor simulation and output modes (`--simulate-sensor`, `--simulate-output`)
- Configurable high and low sampling rates with stability threshold logic
- Sensor name/description support in payloads
- Site-based configuration structure (`main_site`, `aux_site`)
- Project scaffold with modular architecture:
  - `sensor`, `sensor_sim`, `controller`, `payload`, `mqtt`, `console`
- Test suite with unit coverage for:
  - Payload builder
  - Sensor manager (simulated)
  - MQTT output (mocked)
  - Integration with controller logic
- README and developer workflow documentation
- `.gitignore` with proper venv exclusions
- Test coverage for site-specific sensor naming and dynamic site config loading
- Integration test (`test_sensor_to_mqtt_flow`) updated to verify named sensor readings in payload
- Updated README to reflect new CLI options and config structure

### Changed
- Payloads now include sensor `name` and `value` as separate fields
- `config.py` now fully supports dynamic site selection using the `--site` CLI argument with fallback to `main_site` if unspecified or invalid
- Payload builder updated to include sensor `name` using config-defined labels
- `sensor.py` and `sensor_sim.py` both updated to return full metadata for each reading (`channel`, `voltage`, `value`, `name`)
- `main.py` uses `config.yaml` defaults but accepts CLI overrides
- Configuration now encapsulates all logic per "site", supporting multiple physical deployments

---

## [Planned]
### In Progress
- `config.py` support for selecting site configuration dynamically
- CLI support for `--site` override (default: `main_site`)

### Next Steps
- Add fallback and error-handling for invalid site names
- Real hardware integration test (ADS1115 and MQTT broker)
- Grafana dashboard design and deployment
- Add CLI flag for listing all available sites
- Future: offline storage and buffered replay if network is unavailable