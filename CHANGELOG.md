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
- ADS1115 hardware integration in `sensor.py` with module-level imports and safe fallbacks
- Unit test with mocks for ADS1115 integration, enabling validation without hardware
- PublisherManager to support multiple outputs (console + MQTT) concurrently
- `outputs` block in config for enabling/disabling console, MQTT, and verbose logging
- `--verbose` CLI flag to control detailed console and MQTT debug output
- **Per-sensor payload publishing**: `payload.py` now emits one message per sensor reading for compatibility with Telegraf/InfluxDB
- **Test suite updates**: Integration and MQTT publisher tests extended to validate per-sensor publishing

### Changed
- Payloads now include sensor `name` and `value` as separate fields
- **Payload structure changed from a single object with `readings[]` to a list of individual per-sensor payloads**
- `MqttPublisher` updated to loop over payload list and publish each individually
- `ConsolePublisher` updated to loop over payload list and print each individually
- `config.py` now fully supports dynamic site selection using the `--site` CLI argument with fallback to `main_site` if unspecified or invalid
- Payload builder updated to include sensor `name` using config-defined labels
- `sensor.py` and `sensor_sim.py` both updated to return full metadata for each reading (`channel`, `voltage`, `value`, `name`)
- `main.py` uses `config.yaml` defaults but accepts CLI overrides
- Configuration now encapsulates all logic per "site", supporting multiple physical deployments
- Standardized sensor readings across all modules to use `{ "name": ..., "value": ... }` format
- Updated `sensor.py` and `sensor_sim.py` to return readings with sensor names instead of channel numbers, using `max_voltage` for scaling
- Refactored `controller.py` to index history and stability checks by sensor name
- Simplified `payload.py` to directly forward reading dicts
- Updated console and MQTT outputs to display/publish sensor names and values
- Aligned all tests (`test_sensor.py`, `test_integration.py`, `test_controller.py`, `test_payload.py`, `test_mqtt.py`) with the new data structure
- ConsolePublisher updated to support verbose mode (per-reading output with 2 decimal places)
- Controller and MqttPublisher debug logs now respect verbose flag
- `main.py` updated to instantiate PublisherManager instead of single output
- README updated with usage instructions, config examples, and new file structure

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