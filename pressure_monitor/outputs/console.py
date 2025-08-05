import json

class ConsolePublisher:
    def __init__(self, config, verbose=False):
        self.verbose = verbose
        print("[ConsolePublisher] Ready to print payloads to stdout")

    def publish(self, payloads):
        if self.verbose:
            for p in payloads:
                print(f"[ConsolePublisher] {p['name']}: {p['value']:.2f}")
        else:
            print(json.dumps(payloads, indent=2))