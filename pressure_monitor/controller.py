import time
from datetime import datetime
from pressure_monitor.payload import build_payload

class Controller:
    def __init__(self, config, sensor, output):
        self.config = config
        self.sensor = sensor
        self.output = output

        self.high_rate = config["sampling"]["high_rate_hz"]
        self.low_rate = config["sampling"]["low_rate_hz"]
        self.threshold_pct = config["sampling"]["stability_threshold_pct"]
        self.window_sec = config["sampling"]["stability_window_sec"]

        self.history = {}  # {name: [(timestamp, value), ...]}
        self.last_publish_time = 0
        self.stable = False
        self.verbose = config.get("outputs", {}).get("verbose", False)

    def run(self):
        print("Starting controller loop...")
        try:
            while True:
                now = time.time()
                readings = self.sensor.read_all()
                self._update_history(now, readings)

                if self._is_stable():
                    interval = 1 / self.low_rate
                else:
                    interval = 1 / self.high_rate

                if now - self.last_publish_time >= interval:
                    payload = build_payload(readings)
                    try:
                        self.output.publish(payload)
                        self.last_publish_time = now
                        if self.verbose:
                            ts_str = datetime.fromtimestamp(now).strftime("%H:%M:%S.%f")[:-4]
                            print(f"Published at {ts_str} (stable={self.stable})")
                    except Exception as e:
                        print(f"[ERROR] Output failed: {e}")

                time.sleep(1 / self.high_rate)

        except KeyboardInterrupt:
            print("Controller stopped by user.")

    def _update_history(self, now, readings):
        for r in readings:
            name = r["name"]
            val = r["value"]
            if name not in self.history:
                self.history[name] = []
            self.history[name].append((now, val))

        # Trim history to the configured window
        cutoff = now - self.window_sec
        for ch in self.history:
            self.history[ch] = [(t, v) for (t, v) in self.history[ch] if t >= cutoff]

    def _is_stable(self):
        """Return True if all channels have been stable within threshold"""
        self.stable = True
        for ch, series in self.history.items():
            if len(series) < 2:
                self.stable = False
                continue

            values = [v for (t, v) in series]
            vmin, vmax = min(values), max(values)

            # Use configured max_value as denominator instead of vmax
            max_scale = None
            for cfg in self.config["sensor"]["channels"].values():
                if cfg.get("name") == ch:
                    max_scale = cfg.get("max_value", 100.0)
                    break
            if max_scale is None:
                max_scale = 100.0

            if max_scale == 0:
                continue

            pct_change = 100 * abs(vmax - vmin) / max_scale
            if pct_change > self.threshold_pct:
                self.stable = False
        return self.stable