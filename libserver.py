
import sys
import selectors
import json
import io
import struct

import logging
import game

BUFFER_SIZE = 4096

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Message:
    def __init__(self, sel, socket, address):
        self.sel = sel
        self.socket = socket
        self.address = address
        self.client_name = ""
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False

    def _set_selector_events_mask(self, mode):
        if mode == "r":
            events = selectors.EVENT_READ
            logger.info("Server ready to read")
        elif mode == "w":
            events = selectors.EVENT_WRITE
            logger.info("Server ready to write")
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE

        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}")
        
        self.sel.modify(self.socket, events, data=self)

# Message class
    def _read(self):
        try:
            message = self.socket.recv(BUFFER_SIZE)
        except BlockingIOError:
            pass
        else:
            if message:
                self._recv_buffer += message
            else:
                raise RuntimeError("Peer closed.")
        

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer), "to", self.address)
            try:
                sent = self.socket.send(self._send_buffer)
            except BlockingIOError:
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                #Close when buffer empty
                if sent and not self._send_buffer:
                    pass
                    


    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)


    def _json_decode(self, json_bytes, encoding):   
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj


    def _create_message(self, *, content_bytes, content_type, content_encoding):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_header = struct.pack(">H", len(jsonheader_bytes))
        message = message_header + jsonheader_bytes + content_bytes
        return message


    def _create_response_json_content(self):
        msg_type = self.request.get("msg_type")

        if self.request.get("value"):
            value = self.request.get("value")

        if msg_type == 'name':
            if value:
                self.client_name = value
                logger.info(f"Username registered: {self.client_name}")
                answer = {"payload": "Enter join to join a game or start to start a game: "}
                content = {"result": answer}

        elif msg_type == 'chat':
            self.handle_chat(value)


        elif msg_type == "result":
            if value == 'start':
                success = game.Game.start_game(self.address,self.client_name)
                if success:
                    content = {"result": {"status": "Successfully started game"}}
                else:
                    content = {"result": {"status": "Failed to start game"}}

            elif value == 'join':
                success = game.Game.join_game(self.address,self.client_name)
                if success:
                    content = {"result": {"status": "Successfully joined game"}}
                else:
                    content = {"result": {"status": "Failed to join game"}}

        elif msg_type == 'quit':
            content = {"result": {"status": "Goodbye"}}
            self.close()

        content_encoding = "utf-8"
        response = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": "text/json",
            "content_encoding": content_encoding,
        }
        return response


    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()


    def read(self):
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.request is None:
                self.process_request()


    def write(self):
        if self.request:
            if not self.response_created:
                self.create_response()

        self._write()


    def close(self):
        print("closing connection to", self.address)
        try:
            self.sel.unregister(self.socket)
        except Exception as e:
            print(
                f"error: selector.unregister() exception for",
                f"{self.address}: {repr(e)}"
            )            
        
        try:
            self.socket.close()
            logger.info('Player left the server')
        except OSError as e:
            print(
                f"error: socket.close() exception for",
                f"{self.address}: {repr(e)}"
            )
        finally:
            self.socket = None


    def process_protoheader(self):
        header_len = 2
        if len(self._recv_buffer) >= header_len:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:header_len]
            )[0]
            self._recv_buffer = self._recv_buffer[header_len:]


    def process_jsonheader(self):
        header_len = self._jsonheader_len
        if len(self._recv_buffer) >= header_len:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:header_len], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[header_len:]
            for reghdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reghdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reghdr}')


    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = self._json_decode(data, encoding)
            print("received request", repr(self.request), "from", self.address)
        else:
            print("Not in text/json format, cannot be read")

        self._set_selector_events_mask("w")

    
    def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
                response = self._create_response_json_content()
        else:
            print("Message has to be in JSON format")
            #Error
        message = self._create_message(**response)
        self.response_created = True
        self._send_buffer += message

        #set selector to read after creating a response
        self._set_selector_events_mask("r")

    '''
    def close_client(self):
        self.sel.unregister(self.socket)
        self.socket.close()
        print(f"[*] Client disconnected")
        logger.info('Player left the server')

        for client_id, info in list(clients.items()):
            if info['socket'] == client_socket:
                del clients[client_id]
                broadcast_status(f"Player {info['name']} left the game.")
                break
            update_turn()
    '''

    def handle_chat(self, value):
        player_chat = value.get('message')
        '''
        for client_id, info in self.socket.items():
            if info['socket'] == self.socket:
                broadcast_status(f"[*] {info['name']} : {player_chat}")
                break
                '''

    
    # This method will compare if the answer the play gave matches with the correct answer
    def handle_answer(self, value):
        player_answer = value.get('value')
        if player_answer:
            pass
            
    '''
    def broadcast_status(status_message):
        status = json.dumps({
            "type": "status",
            "payload": {
                'players': [{'player_name': info['name']} for info in clients.values()],
                'message': status_message
            }
        })
        for client in clients.values():
            client['socket'].send(status.encode())


    def broadcast_chat(chat_message):
        chat = {'type': 'chat', 'payload': {'message': chat_message}}
        for client in clients.values():
            client['socket'].send(json.dumps(chat).encode())
    '''

    def start_game(self):
        game_started = True
        return
        
