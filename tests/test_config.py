

import pytest
import tempfile
import yaml
from pressure_monitor.config import load_config

VALID_CONFIG = {
    "sites": {
        "main_site": {
            "sensor": {
                "type": "ads1115",
                "channels": {
                    0: {
                        "enabled": True,
                        "name": "test_sensor",
                        "max_voltage": 5.0,
                        "max_value": 100.0,
                    }
                },
            }
        },
        "aux_site": {
            "sensor": {
                "type": "ads1115",
                "channels": {
                    0: {
                        "enabled": True,
                        "name": "aux_sensor",
                        "max_voltage": 5.0,
                        "max_value": 100.0,
                    }
                },
            }
        }
    },
    "sampling": {"high_rate_hz": 10, "low_rate_hz": 0.2},
    "simulation": {"sensor": True, "output": True},
    "mqtt": {"enabled": True, "host": "localhost"}
}

def write_temp_config(config_dict):
    temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    yaml.dump(config_dict, temp_file)
    temp_file.flush()
    return temp_file.name

def test_load_main_site_config():
    path = write_temp_config(VALID_CONFIG)
    config = load_config(path, site="main_site")
    assert config["sensor"]["channels"][0]["name"] == "test_sensor"

def test_load_aux_site_config():
    path = write_temp_config(VALID_CONFIG)
    config = load_config(path, site="aux_site")
    assert config["sensor"]["channels"][0]["name"] == "aux_sensor"

def test_default_site_config():
    path = write_temp_config(VALID_CONFIG)
    config = load_config(path)
    assert config["sensor"]["channels"][0]["name"] == "test_sensor"

def test_missing_sites_key():
    invalid_config = {
        "sampling": {},
        "simulation": {},
        "mqtt": {}
    }
    path = write_temp_config(invalid_config)
    with pytest.raises(ValueError, match="No 'sites' key found"):
        load_config(path)

def test_invalid_site_name():
    path = write_temp_config(VALID_CONFIG)
    with pytest.raises(ValueError, match="Site 'invalid' not found"):
        load_config(path, site="invalid")