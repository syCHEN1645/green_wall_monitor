import json
import os

CONFIG_FILE = "config/sen0464_config.json"
ORP_CONFIG = None

def load_sen0464_config():
    """Load SEN0464 configuration from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, CONFIG_FILE)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
        
    with open(config_path, "r") as f:
        return json.load(f)
    
def process_orp_reading(voltage_mv: float) -> float:
    """Compute ORP from sensor voltage.

    Args:
    voltage_mv: Sensor voltage in mV.

    Returns:
    ORP value as float.
    """
    # load config if config is none
    global ORP_CONFIG
    if ORP_CONFIG is None:
        ORP_CONFIG = load_sen0464_config()
    assert isinstance(ORP_CONFIG, dict)

    offset = ORP_CONFIG.get("zero_point_offset")
    assert isinstance(offset, int)
    zero_point_mv = ORP_CONFIG.get("zero_point_mv")
    assert isinstance(zero_point_mv, int)
    
    res = voltage_mv - zero_point_mv + offset
    return res
