import json
import pathlib

PH_NAME = "PH"
DO_NAME = "DO"
ORP_NAME = "ORP"

CONFIG_FILENAME_LOOKUP = {
    PH_NAME: "water_treatment/post_processing/config/sen0169_config.json",
    DO_NAME: "water_treatment/post_processing/config/sen0237_config.json",
    ORP_NAME: "water_treatment/post_processing/config/sen0464_config.json"
}

PROJECT_DIR = pathlib.Path(__file__).parent.parent.resolve()

def load_config(sensor_name: str):
    """Load configuration for a given sensor from its JSON file.

    Args:
        sensor_name (str): The name of the sensor.

    Returns:
        dict: The configuration data loaded from the JSON file.
    """
    filename = CONFIG_FILENAME_LOOKUP.get(sensor_name)
    if filename is None:
        raise ValueError(f"This sensor does not exist or does not have a config file: {sensor_name}")
    
    config_file = PROJECT_DIR / filename
    if not config_file.exists():
        raise ValueError(f"No configuration file found for sensor {sensor_name} at {config_file}")
    
    with open(config_file, "r") as f:
        return json.load(f)
    
def save_config(sensor_name: str, config_data: dict):
    """Save configuration for a given sensor to its JSON file.

    Args:
        sensor_name (str): The name of the sensor.
        config_data (dict): The configuration data to save.
    """
    filename = CONFIG_FILENAME_LOOKUP.get(sensor_name)
    if filename is None:
        raise ValueError(f"This sensor does not exist or does not have a config file: {sensor_name}")
    
    config_file = PROJECT_DIR / filename
    if not config_file.exists():
        raise ValueError(f"No configuration file found for sensor {sensor_name} at {config_file}")
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=4)
        print("New configuration saved successfully.")

def get_config_value(sensor_name: str, config_name: str):
    """Retrieve a configuration value from the JSON file of the sensor.

    Args:
        sensor_name (str): The name of the sensor.
        config_name (str): The name of the configuration value to retrieve.
    """
    filename = CONFIG_FILENAME_LOOKUP.get(sensor_name)
    if filename is None:
        raise ValueError(f"This sensor does not exist or does not have a config file: {sensor_name}")
    
    # / is similar to os.path.join, it joins the parent directory with the filename in pathlib
    config_file = PROJECT_DIR / filename
    if not config_file.exists():
        raise ValueError(f"No configuration file found for sensor {sensor_name} at {config_file}")
    
    with open(config_file, "r") as f:
        config_data = json.load(f)
        config_value = config_data.get(config_name)
        if config_value is None:
            raise ValueError(f"Configuration value '{config_name}' not found in {config_file}")
        print(f"Retrieved configuration value: {config_value}")
        return config_value
    
def set_config_value(sensor_name: str, config_name: str, config_value):
    """Set a configuration value in the JSON file of the sensor.

    Args:
        sensor_name (str): The name of the sensor.
        config_name (str): The name of the configuration value to set.
        config_value: The value to set for the configuration.
    """
    # check valid sensor name
    filename = CONFIG_FILENAME_LOOKUP.get(sensor_name)
    if filename is None:
        raise ValueError(f"This sensor does not exist or does not have a config file: {sensor_name}")
    
    # check config file exists
    config_file = PROJECT_DIR / filename
    if not config_file.exists():
        raise ValueError(f"No configuration file found for sensor {sensor_name} at {config_file}")
    
    with open(config_file, "r") as f:
        config_data = json.load(f)
    
    # check config name exists
    if config_name not in config_data:
        raise ValueError(f"Configuration value '{config_name}' not found in {config_file}")
    
    # check new config value type matches the original config value type
    original_value_type = type(config_data[config_name])
    if not isinstance(config_value, original_value_type):
        raise ValueError(f"Type mismatch: Expected {original_value_type.__name__} for '{config_name}', got {type(config_value).__name__}")
    
    # write the new config
    config_data[config_name] = config_value
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=4)
        print("New configuration value set successfully.")