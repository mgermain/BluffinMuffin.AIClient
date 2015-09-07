import json
import socket
from bluffinmuffin.protocol import CommandDecoder
from bluffinmuffin import protocol as proto
from bluffinmuffin.AIClient.AIType.random import Random as randomBot


def jprint(j):
    print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))


class AIClient(object):

    def __init__(self, ai_type, server, port):
        self.ai_type = ai_type
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect(server, port)

        self._currentTableId = None
        self._currentSeatId = None

    def _connect(self, server, port):
        print("Connection to {}:{} ... ".format(server, port), end="")
        self.socket.connect((server, port))
        print("Done")

        # Check version
        self._send(proto.lobby.CheckCompatibilityCommand(proto.__version__).encode())
        compat_rep = self._receive()
        if compat_rep.success:
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
        if join_tables_rep['Success']:
            self._currentTableId = best_table[1]
        table_status = self._receive()

        # Sit table
        self._send(proto.game.PlayerSitInCommand({"TableId": best_table[1], "NoSeat": 1, "MoneyAmount": best_table[2]['Params']['Lobby']['StartingAmount']}).encode())
        tables_sit_rep = self._receive()
        while tables_sit_rep['CommandName'] != "PlayerSitInResponse":
            tables_sit_rep = self._receive()

        if tables_sit_rep['Success']:
            self._currentSeatId = tables_sit_rep["NoSeat"]

        return tables_sit_rep['Success']

    def play(self):
        bot = None
        table_status = {}
        cards = []
        while True:
            rep = self._receive()
            cmd_name = rep['CommandName']

            if cmd_name == "TableInfoCommand":
                table_status = rep
                print("# Updated table status #")

            elif cmd_name == "GameStartedCommand":
                bot = randomBot(table_status["Seats"][self._currentSeatId]["Player"]["MoneySafeAmnt"])
                if rep['NeededBlindAmount'] > 0:
                    self._send(proto.game.PlayerPlayMoneyCommand({"TableId": self._currentTableId, "AmountPlayed": rep['NeededBlindAmount']}).encode())
                    #played_money_rep = self._receive()
                    #jprint(played_money_rep)
                    #if played_money_rep['CommandName'] != "PlayerPlayMoneyResponse":
                    #    raise Exception("11111OMGWTF TOTAL MONEY FAIL: {}".format(played_money_rep['CommandName']))
                    print("# Posted Blind #")
                    bot.total_bet_this_round = rep['NeededBlindAmount']
                    bot.total_money -= rep['NeededBlindAmount']
                    print("# Started Bot #")

            elif cmd_name == "PlayerHoleCardsChangedCommand":
                if rep["NoSeat"] == self._currentSeatId:
                    bot.set_hand(rep["Cards"])

            elif cmd_name == "PlayerTurnBeganCommand":
                #jprint(rep)
                if rep["NoSeat"] == self._currentSeatId:
                    #jprint(rep)
                    #jprint(table_status)
                    bet = bot.get_bet(rep["MinimumRaiseAmount"])
                    self._send(proto.game.PlayerPlayMoneyCommand({"TableId": self._currentTableId, "AmountPlayed": bet}).encode())
                    #played_money_rep = self._receive()
                    #jprint(played_money_rep)

            elif cmd_name == "BetTurnStartedCommand":
                if rep["BettingRoundId"] != 1 and bot is not None:
                    c = rep["Cards"]
                    filter(lambda x: x != '', c)
                    bot.start_betting_round(c)

            elif cmd_name == "PlayerTurnEndedCommand":
                if rep["NoSeat"] == self._currentSeatId:
                    #if bot.total_money != rep["TotalSafeMoneyAmount"]:
                    #    raise Exception("OMGWTF TOTAL MONEY FAIL: {}:{}".format(bot.total_money, rep["TotalSafeMoneyAmount"]))
                    bot.total_money = rep["TotalSafeMoneyAmount"]

            else:
                print("#################")
                print(rep['CommandName'])
                #jprint(rep)

    def find_table(self):
        if not self._join_table():
            raise Exception("No table to join!")
        # Need to add create table if no table available

    def _send(self, msg):
        msg = "{}\n".format(msg).encode('ascii')
        sent = self.socket.send(msg)
        if sent != len(msg):
            raise RuntimeError("socket connection broken")

    def _receive(self):
        rep = b""
        while not rep.endswith(b'\n'):
            rep += self.socket.recv(100)
        return CommandDecoder.decode(json.loads(rep.decode("utf-8")))

    def __del__(self):
        if self._currentSeatId:
            self._send(proto.game.PlayerSitOutCommand({"TableId": self._currentTableId}).encode())
            print("Sit out from table: {}".format(self._currentTableId))

        if self._currentTableId:
            self._send(proto.lobby.LeaveTableCommand({"TableId": self._currentTableId}).encode())
            print("Left table: {}".format(self._currentTableId))

        self._send(proto.DisconnectCommand({}).encode())
        print("Logged Out!")
        self.socket.shutdown(1)
        self.socket.close()
