import socket
import sys
import selectors

sel = selectors.DefaultSelector()

host, port = sys.argv[1], int(sys.argv[2])
address = (host, port)
BUFFER_SIZE = 1024

if len(sys.argv) != 3:
    print("[-] Usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setblocking(False)

try:
    client.connect_ex(address)
    print(f"[*] Connected to {host}:{port}")

    sel.register(client, selectors.EVENT_READ, selectors.EVENT_WRITE)

    while True:
        events = sel.select(timeout=1)

        for key, mask in events:
            if mask & selectors.EVENT_READ:
                try:
                    response = client.recv(BUFFER_SIZE)

                    if response:
                        print(f"[Server]: {response}")
                    else:
                        print("Connection closed")
                        sel.unregister(client)
                        client.close()
                        sys.exit(0)
            
                except ConnectionResetError:
                    print("[*] Connection reset by server")
                    sel.unregister(client)
                    client.close()
                    sys.exit(1)
            
            if mask & selectors.EVENT_WRITE:
                message = input("Type in message or use 'exit' to quit: ")
                if message.lower() == 'exit':
                    print("Client exiting")
                    sel.unregister(client)
                    client.close()
                    sys.exit(0)
                client.sendall(message.encode())

except ConnectionRefusedError:
    print(f"[-] Unable to connect to {host}:{port}")
    
except socket.error as e:
    print(f"[-] Socket error: {e}")

except Exception as e:
    print(f"[-] Unexpected error: {e}")

finally:
    print(f"[*] Disconnected from {host}:{port}")
    client.close()
