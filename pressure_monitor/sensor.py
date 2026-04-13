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

        # Placeholder for ADC object, initialized later
        self.ads = None  # To be initialized when hardware is available
        self.analog_inputs = {}

        # Initialize ADS1115 if hardware libraries are available
        if self.busio and self.ADS1115:
            try:
                i2c = self.busio.I2C(self.board.SCL, self.board.SDA)
                self.ads = self.ADS1115(i2c)
                self.analog_inputs = {
                    ch: self.AnalogIn(self.ads, self.CHANNEL_MAP[ch])
                    for ch in self.enabled_channels
                }
                print("ADS1115 initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize ADS1115: {e}")
                self.ads = None
                self.analog_inputs = {}

    def read_all(self):
        readings = []
        for ch in self.enabled_channels:
            voltage = self.read_adc_channel(ch)
            cfg = self.channel_configs[ch]
            min_voltage = cfg.get("min_voltage", 0.5)
            max_voltage = cfg["max_voltage"]
            max_value = cfg["max_value"]
            name = cfg["name"]

            # Scale voltage to value using sensor's linear range
            # Typical 3-wire transducer: 0.5V = 0 PSI, 4.5V = max PSI
            clamped = max(min_voltage, min(voltage, max_voltage))
            value = ((clamped - min_voltage) / (max_voltage - min_voltage)) * max_value
            value += cfg.get("calibration_offset", 0.0)
            readings.append({"name": name, "value": value})

        return readings

    def read_adc_channel(self, ch):
        if self.ads and self.AnalogIn:
            try:
                return self.analog_inputs[ch].voltage
            except Exception as e:
                print(f"Error reading channel {ch}: {e}")
                return 0.0
        else:
            # Fallback dummy voltage for testing/simulation
            return 2.5
