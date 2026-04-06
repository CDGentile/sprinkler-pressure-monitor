# SEM-meter circuit configuration
# Maps sense[] array index to circuit name, type, and scaling factors.
# Scaling factors derived from Home Assistant config for device A085E3FD6EA6.

CIRCUITS = {
    0:  {"name": "old_outlet",      "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    1:  {"name": "heater",          "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    2:  {"name": "old_pump",        "type": "240v", "voltage_scale": 0.2,  "current_scale": 0.01, "power_scale": 0.02,  "energy_scale": 0.002},
    3:  {"name": "timer_outlet",    "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    4:  {"name": "gfci_network",    "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    5:  {"name": "indicator_light", "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    6:  {"name": "20a_outlet",      "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    7:  {"name": "lights",          "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    8:  {"name": "pond_pump",       "type": "240v", "voltage_scale": 0.2,  "current_scale": 0.01, "power_scale": 0.02,  "energy_scale": 0.002},
    9:  {"name": "new_pump",        "type": "240v", "voltage_scale": 0.2,  "current_scale": 0.01, "power_scale": 0.02,  "energy_scale": 0.002},
    10: {"name": "circuit11",       "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    11: {"name": "circuit12",       "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    12: {"name": "circuit13",       "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    13: {"name": "circuit14",       "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    14: {"name": "circuit15",       "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    15: {"name": "circuit16",       "type": "120v", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    16: {"name": "main_leg1",       "type": "main", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    17: {"name": "main_leg2",       "type": "main", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
    18: {"name": "main_leg3",       "type": "main", "voltage_scale": 0.1,  "current_scale": 0.01, "power_scale": 0.01,  "energy_scale": 0.001},
}

MAIN_LEGS = [16, 17, 18]
