import json
import socket
from bluffinmuffin import protocol as proto


class AIClient(object):

    def __init__(self, ai_type, server, port):
        self.ai_type = ai_type
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect(server, port)

    def _connect(self, server, port):
        print("Connection to {}:{} ... ".format(server, port), end="")
        self.socket.connect((server, port))
        print("Done")

        # Check version
        self._send(proto.lobby.CheckCompatibilityCommand({"ImplementedProtocolVersion": "2.2.0"}).encode())
        compat_rep = self._receive()
        if compat_rep['Success']:
            print("The server is compatible!")
        else:
            raise Exception("Server incompatible!!")

        # Identify
        ai_name = "AI-{}".format(self.ai_type)
        ai_id = 1
        ident_rep = {"Success": False}
        while not ident_rep['Success']:
            self._send(proto.lobby.quick_mode.IdentifyCommand({"Name": ai_name}).encode())
            ident_rep = self._receive()
            if not ident_rep['Success']:
                print(ident_rep['Message'] + " Trying a different one.")
                ai_name += str(ai_id)
                ai_id += 1
        print("Logged in as: {}".format(ai_name))

    def _send(self, msg):
        msg = "{}\n".format(msg).encode('ascii')
        sent = self.socket.send(msg)
        if sent != len(msg):
            raise RuntimeError("socket connection broken")

    def _receive(self):
        rep = b""
        while not rep.endswith(b'\n'):
            rep += self.socket.recv(100)
        return json.loads(rep.decode("utf-8"))

    def __del__(self):
        self._send(proto.DisconnectCommand({}).encode())
        print("Logged Out!")
        self.socket.shutdown(1)
        self.socket.close()
