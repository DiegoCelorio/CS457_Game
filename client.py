import socket
import sys
import selectors
import json

sel = selectors.DefaultSelector()
BUFFER_SIZE = 1024
current_turn = None

def handle_server_response(response):
    data = json.loads(response)
    msg_type = data.get('type')

    if msg_type == 'status':
        players = data['payload']['players']
        current_turn = data['payload']['current_turn']
        message = data['payload']['message']

        print(f"Game Status: {message}")
        print("Players: ")
        for player in players:
            print(f"- {player['player name']} at {player['position']}")
    elif msg_type == 'chat':
        print(f"{data['payload']['players']['player name']} : {data['message']['payload']}")
    else:
        print("Unknown message received")


if len(sys.argv) != 3:
    print("[-] Usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

def main():
    host, port = sys.argv[1], int(sys.argv[2])
    address = (host, port)

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setblocking(False)

    try:
        client.connect_ex(address)
        print(f"[*] Connected to {host}:{port}")

        sel.register(client, selectors.EVENT_READ, selectors.EVENT_WRITE)

        player_name = input("Enter player name: ")
        join_message = json.dumps({
            "type":"join",
            "payload": {"player_name" : player_name}
        })
        client.send(join_message.encode())

        while True:
            events = sel.select(timeout=1)

            for key, mask in events:
                if mask & selectors.EVENT_READ:
                    try:
                        response = client.recv(BUFFER_SIZE)

                        if response:
                            handle_server_response(response.decode())
                        else:
                            print("[-] Connection closed")
                            sel.unregister(client)
                            client.close()
                            sys.exit(0)
            
                    except ConnectionResetError:
                        print("[*] Connection reset by server")
                        sel.unregister(client)
                        client.close()
                        sys.exit(1)
            
                if mask & selectors.EVENT_WRITE:
                    message = input("Enter 'move', 'chat' or use 'exit' to quit: ")
                    
                    if message.lower() == 'exit':
                        print("Client exiting")
                        sel.unregister(client)
                        client.close()
                        sys.exit(0)

                    elif message.lower() == 'move':
                        if current_turn == player_name:
                            player_move = input("Call your shot! (x,y): ").split(',')
                            move_message = json.dumps({
                                "type":"move",
                                "payload": {
                                    "position" : {"x": int(player_move[0]), "y": int(player_move[1])}
                                }
                            })
                            client.send(move_message.encode())
                        else:
                            print("It is not your turn yet")

                    elif message.lower() == 'chat':
                        player_chat = input("Enter chat:")
                        chat_message = json.dumps({
                            "type":"chat",
                            "payload": {
                                "message": player_chat
                            }
                        })
                        client.send(chat_message.encode())
                
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

if __name__ == "__main__":
    main()