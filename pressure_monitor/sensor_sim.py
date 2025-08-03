import random
import time

class SimulatedSensorManager:
    def __init__(self, config):
        self.config = config
        self.channels = [
            int(ch) for ch, cfg in config["sensor"]["channels"].items()
            if cfg.get("enabled", False)
        ]
        self.baseline = {ch: random.uniform(30.0, 60.0) for ch in self.channels}

    def read_all(self):
        readings = []
        channels_cfg = self.config["sensor"]["channels"]
        for ch in self.channels:
            delta = random.uniform(-0.3, 0.3)
            self.baseline[ch] += delta
            # Retrieve channel config
            cfg = channels_cfg.get(ch) or channels_cfg.get(str(ch))
            if not cfg:
                raise KeyError(f"Channel {ch} not found in config")
            voltage = (self.baseline[ch] / 100.0) * cfg.get("max_voltage", 5.0)  # match calibration

            name = cfg["name"]
            readings.append({"name": name, "value": self.baseline[ch]})

        return readings