# SEM-meter circuit configuration
# Maps sense[] array index to circuit name, type, and scaling factors, PER DEVICE.
#
# Each physical SEM meter reports the same sense[] structure (indices 0-18), but
# assigns different real-world circuits to those indices. Scaling therefore also
# differs per index per device, so the mapping must be keyed by device ID (the
# MAC-style ID in the MQTT topic: SEMMETER/<device_id>/HA).
#
# Scaling factors derived from the SEM-provided Home Assistant config for each
# device (see scratchpad/<device_id>--homeasistantConfig.txt).

# Standard scaling profiles. current_scale is 0.01 for every circuit; 240V
# (double-pole) circuits use double the voltage/power/energy scale of 120V.
_120V = {"type": "120v", "voltage_scale": 0.1, "current_scale": 0.01, "power_scale": 0.01, "energy_scale": 0.001}
_240V = {"type": "240v", "voltage_scale": 0.2, "current_scale": 0.01, "power_scale": 0.02, "energy_scale": 0.002}
_MAIN = {"type": "main", "voltage_scale": 0.1, "current_scale": 0.01, "power_scale": 0.01, "energy_scale": 0.001}


def _c(name, profile):
    """Build a circuit config dict from a name and a scaling profile."""
    return {"name": name, **profile}


# Per-device index -> circuit config.
# Indices not present in a device's map are ignored by the consumer (e.g. a
# meter's unconnected circuit slots), so only wire up circuits that are real.
DEVICE_CIRCUITS = {
    # Original meter ("Shop") - all 16 circuit slots + 3 main legs populated.
    "A085E3FD6EA6": {
        0:  _c("old_outlet",      _120V),
        1:  _c("heater",          _240V),
        2:  _c("old_pump",        _240V),
        3:  _c("timer_outlet",    _120V),
        4:  _c("gfci_network",    _120V),
        5:  _c("indicator_light", _120V),
        6:  _c("20a_outlet",      _120V),
        7:  _c("lights",          _120V),
        8:  _c("pond_pump",       _240V),
        9:  _c("new_pump",        _240V),
        10: _c("circuit11",       _120V),
        11: _c("circuit12",       _120V),
        12: _c("circuit13",       _120V),
        13: _c("circuit14",       _120V),
        14: _c("circuit15",       _120V),
        15: _c("circuit16",       _120V),
        16: _c("main_leg1",       _MAIN),
        17: _c("main_leg2",       _MAIN),
        18: _c("main_leg3",       _MAIN),
    },
    # Second meter ("Hobbit") - 2 main legs + 5 connected circuits (0-4).
    # Slots 5-15 are unconnected and intentionally omitted.
    "1CDBD4423A6E": {
        0:  _c("tank_pump",       _240V),
        1:  _c("hobbit_outlets",  _120V),
        2:  _c("hangar",          _120V),
        3:  _c("dryer",           _240V),
        4:  _c("runway_pump",     _240V),
        16: _c("main_leg1",       _MAIN),
        17: _c("main_leg2",       _MAIN),
        18: _c("main_leg3",       _MAIN),
    },
}

# Per-device main-leg indices summed into the synthetic "main_total" circuit.
DEVICE_MAIN_LEGS = {
    "A085E3FD6EA6": [16, 17, 18],
    "1CDBD4423A6E": [16, 17, 18],
}
