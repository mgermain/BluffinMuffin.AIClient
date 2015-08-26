import json
import socket
from bluffinmuffin import protocol as proto


class AIClient(object):

    def __init__(self, ai_type, server, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect(server, port)

    def _connect(self, server, port):
        print("Connection to {}:{} ... ".format(server, port), end="")
        self.socket.connect((server, port))
        print("Done")

        self._send(proto.lobby.CheckCompatibilityCommand({"ImplementedProtocolVersion": "2.2.0"}).encode())
        compat_rep = self._receive()

        if compat_rep['Success']:
            print("The server is compatible!")
        else:
            raise Exception("Server incompatible!!")


    def _send(self, msg):
        msg = "{}\n".format(msg).encode('ascii')
        sent = self.socket.send(msg)
        if sent != len(msg):
            raise RuntimeError("socket connection broken")

    def _receive(self):
        rep = b""
        while not rep.endswith(b'\n'):
            rep += self.socket.recv(100)
        return json.loads(rep.decode("utf-8") )

    def __del__(self):
        self.socket.shutdown(1)
        self.socket.close()
