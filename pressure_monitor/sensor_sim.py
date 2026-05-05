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

    def read_channel(self, ch):
        """Read and return a single simulated channel."""
        channels_cfg = self.config["sensor"]["channels"]
        cfg = channels_cfg.get(ch) or channels_cfg.get(str(ch))
        if not cfg:
            raise KeyError(f"Channel {ch} not found in config")
        delta = random.uniform(-0.3, 0.3)
        self.baseline[ch] += delta
        return {"name": cfg["name"], "value": self.baseline[ch]}

    def read_all(self):
        """Read all enabled channels sequentially with no delay."""
        return [self.read_channel(ch) for ch in self.channels]

    def read_all_staggered(self, offset_sec):
        """Read all enabled channels with a delay between each."""
        readings = []
        for i, ch in enumerate(self.channels):
            if i > 0:
                time.sleep(offset_sec)
            readings.append(self.read_channel(ch))
        return readings