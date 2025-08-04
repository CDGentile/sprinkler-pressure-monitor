

from .console import ConsolePublisher
from .mqtt import MqttPublisher

class PublisherManager:
    def __init__(self, config):
        self.publishers = []
        outputs_cfg = config.get("outputs", {})
        print(outputs_cfg)

        # Enable console publisher if configured
        if outputs_cfg.get("console", False):
            verbose = outputs_cfg.get("verbose", False)
            print("Initializing console output... verbose = ", verbose)
            self.publishers.append(ConsolePublisher(outputs_cfg, verbose=verbose))

        # Enable MQTT publisher if configured
        if outputs_cfg.get("mqtt", False):
            print("Initializing MQTT output...")
            self.publishers.append(MqttPublisher(config))

    def publish(self, payload):
        for publisher in self.publishers:
            publisher.publish(payload)