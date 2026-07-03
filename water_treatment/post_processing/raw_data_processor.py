import sys
import json
import socket
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from sen0237_calibration import process_do_reading
from sen0464_calibration import process_orp_reading
from config.general_config import SENSOR_TYPES, LOCAL_IP, UDP_PROCESSING_PORT, UDP_BUFFER_SIZE, INFLUXDB_URL, INFLUXDB_TOKEN, INFLUXDB_ORG, INFLUXDB_BUCKET

"""
expected Json structure:
error:
    doc["sensor"] = 0;
    doc["reading"] = 0;
    doc["error"] = "Uno: Invalid sensor type";
good data:
    doc["sensor"] = SENSOR_TYPES[sensor_type];
    doc["reading"] = reading;
    doc["error"] = "";
"""
influx_client = None
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def start_up() -> bool:
    global influx_client, s
    try:
        influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
    except Exception as e:
        print(f"Error connecting to InfluxDB: {e}")
        return False

    try:
        s.bind((LOCAL_IP, UDP_PROCESSING_PORT))
        print(f"Listening for UDP gateway on port {UDP_PROCESSING_PORT}")

    except Exception as e:
        print(f"Error starting UDP socket: {e}")
        return False

    if influx_client is not None:
        return True
    return False


def main():
    if not start_up():
        print("Startup failed. Exiting.")
        sys.exit()

    assert influx_client is not None
    assert s is not None

    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    while True:
        try:
            data, addr = s.recvfrom(UDP_BUFFER_SIZE)
            payload = json.loads(data.decode("utf-8"))

            assert isinstance(payload, dict)
            if "sensor" not in payload or "reading" not in payload or "error" not in payload:
                raise ValueError("Payload missing essential keys: 'sensor', 'reading', or 'error'")
            if payload["error"]:
                raise ValueError(f"Received error: {payload['error']}")

            sensor_type_id = payload["sensor"]
            reading = payload["reading"]
            assert isinstance(sensor_type_id, int)
            assert isinstance(reading, int)
            if sensor_type_id not in SENSOR_TYPES.values():
                raise ValueError(f"Invalid sensor type ID: {sensor_type_id}")
            
            if sensor_type_id == SENSOR_TYPES["DO"]:
                processed_reading = process_do_reading(float(reading))
                measurement_name = "DO"
            elif sensor_type_id == SENSOR_TYPES["ORP"]:
                processed_reading = process_orp_reading(float(reading))
                measurement_name = "ORP"
            elif sensor_type_id == SENSOR_TYPES["PH"]:
                processed_reading = 1.0
                measurement_name = "PH"
            else:
                raise ValueError(f"Unsupported sensor type ID: {sensor_type_id}")

            # write to InfluxDB
            point = (
                Point("water_treatment")
                .measurement("water_treatment")
                .field(measurement_name, processed_reading)
            )
            write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)


        except Exception as e:
            print(f"Error receiving data: {e}")
            continue

if __name__ == "__main__":
    main()