"""
This is the main listening loop for UDP server on Raspberry Pi
"""

import socket
import sys

# listen to all network interfaces
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
BUF_SIZE = 1024

try:
    # AF_INET is ipv4, SOCK_DGRAM is udp
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((UDP_IP, UDP_PORT))
    print(f"Listening for ESP32 on port {UDP_PORT}")
except Exception as e:
    print(f"Error starting UDP server: {e}")
    sys.exit()

try: 
    while True:
        # data = the raw bytes packet, addr = (ESP32_IP, ESP32_Port)
        data, addr = s.recvfrom(BUF_SIZE)

        try:
            payload = data.decode("utf-8")
            print(f"[From {addr[0]} received: {payload}]")

        except Exception as e:
            print(f"Error during listening: {e}")
    
except KeyboardInterrupt:
    print("User terminated program.")

finally:
    s.close()
    print("Socket successfully closed.")