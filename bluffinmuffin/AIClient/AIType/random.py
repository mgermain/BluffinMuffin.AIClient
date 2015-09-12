import random as rnd
import numpy as np


class Random(object):

    def __init__(self, total_money):
        self.hand = []
        self.board = []
        self.total_bet_this_round = 0
        self.total_money = total_money

    def set_hand(self, hand):
        self.hand = hand
        print("@@ Received cards: {}".format(hand))

    def start_betting_round(self, board):
        print("@@ Board cards: {}".format(board))
        self.board = board
        self.total_bet_this_round = 0

    def get_bet(self, call_amount, min_raise):
        # 0=Fold, 1=Raise >1=Call
        move = rnd.randint(0, 3)
        if move == 0:
            bet = -1
        elif move == 1:
            # <50=Small, >50<80=Medium, >80<98=Large, >98=all-in
            z = int(np.argmax(np.random.multinomial(1, [0.5, 0.3, 0.18, 0.02])) + 1)
            print("RAISE", call_amount, min_raise, self.total_bet_this_round, self.total_money, z)
            bet = call_amount + (min_raise * z)

        else:
            print("CALL", call_amount, self.total_bet_this_round)
            bet = call_amount

        print("CURR MONEY", self.total_money - self.total_bet_this_round, bet)
        if bet > self.total_money:
            bet = self.total_money

        print("@@ Betted: {}".format(bet))
        if bet > -1:
            self.total_bet_this_round += bet
            self.total_money -= bet
        return bet
