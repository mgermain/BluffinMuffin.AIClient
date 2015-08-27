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

    def get_bet(self, min_bet):
        # 0=Fold, 1=Raise >1=Call
        move = rnd.randint(0, 3)
        if move == 0:
            bet = -1
        elif move == 1:
            # <50=Small, >50<80=Medium, >80<98=Large, >98=all-in
            z = np.argmax(np.random.multinomial(1, [0.5, 0.3, 0.18, 0.02])) + 1
            print("RAISE", min_bet, self.total_bet_this_round, self.total_money, z)
            bet = int((2 * min_bet - self.total_bet_this_round) * z)

        else:
            print("CALL", min_bet, self.total_bet_this_round)
            bet = min_bet - self.total_bet_this_round

        print("CURR MONEY", self.total_money - self.total_bet_this_round, bet)
        if bet > self.total_money:
            bet = self.total_money

        print("@@ Betted: {}".format(bet))
        if bet > -1:
            self.total_bet_this_round += bet
            self.total_money -= bet
        return bet
