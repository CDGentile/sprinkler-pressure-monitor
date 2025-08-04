import yaml

def load_config(path, site="main_site"):
    with open(path, "r") as f:
        full_config = yaml.safe_load(f)

    if "sites" not in full_config:
        raise ValueError("No 'sites' key found in configuration.")

    if site not in full_config["sites"]:
        raise ValueError(f"Site '{site}' not found in configuration.")

    # Merge selected site config with top-level config
    selected_site_config = full_config["sites"][site]

    # Combine other top-level config sections (sampling, mqtt, etc.)
    merged_config = {
        "sensor": selected_site_config["sensor"],
        "sampling": full_config.get("sampling", {}),
        "simulation": full_config.get("simulation", {}),
        "mqtt": full_config.get("mqtt", {}),
        "outputs": full_config.get("outputs", {}),
    }

    return merged_config