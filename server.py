import logging
import selectors
import socket
import sys
import json


logging.basicConfig(level=logging.INFO)
sel = selectors.DefaultSelector()

host = sys.argv[1]
port = int(sys.argv[2])
address = (host, port)
BUFFER_SIZE = 1024
clients = {}

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

    for client_id, info in list(clients.items()):
        if info['socket'] == client_socket:
            del clients[client_id]
            broadcast_status(f"Player {info['name']} left the game.")
            break

def handle_message(client_socket, message):
    try:
        data = json.loads(message.decode())
        msg_type = data.get('type')
        payload = data.get('payload', {})

        if msg_type == 'join':
            handle_join(client_socket, payload)
        elif msg_type == 'move':
            handle_move(client_socket, payload)
        elif msg_type == 'chat':
            handle_chat(client_socket, payload)
        elif msg_type == 'quit':
            close_client(client_socket)
    except:
        print(f"[*] Invalid message from client try: 'join', 'move, 'chat' or use 'quit' to exit.")

def handle_join(client_socket, payload):
    player_name = payload.get('player_name')
    client_id = len(clients) + 1
    clients[client_id] = {'name': player_name}
    print(f"[+] Player {player_name} joined the game")
    broadcast_status(f"Player {player_name} joined the game")

def handle_move(client_socket, payload):
    player_move = payload.get('position')
    for client_id, info in clients.items():
        if info['socket'] == client_socket:
            info['position'] = player_move
            print(f"[+] Player {info['name']} striked {player_move}")
            broadcast_status(f"Player {info['name']} striked {player_move}")
            break

def handle_chat(client_socket, payload):
    player_chat = payload.get('message')
    for client_id, info in clients.items():
        if info['socket'] == client_socket:
            print(f"[*] Player {info['name']} said {player_chat}")
            broadcast_status(f"Player {info['name']} : {player_chat}")
            break

def broadcast_status(status_message):
    status = json.dumps({
        "type": "status",
        "payload": {
            'players': [{'player_name': info['name'], 'position': info['position']} for info in clients.values()],
            'message': status_message
        }
    })
    for client in clients.values():
        client['socket'].send(status.encode())

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