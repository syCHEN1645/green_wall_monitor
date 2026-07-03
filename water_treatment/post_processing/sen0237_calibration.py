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
    voltage_mv: float
) -> float:
    """Compute dissolved oxygen from sensor voltage and temperature.

    Args:
    voltage_mv: Sensor voltage in millivolts.

    Returns:
    Dissolved oxygen value as float.
    """
    # load config if config is none
    global DO_CONFIG
    if DO_CONFIG is None:
        DO_CONFIG = load_sen0237_config()
    assert isinstance(DO_CONFIG, dict)

    do_lookup_table = DO_CONFIG.get("do_lookup_table")
    assert isinstance(do_lookup_table, dict)
    # Two-point calibration mode flag from original code.
    # 1 -> one-point formula, 2 -> two-point formula.
    calibration_formula = DO_CONFIG.get("calibration_formula")
    temp_c = DO_CONFIG.get("water_temperature")
    assert isinstance(temp_c, int) and 0 <= temp_c <= 41, "Temperature must be an integer between 0 and 41."
    cal1_v = DO_CONFIG.get("cal1_v")
    cal1_t = DO_CONFIG.get("cal1_t")
    cal2_v = DO_CONFIG.get("cal2_v")
    cal2_t = DO_CONFIG.get("cal2_t")

    """
    #if TWO_POINT_CALIBRATION == 0
    uint16_t V_saturation = (uint32_t)CAL1_V + (uint32_t)35 * temperature_c - (uint32_t)CAL1_T * 35;
    return (voltage_mv * DO_Table[temperature_c] / V_saturation);
    #else
    uint16_t V_saturation = (int16_t)((int8_t)temperature_c - CAL2_T) * ((uint16_t)CAL1_V - CAL2_V) / ((uint8_t)CAL1_T - CAL2_T) + CAL2_V;
    return (voltage_mv * DO_Table[temperature_c] / V_saturation);
    """

    if calibration_formula == 1:
        if cal1_v is None or cal1_t is None:
            raise ValueError("Calibration values for one-point calibration are not all set.")
        # Linear/One-point calibration formula
        v_saturation = cal1_v + 35 * temp_c - cal1_t * 35
        res = voltage_mv * do_lookup_table[temp_c] / v_saturation
    elif calibration_formula == 2:
        if cal1_v is None or cal1_t is None or cal2_v is None or cal2_t is None or temp_c is None:
            raise ValueError("Calibration values for two-point calibration are not all set.")
        # Two-point calibration formula
        v_saturation = (temp_c - cal2_t) * (cal1_v - cal2_v) / (cal1_t - cal2_t) + cal2_v
        res = voltage_mv * do_lookup_table[temp_c] / v_saturation
    else:
        raise ValueError("Invalid calibration formula. Must be 1 (one-point) or 2 (two-point).")
    
    return res

