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
            print(f"[MqttPublisher] Disconnected from broker with code {rc}")
        self.client.on_disconnect = on_disconnect

        self.topic = self.config["topic"]
        print(f"Connected to MQTT broker at {self.config['host']}, printing to topic {self.topic}")

    def publish(self, payloads):
        # payloads is now a list of individual sensor payloads
        for p in payloads:
            message = json.dumps(p)
            if self.verbose:
                print(f"[MqttPublisher] {p['name']}: {p['value']:.2f}")
            self.client.publish(self.topic, message, qos=self.config.get("qos", 0))