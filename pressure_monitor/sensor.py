class SensorManager:
    def __init__(self, config):
        self.channel_configs = {
            int(ch): cfg for ch, cfg in config["sensor"]["channels"].items()
            if cfg.get("enabled", False)
        }

        self.enabled_channels = sorted(self.channel_configs.keys())
        print(f"Enabled sensor channels: {self.enabled_channels}")

        # Scoped imports for ADS1115 hardware
        try:
            import board
            import busio
            from adafruit_ads1x15.ads1115 import ADS1115
            from adafruit_ads1x15.analog_in import AnalogIn

            self.board = board
            self.busio = busio
            self.ADS1115 = ADS1115
            self.AnalogIn = AnalogIn

            # Channel map: config channel number → ADS constant
            self.CHANNEL_MAP = {
                0: ADS1115.P0,
                1: ADS1115.P1,
                2: ADS1115.P2,
                3: ADS1115.P3
            }
        except ImportError:
            print("ADS1115 libraries not available; running in simulation/test mode.")
            self.board = None
            self.busio = None
            self.ADS1115 = None
            self.AnalogIn = None
            self.CHANNEL_MAP = {}

        # Placeholder for ADC object, initialized later
        self.ads = None  # To be initialized when hardware is available

        # Initialize ADS1115 if hardware libraries are available
        if self.busio and self.ADS1115:
            try:
                i2c = self.busio.I2C(self.board.SCL, self.board.SDA)
                self.ads = self.ADS1115(i2c)
                print("ADS1115 initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize ADS1115: {e}")
                self.ads = None

    def read_all(self):
        readings = []
        for ch in self.enabled_channels:
            voltage = self.read_adc_channel(ch)  # Placeholder
            max_voltage = self.channel_configs[ch]["max_voltage"]
            max_value = self.channel_configs[ch]["max_value"]
            name = self.channel_configs[ch]["name"]

            # Normalize reading
            value = (voltage / max_voltage) * max_value
            readings.append({"name": name, "value": value})

        return readings

    def read_adc_channel(self, ch):
        if self.ads and self.AnalogIn:
            try:
                chan = self.AnalogIn(self.ads, self.CHANNEL_MAP[ch])
                return chan.voltage
            except Exception as e:
                print(f"Error reading channel {ch}: {e}")
                return 0.0
        else:
            # Fallback dummy voltage for testing/simulation
            return 2.5