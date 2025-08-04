import json

class ConsolePublisher:
    def __init__(self, config, verbose=False):
        self.verbose = verbose
        print("[ConsolePublisher] Ready to print payloads to stdout")

    def publish(self, payload):
        if self.verbose:
            for r in payload.get("readings", []):
                print(f"[ConsolePublisher] {r['name']}: {r['value']:.2f}")
        else:
            print(json.dumps(payload, indent=2))