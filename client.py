import socket
import sys
import selectors
import traceback
import logging
import requests

import libclient

sel = selectors.DefaultSelector()
BUFFER_SIZE = 1024

logging.basicConfig(
    filename='client.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SERVER_HTTP_PORT_OFFSET = 1


def create_request(msg_type, value):
    return dict(
        type="text/json",
        encoding="utf-8",
        content=dict(msg_type=msg_type, value=value)
    )


def start_connection(host, port, request):
    address = (host, port)
    print(f"Starting connection to: {address}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(address)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    message = libclient.Message(sel, sock, address, request)
    sel.register(sock, events, data=message)


def join_game_http(host, port, username):
    url = f"http://{host}:{port}/join"
    payload = {"username": username}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(response.json().get("message"))
        else:
            print(f"Error: {response.json().get('error')}")
    except Exception as e:
        print(f"Failed to join game via HTTP: {e}")


def start_game_http(host, port, username):
    url = f"http://{host}:{port}/start"
    payload = {"username": username}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(response.json().get("message"))
        else:
            print(f"Error: {response.json().get('error')}")
    except Exception as e:
        print(f"Failed to start game via HTTP: {e}")


def get_game_status_http(host, port):
    url = f"http://{host}:{port}/join"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            game_status = response.json()
            print(f"Game Status: {game_status}")
        else:
            print(f"Error: {response.json().get('error')}")
    except Exception as e:
        print(f"Failed to fetch game status via HTTP: {e}")


def submit_answer_http(host, port, username, answer):
    url = f"http://{host}:{port}/submit_answer"
    payload = {"username": username, "answer": answer}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(response.json().get("message"))
        else:
            print(f"Error: {response.json().get('error')}")
    except Exception as e:
        print(f"Failed to start game via HTTP: {e}")


def get_next_question_http(host, port, username):
    url = f"http://{host}:{port}/next_question"
    try:
        response = requests.post(url)
        if response.status_code == 200:
            print(response.json().get("message"))
        else:
            print(f"Error: {response.json().get('error')}")
    except Exception as e:
        print(f"Failed to start game via HTTP: {e}")


def main():
    if len(sys.argv) != 3:
        print("[-] Usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    http_port = port + SERVER_HTTP_PORT_OFFSET


    print("Options:")
    print("1. Join game via HTTP")
    print("2. Get game status via HTTP")
    print("3. Start game via HTTP")
    print("4. Quit")

    while True:
        choice = input("Enter choice: ")
        if choice == "1":
            username = input("Enter your username: ")
            join_game_http(host, http_port, username)
        if choice == "2":
            get_game_status_http(host, http_port)
        if choice == "3":
            username = input("Enter your username: ")
            start_game_http(host, http_port, username)
        elif choice == "4":
            print("quitting")
            sys.exit(1)
    '''
    msg_type = input("Enter name, or quit: ")
    if msg_type == 'name':
        value = input("Enter your name: ")
    elif msg_type == "quit":
        print("Client quitting")
        sys.exit(1)

    request = create_request(msg_type, value)
    start_connection(host, port, request)

    try:
        while True:
            events = sel.select(timeout=1)
            for key, mask in events:
                message = key.data
                try: 
                    message.process_events(mask)
                except Exception:
                    print(
                        "Main: error: exception for",
                        f"{message.address}:\n{traceback.format_exc()}",
                    )
                    message.close()
            if not sel.get_map():
                break
    

    except KeyboardInterrupt:
        print(" Caught keyboard interrupt closing")
    finally:
        sel.close()

'''

if __name__ == "__main__":
    main()