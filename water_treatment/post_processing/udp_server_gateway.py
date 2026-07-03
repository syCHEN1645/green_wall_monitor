"""
This is the main listening loop for UDP server on Raspberry Pi
"""

import socket
import sys
import json

from config.general_config import LOCAL_IP, UDP_GATEWAY_PORT, UDP_BUFFER_SIZE, UDP_WEB_UI_PORT, UDP_PROCESSING_PORT

CONFIG_FILE = "config/general_config.json"

influx_client = None
# sockets, AF_INET is ipv4, SOCK_DGRAM is udp
s_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def start_up() -> bool:
    global s_rx, s_tx
    try:
        s_rx.bind(("0.0.0.0", UDP_GATEWAY_PORT))
        print(f"Listening for Uno on port {UDP_GATEWAY_PORT}")
    except Exception as e:
        print(f"Error starting UDP server: {e}")
        return False

    if influx_client is not None:
        return True
    return False

def main():
    if not start_up():
        print("Startup failed. Exiting.")
        sys.exit()

    # main program loop starts here
    assert influx_client is not None
    assert s_rx is not None
    assert s_tx is not None

    try: 
        while True:
            # data = the raw bytes packet, addr = (Uno_IP, Uno_Port)
            data, addr = s_rx.recvfrom(UDP_BUFFER_SIZE)

            try:
                payload = data.decode("utf-8")
                print(f"[From {addr[0]} received: {payload}]")

                # TODO
                is_data = True
                # only forward data packets to web_ui, ignore handshake packets
                if is_data:
                    # forward to web ui for display
                    try:
                        s_tx.sendto(data, (LOCAL_IP, UDP_WEB_UI_PORT))
                    except Exception as e:
                        # ignore if web ui is not running
                        pass
            
            except Exception as e:
                print(f"Error during listening: {e}")
        
    except KeyboardInterrupt:
        print("User terminated program.")

    finally:
        s_rx.close()
        s_tx.close()
        print("Sockets successfully closed.")

if __name__ == "__main__":
    main()