import random as rnd
import numpy as np
from .base import BaseBot

class Random(BaseBot):

    def get_bet(self, call_amount, min_raise):
        # 0=Fold, 1=Raise >1=Call
        move = rnd.randint(0, 3)
        if move == 0:
            bet = -1
            print("@@ FOLD")
        elif move == 1:
            # <50=Small, >50<80=Medium, >80<98=Large, >98=all-in
            z = int(np.argmax(np.random.multinomial(1, [0.5, 0.3, 0.18, 0.02])) + 1)
            print("@@ RAISE", call_amount, min_raise, self.total_bet_this_round, self.total_money, z)
            bet = call_amount + (min_raise * z)

        else:
            print("@@ CALL", call_amount, self.total_bet_this_round)
            bet = call_amount

        if bet > self.total_money:
            print("@@ ALL IN", call_amount, min_raise, self.total_money, bet)
            bet = self.total_money

        if bet > -1:
            self.total_money -= bet
        return bet

class Raiser(BaseBot):

    def get_bet(self, call_amount, min_raise):
        print("@@ RAISE", call_amount, min_raise, self.total_bet_this_round, self.total_money)
        bet = call_amount + min_raise

        if bet > self.total_money:
            print("@@ ALL IN", call_amount, min_raise, self.total_money, bet)
            bet = self.total_money

        if bet > -1:
            self.total_money -= bet
        return bet

class Caller(BaseBot):

    def get_bet(self, call_amount, min_raise):
        print("@@ CALL", call_amount, self.total_bet_this_round)
        bet = call_amount

        if bet > self.total_money:
            print("@@ ALL IN", call_amount, min_raise, self.total_money, bet)
            bet = self.total_money

        if bet > -1:
            self.total_money -= bet
        return bet
