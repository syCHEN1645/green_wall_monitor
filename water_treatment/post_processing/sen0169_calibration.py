import os
import json

CONFIG_FILE = "config/sen0169_config.json"
PH_CONFIG = None

def load_sen00169_config():
    """Load SEN0169 configuration from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, CONFIG_FILE)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
        
    with open(config_path, "r") as f:
        return json.load(f)
    
def process_ph_reading(voltage_mv: float) -> float:
    """Compute pH value from sensor voltage.

    Args:
    voltage_mv: Sensor voltage in millivolts.

    Returns:
    pH value as float.
    """
    global PH_CONFIG
    if PH_CONFIG is None:
        PH_CONFIG = load_sen00169_config()
    assert isinstance(PH_CONFIG, dict)

    offset = PH_CONFIG.get("offset")
    assert isinstance(offset, float)

    res = 3.5 * voltage_mv + offset
    return res