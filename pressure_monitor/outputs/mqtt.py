import paho.mqtt.client as mqtt
import json

class MqttPublisher:
    def __init__(self, config):
        self.config = config["mqtt"]
        self.client = mqtt.Client()
        self.client.connect(self.config["host"], self.config["port"])
        self.topic = self.config["topic"]
        print(f"Connected to MQTT broker at {self.config['host']}")

    def publish(self, payload):
        message = json.dumps(payload)
        self.client.publish(self.topic, message, qos=self.config.get("qos", 0))