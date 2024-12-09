#!/usr/bin/env python3

import logging
import selectors
import socket
import sys
import traceback

import libserver as libserver

from flask import Flask, jsonify, request, render_template
from game import Game

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sel = selectors.DefaultSelector()

app = Flask(__name__, static_folder="static", template_folder="templates")
game = Game()

def accept(socket):
    client_conn, client_address = socket.accept()
    print(f"[*] New client connection established from {client_address}")
    logger.info(f"New player joined: {client_address}")
    client_conn.setblocking(False)

    message = libserver.Message(sel, client_conn, client_address)
    sel.register(client_conn, selectors.EVENT_READ, data=message)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join_game():
    username = request.json.get("username")
    if game.started == False:
        return jsonify({"error": "Game has not been started"})
    if not username:
        return jsonify({"error": "Username is required"}), 400
    response = game.join_game(username)
    return jsonify({"message": response}), 200


@app.route('/start', methods=['POST'])
def start_game():
    username = request.json.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400
    response = game.start_game(username)
    return jsonify({"message": response}), 200


@app.route('/game_status', methods=['GET'])
def game_status():
    return jsonify({"players": game.players, "started": game.started, "host": game.host}), 200


@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    username = request.json.get("username")
    answer = request.json.get("answer")
    if not username or not answer:
        return jsonify({"error": "Username or answer is required"}), 400
    response = game.submit_answer(username, answer)
    return jsonify({"message": response}), 200


@app.route('/next_question', methods=['POST'])
def next_question():
    response = game.next_question()
    if response == "Quiz is over! Check leaderboard":
        leaderboard = game.get_leaderboard()
        return jsonify({"message": response, "leaderboard": leaderboard}), 200
    return jsonify({"message": response}), 200


@app.route('/current_question', methods=['GET'])
def current_question():
    question = game.get_current_question()
    return jsonify({"question": question}), 200


@app.route('/players_correct', methods=['GET'])
def players_correct():
    players = game.get_players_correct()
    return jsonify({"players": players}), 200

@app.route('/leaderborad', methods=['GET'])
def leaderboard():
    leaderboard = game.get_leaderboard()
    if not leaderboard:
        return jsonify({"error": "Error with leaderboard or no users got any questions right"}), 200
    return jsonify({"leaderboard": leaderboard}), 200
    

if len(sys.argv) != 3:
    print("[-] Usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
address = (host, port)
game_port = port + 1 # Gameport is offset from http port

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.setblocking(False)

lsock.bind(address)

lsock.listen()
print(f"[*] Listening on {host}:{port}")
lsock.setblocking(False)
logger.info('Server started listening')

sel.register(lsock, selectors.EVENT_READ, data=None)

try: 
    app.run(host=host, port=game_port)   
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept(key.fileobj)
            else:
                message = key.data
                try:
                    message.process_events(mask)
                except Exception as e:
                    print(
                        "Main: error: exception for",
                        f"{message.address}:\n{traceback.format_exc()}",
                    )
                    message.close()
                    logger.error(f"Error handling client: {e}")

except KeyboardInterrupt:
    print("Keyboard interrupt, exiting")
    logger.info("Server closed by user")
finally:
    sel.close()
    lsock.close()
    logger.info("Server shut down")
