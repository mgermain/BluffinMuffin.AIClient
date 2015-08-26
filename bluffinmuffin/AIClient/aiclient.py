import json
import socket
from bluffinmuffin import protocol as proto

def jprint(j):
    print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))

class AIClient(object):

    def __init__(self, ai_type, server, port):
        self.ai_type = ai_type
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect(server, port)

        self._currentTableId = None

    def _connect(self, server, port):
        print("Connection to {}:{} ... ".format(server, port), end="")
        self.socket.connect((server, port))
        print("Done")

        # Check version
        self._send(proto.lobby.CheckCompatibilityCommand({"ImplementedProtocolVersion": proto.__version__}).encode())
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


    def _join_table(self):
        # List tables
        self._send(proto.lobby.ListTableCommand({"LobbyTypes": [proto.enums.LobbyTypeEnum.QuickMode.name]}).encode())
        tables_rep = self._receive()

        best_table = (-1, None)
        for t in tables_rep['Tables']:
            if t['NbPlayers'] < t['Params']['MaxPlayers']:
                if t['NbPlayers'] > best_table[0]:
                    best_table = (t['NbPlayers'], t['IdTable'], t)
        if best_table[0] == -1:
            return False

        # Join table
        self._send(proto.lobby.JoinTableCommand({"TableId": best_table[1]}).encode())
        join_tables_rep = self._receive()

        # Sit table
        self._send(proto.game.PlayerSitInCommand({"TableId": best_table[1], "NoSeat" : 1, "MoneyAmount": best_table[2]['Params']['Lobby']['StartingAmount']}).encode())
        tables_sit_rep = self._receive()
        if tables_sit_rep['Success']:
            self._currentTableId = best_table[1]

        return tables_sit_rep['Success']


    def find_table(self):
        if not self._join_table():
            raise Exception("No table to join!")


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
        ## Seems bugged at the moment
        #if self._currentTableId:
        #    self._send(proto.lobby.LeaveTableCommand({"TableId": self._currentTableId}).encode())
        #    print("Left table: {}".format(self._currentTableId))
        #    import time as t
        #    t.sleep(10)

        self._send(proto.DisconnectCommand({}).encode())
        print("Logged Out!")
        self.socket.shutdown(1)
        self.socket.close()
