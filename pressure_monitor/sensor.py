import time

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except ImportError:
    from types import SimpleNamespace
    board = SimpleNamespace(SCL=None, SDA=None)
    busio = SimpleNamespace(I2C=None)
    ADS = SimpleNamespace(ADS1115=None, P0=None, P1=None, P2=None, P3=None)
    AnalogIn = None

class SensorManager:
    def __init__(self, config):
        self.channel_configs = {
            int(ch): cfg for ch, cfg in config["sensor"]["channels"].items()
            if cfg.get("enabled", False)
        }

        self.enabled_channels = sorted(self.channel_configs.keys())
        print(f"Enabled sensor channels: {self.enabled_channels}")

        if board and busio and ADS and AnalogIn:
            self.board = board
            self.busio = busio
            self.ADS1115 = ADS.ADS1115
            self.AnalogIn = AnalogIn
            self.CHANNEL_MAP = {
                0: ADS.P0,
                1: ADS.P1,
                2: ADS.P2,
                3: ADS.P3
            }
        else:
            print("ADS1115 libraries not available; running in simulation/test mode.")
            self.board = None
            self.busio = None
            self.ADS1115 = None
            self.AnalogIn = None
            self.CHANNEL_MAP = {}

        self.ads = None
        self._channels = {}
        self._pins = {}

        # Initialize ADS1115 if hardware libraries are available
        if self.busio and self.ADS1115:
            try:
                i2c = self.busio.I2C(self.board.SCL, self.board.SDA)
                self.ads = self.ADS1115(i2c)
                # Pre-create AnalogIn objects (used for voltage conversion)
                # and cache pin values for direct register access
                for ch in self.enabled_channels:
                    self._channels[ch] = self.AnalogIn(self.ads, self.CHANNEL_MAP[ch])
                    # Single-ended pin = raw pin + 0x04
                    self._pins[ch] = self.CHANNEL_MAP[ch] + 0x04
                self._conversion_wait = 1.0 / self.ads.data_rate + 0.001
                print("ADS1115 initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize ADS1115: {e}")
                self.ads = None

    def read_all(self):
        readings = []
        for ch in self.enabled_channels:
            voltage = self.read_adc_channel(ch)
            max_voltage = self.channel_configs[ch]["max_voltage"]
            max_value = self.channel_configs[ch]["max_value"]
            name = self.channel_configs[ch]["name"]

            # Normalize reading
            value = (voltage / max_voltage) * max_value
            readings.append({"name": name, "value": value})

        return readings

    def read_adc_channel(self, ch):
        if self.ads and ch in self._channels:
            try:
                pin = self._pins[ch]
                # Bypass the Adafruit library's _conversion_complete()
                # polling which has an OS-bit race condition: the poll
                # can return before the ADS1115 clears the OS bit,
                # reading the previous channel's stale result.
                # Instead, use time-based waiting for guaranteed completion.

                # First conversion: sets MUX, allows input to settle
                self.ads._write_config(pin)
                time.sleep(self._conversion_wait)

                # Second conversion: input settled, real read
                self.ads._write_config(pin)
                time.sleep(self._conversion_wait)

                # Read result directly from conversion register
                raw = self.ads._conversion_value(self.ads.get_last_result())
                return self._channels[ch].convert_to_voltage(raw)
            except Exception as e:
                print(f"Error reading channel {ch}: {e}")
                return 0.0
        else:
            # Fallback dummy voltage for testing/simulation
            return 2.5
