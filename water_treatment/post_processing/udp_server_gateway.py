"""
This is the main listening loop for UDP server on Raspberry Pi
"""

import socket
import sys
import json
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from config.general_config import INFLUXDB_BUCKET, INFLUXDB_ORG, INFLUXDB_TOKEN, INFLUXDB_URL, \
    UDP_IP, UDP_PORT, UDP_BUFFER_SIZE, FORWARD_PORT_WEB_UI, FORWARD_PORT_PROCESSING

CONFIG_FILE = "config/general_config.json"

influx_client = None
# sockets, AF_INET is ipv4, SOCK_DGRAM is udp
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
forward_socket_web_ui = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
forward_socket_processing = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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
        sys.exit()

    try:
        s.bind((UDP_IP, UDP_PORT))
        print(f"Listening for ESP32 on port {UDP_PORT}")

        forward_socket_web_ui.bind((UDP_IP, FORWARD_PORT_WEB_UI))
        forward_socket_processing.bind((UDP_IP, FORWARD_PORT_PROCESSING))
    except Exception as e:
        print(f"Error starting UDP server: {e}")
        sys.exit()

    if influx_client is not None:
        return True
    return False

def main():
    if not start_up():
        print("Startup failed. Exiting.")
        sys.exit()

    # main program loop starts here
    assert influx_client is not None
    assert s is not None

    write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    try: 
        while True:
            # data = the raw bytes packet, addr = (ESP32_IP, ESP32_Port)
            data, addr = s.recvfrom(UDP_BUFFER_SIZE)

            try:
                payload = data.decode("utf-8")
                print(f"[From {addr[0]} received: {payload}]")

                # TODO: parse payload
                # payload should have 2 types, handshake and data
                # handshake, data, data, ..., auto close at last data

                # write to InfluxDB
                # point = (
                #     Point("sensor_data")
                #     .tag("source", addr[0])
                #     .field("data", payload)
                # )
                # write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

                # TODO
                is_data = True
                # only forward data packets to web_ui, ignore handshake packets
                if is_data:
                    # forward to web ui for display
                    try:
                        forward_socket_web_ui.sendto(data, ("127.0.0.1", FORWARD_PORT_WEB_UI))
                    except Exception as e:
                        # ignore if web ui is not running
                        pass
            
            except Exception as e:
                print(f"Error during listening: {e}")
        
    except KeyboardInterrupt:
        print("User terminated program.")

    finally:
        s.close()
        print("Socket successfully closed.")
        influx_client.close()
        print("InfluxDB client successfully closed.")

if __name__ == "__main__":
    main()