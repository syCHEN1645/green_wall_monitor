import socket
import json
import random
import time

def main():
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        while True:
            for i in range(1, 4):
                reading = i * 1000 + random.randint(i * (-100), i * 100)

            
                # Create a sample JSON message
                message = {
                    "sensor": i,
                    "reading": reading,
                    "error": ""
                }
                
                # Convert the message to a JSON string
                json_message = json.dumps(message)
                # Send the JSON message to the server
                print(f"Sending message: {json_message}")
                sock.sendto(json_message.encode(), ('127.0.0.1', 5005))

                time.sleep(1)  # Wait for 1 second before sending the next message
            time.sleep(5)  # Wait for 5 seconds before sending the next batch of messages
    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the socket
        sock.close()


if __name__ == "__main__":
    main()
