import paho.mqtt.client as mqtt
import json

class MqttPublisher:
    def __init__(self, config):
        self.config = config["mqtt"]
        self.verbose = config.get("outputs", {}).get("verbose", False)
        self.client = mqtt.Client()
        self.client.connect(self.config["host"], self.config["port"])
        self.client.loop_start()   # Start background network loop

        # Debug disconnect callback
        def on_disconnect(client, userdata, rc):
            if self.verbose:
                print(f"[MqttPublisher] Disconnected from broker with code {rc}")
        self.client.on_disconnect = on_disconnect

        self.topic = self.config["topic"]
        if self.verbose:
            print(f"Connected to MQTT broker at {self.config['host']}")

    def publish(self, payload):
        message = json.dumps(payload)
        if self.verbose:
            for r in payload.get("readings", []):
                print(f"[MqttPublisher] {r['name']}: {r['value']:.2f}")
        self.client.publish(self.topic, message, qos=self.config.get("qos", 0))