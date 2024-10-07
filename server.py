import logging
import selectors
import socket
import sys


logging.basicConfig(level=logging.INFO)
sel = selectors.DefaultSelector()

host = sys.argv[1]
port = int(sys.argv[2])
address = (host, port)
BUFFER_SIZE = 1024

if len(sys.argv) != 3:
    print("[-] Usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

def accept(server, mask):
    client_socket, client_address = server.accept()
    print(f"[*] New client connection established from {client_address}")
    client_socket.setblocking(False)
    sel.register(client_socket, selectors.EVENT_READ, read)

def read(client_socket, mask):
    try:
        message = client_socket.recv(BUFFER_SIZE)
        if message:
            print(f"[+] Message: {message} received from {client_socket}")
            # Echo back message to client
            client_socket.send(message)
        else:
            close_client(client_socket)
    except:
        close_client(client_socket)

def close_client(client_socket):
    sel.unregister(client_socket)
    client_socket.close()
    print(f"[*] Client disconnected")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.setblocking(False)

server.bind(address)

server.listen()
print(f"[*] Listening on {host}:{port}")

sel.register(server, selectors.EVENT_READ, accept)

while True:
    events = sel.select()
    for key, mask in events:
        message = key.data
        message(key.fileobj, mask)