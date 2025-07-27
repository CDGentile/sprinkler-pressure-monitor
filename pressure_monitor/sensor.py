class SensorManager:
    def __init__(self, config):
        self.channel_configs = {
            int(ch): cfg for ch, cfg in config["sensor"]["channels"].items()
            if cfg.get("enabled", False)
        }

        self.enabled_channels = sorted(self.channel_configs.keys())
        print(f"Enabled sensor channels: {self.enabled_channels}")

        # TODO: Replace with actual ADS1115 initialization
        self.ads = None  # Placeholder for ADC object

    def read_all(self):
        readings = []
        for ch in self.enabled_channels:
            voltage = self.read_adc_channel(ch)  # Placeholder
            max_voltage = self.channel_configs[ch]["max_voltage"]
            max_value = self.channel_configs[ch]["max_value"]
            name = self.channel_configs[ch]["name"]

            # Normalize reading
            value = (voltage / max_voltage) * max_value
            readings.append((name, value))

        return readings

    def read_adc_channel(self, ch):
        # Placeholder logic — replace with actual ADS1115 voltage read
        return 2.5  # Dummy voltage