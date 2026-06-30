import json
import os

CONFIG_FILE = "config/sen0237_config.json"
DO_CONFIG = None

def load_sen0237_config():
    """Load SEN0237 configuration from JSON file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, CONFIG_FILE)
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found.")
        
    with open(config_path, "r") as f:
        return json.load(f)

def process_do_reading(
    voltage_mv: int,
    temperature_c: int,
) -> int:
    """Compute dissolved oxygen from sensor voltage and temperature.

    Args:
    voltage_mv: Sensor voltage in millivolts.
    temperature_c: Water temperature in Celsius.
    cal1_v: Calibration voltage point 1.
    cal1_t: Calibration temperature point 1.
    cal2_v: Calibration voltage point 2 (required for two-point mode).
    cal2_t: Calibration temperature point 2 (required for two-point mode).

    Returns:
    Dissolved oxygen value as integer (same style as Arduino integer math).
    """
    # load config if config is none
    global DO_CONFIG
    if DO_CONFIG is None:
        DO_CONFIG = load_sen0237_config()
 
    do_lookup_table = DO_CONFIG.get("do_lookup_table")
    # Two-point calibration mode flag from original code.
    # 1 -> one-point formula, 2 -> two-point formula.
    calibration_formula = DO_CONFIG.get("calibration_formula")
    cal1_v = DO_CONFIG.get("cal1_v")
    cal1_t = DO_CONFIG.get("cal1_t")
    cal2_v = DO_CONFIG.get("cal2_v")
    cal2_t = DO_CONFIG.get("cal2_t")

    if calibration_formula == 1:
        v_saturation = cal1_v + 35 * temperature_c - cal1_t * 35
    elif calibration_formula == 2:
        if cal2_v is None or cal2_t is None:
            raise ValueError("cal2_v and cal2_t are required for two-point calibration")
        v_saturation = ((temperature_c - cal2_t) * (cal1_v - cal2_v)) // (cal1_t - cal2_t) + cal2_v
    else:
        raise ValueError("Invalid calibration formula. Valid values: 1, 2")

    return (voltage_mv * do_lookup_table[temperature_c]) // v_saturation