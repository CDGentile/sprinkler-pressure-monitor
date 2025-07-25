from pressure_monitor.config import load_config
from pressure_monitor.controller import Controller

def main():
    config = load_config("config.yaml")
    controller = Controller(config)
    controller.run()

if __name__ == "__main__":
    main()