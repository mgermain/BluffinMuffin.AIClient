import json
import socket

from bluffinmuffin import protocol as proto
from bluffinmuffin.protocol import CommandDecoder
from bluffinmuffin.protocol.enums import BluffinMessageIdEnum

from bluffinmuffin.AIClient.AIType import *


def jprint(j):
    print(json.dumps(json.loads(j), sort_keys=True, indent=4))
    print()


class AIClient(object):

    def __init__(self, ai_type, server, port):
        self.ai_type = ai_type
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect(server, port)

        self._currentTableId = None
        self._currentSeatId = None

    def _connect(self, server, port):
        print("# Connecting to {}:{} ... ".format(server, port), end="")
        self.socket.connect((server, port))
        print("Done")

        # Check version
        self._send(proto.lobby.CheckCompatibilityCommand(proto.__version__).encode())
        compat_rep = self._receive()
        if compat_rep.success:
            print("# Server protocole({}) is compatible with client({})!".format(compat_rep.implemented_protocol_version, proto.__version__))
        else:
            raise Exception("Server incompatible! Server({}) Client({})".format(compat_rep.implemented_protocol_version, proto.__version__))

    def identify(self):
        ai_name = "AI-{}{{}}".format(self.ai_type)
        ai_id = 1
        ident_rep = type('', (object,), {"success": False})()

        print("# Identifing to server ", end="")
        while not ident_rep.success:
            self._send(proto.lobby.quick_mode.IdentifyCommand(ai_name.format(ai_id)).encode())
            ident_rep = self._receive()

            if not ident_rep.success:
                if ident_rep.message_id is BluffinMessageIdEnum.NameAlreadyUsed:
                    print(". ", end="")
                    ai_id += 1
                else:
                    raise Exception("{}Error - {}: {}".format(ident_rep.command_name, ident_rep.message_id, ident_rep.message))

        self.ai_name = ai_name.format(ai_id)
        print("Logged in as: {}".format(self.ai_name))

    def _join_table(self):
        # List tables
        self._send(proto.lobby.ListTableCommand([proto.enums.LobbyTypeEnum.QuickMode]).encode())
        tables_rep = self._receive()

        best_table = type('', (object,), {"nb_players": -1})()
        for t in tables_rep.tables:
            if t.nb_players < t.params.max_players:
                if t.nb_players > best_table.nb_players:
                    best_table = t
        if best_table.nb_players == -1:
            return False

        # Join table
        self._send(proto.lobby.JoinTableCommand(best_table.id_table).encode())
        join_tables_rep = self._receive()
        if join_tables_rep.success:
            self._currentTableId = best_table.id_table
        table_status = self._receive()

        # Sit table
        self._send(proto.game.PlayerSitInCommand(best_table.id_table, 1, best_table.params.lobby.starting_amount).encode())
        tables_sit_rep = self._receive()
        while tables_sit_rep.command_name != "PlayerSitInResponse":
            tables_sit_rep = self._receive()

        if tables_sit_rep.success:
            self._currentSeatId = tables_sit_rep.no_seat

        return tables_sit_rep.success

    def find_table(self):
        if not self._join_table():
            raise Exception("No table to join!")
        # Need to add create table if no table available

    def play(self):
        bot = None
        table_status = None
        cards = []
        while True:
            rep = self._receive()
            print("##########{:^31}##########".format(rep.command_name))

            if rep.command_name == "TableInfoCommand":
                table_status = rep

            elif rep.command_name == "GameStartedCommand":
                curr_money = table_status.seats[self._currentSeatId].player.money_safe_amount
                if curr_money == 0:
                    print("# No more money! I lost ...")
                    return

                bot = eval(self.ai_type)(curr_money)
                print("\n# Started Bot {} | Type:{} Money:{} #".format(self.ai_name, self.ai_type, curr_money))

                if rep.needed_blind_amount > 0:
                    if rep.needed_blind_amount > bot.total_money:
                        raise Exception("Not enought money to pay blind. Money:{} Blind:{}".format(rep.needed_blind_amount, bot.total_money))
                    else:
                        self._send(proto.game.PlayerPlayMoneyCommand(self._currentTableId, rep.needed_blind_amount).encode())
                        bot.set_blind(rep.needed_blind_amount)
                        print("# Posted Blind {} #".format(rep.needed_blind_amount))

            elif rep.command_name == "PlayerHoleCardsChangedCommand":
                if rep.no_seat == self._currentSeatId:
                    bot.set_hand(rep.cards)

            elif rep.command_name == "PlayerTurnBeganCommand":
                if rep.no_seat == self._currentSeatId:
                    bet = bot.get_bet(rep.amount_needed, rep.minimum_raise_amount)
                    self._send(proto.game.PlayerPlayMoneyCommand(self._currentTableId, bet).encode())

            elif rep.command_name == "BetTurnStartedCommand":
                if rep.betting_round_id != 1 and bot is not None:
                    bot.start_betting_round([c for c in rep.cards if c != ''])

            elif rep.command_name == "PlayerTurnEndedCommand":
                if rep.no_seat == self._currentSeatId:
                    if bot.total_money != rep.total_safe_money_amount:
                        raise Exception("OMGWTF TOTAL MONEY FAIL: {}:{}".format(bot.total_money, rep.total_safe_money_amount))
                    bot.total_money = rep.total_safe_money_amount


    def _send(self, msg):
        msg = "{}\n".format(msg).encode('ascii')
        sent = self.socket.send(msg)
        if sent != len(msg):
            raise RuntimeError("socket connection broken")

    def _receive(self):
        # This number should small, this will avoid the ValueError caused by having 2 command in 1 rep
        buff_size = 10

        rep = b""
        while not rep.endswith(b'\n'):
            rep += self.socket.recv(buff_size)
        try:
            j = json.loads(rep.decode("utf-8"))
        except ValueError as e:
            print(rep)
            raise e

        return CommandDecoder.decode(j)

    def __del__(self):
        if self._currentSeatId:
            self._send(proto.game.PlayerSitOutCommand(self._currentTableId).encode())
            print("# Siting out from table: {}".format(self._currentTableId))

        if self._currentTableId:
            self._send(proto.lobby.LeaveTableCommand(self._currentTableId).encode())
            print("# Left table: {}".format(self._currentTableId))

        self._send(proto.DisconnectCommand().encode())
        print("# Logged Out!")
        self.socket.shutdown(1)
        self.socket.close()
