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
        for ch in self.channels:
            delta = random.uniform(-0.3, 0.3)
            self.baseline[ch] += delta
            voltage = (self.baseline[ch] / 100.0) * 5.0  # match calibration

            # Retrieve channel config
            cfg = self.config["sensor"]["channels"][str(ch)]
            name = cfg["name"]
            readings.append((name, self.baseline[ch]))

        return readings