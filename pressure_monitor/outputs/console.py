import json

class ConsolePublisher:
    def __init__(self, config):
        print("[ConsolePublisher] Ready to print payloads to stdout")

    def publish(self, payload):
        print(json.dumps(payload, indent=2))