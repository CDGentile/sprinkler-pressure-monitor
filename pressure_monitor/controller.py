import time
from datetime import datetime
from pressure_monitor.payload import build_payload

class Controller:
    def __init__(self, config, sensor, output):
        self.config = config
        self.sensor = sensor
        self.output = output

        self.rate_hz = config["sampling"].get("rate_hz", 0.5)
        self.channel_offset_ms = config["sampling"].get("channel_offset_ms", 250)
        self.verbose = config.get("outputs", {}).get("verbose", False)

    def run(self):
        print("Starting controller loop...")
        interval = 1.0 / self.rate_hz
        offset_sec = self.channel_offset_ms / 1000.0

        try:
            while True:
                cycle_start = time.time()

                readings = self.sensor.read_all_staggered(offset_sec)

                payload = build_payload(readings)
                try:
                    self.output.publish(payload)
                    if self.verbose:
                        ts_str = datetime.fromtimestamp(cycle_start).strftime("%H:%M:%S.%f")[:-4]
                        print(f"Published at {ts_str}")
                except Exception as e:
                    print(f"[ERROR] Output failed: {e}")

                elapsed = time.time() - cycle_start
                sleep_time = max(0, interval - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("Controller stopped by user.")
