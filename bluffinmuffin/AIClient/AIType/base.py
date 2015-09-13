
class BaseBot(object):

    def __init__(self, total_money):
        self.hand = []
        self.board = []
        self.total_bet_this_round = 0
        self.total_money = total_money

    def set_blind(self, amount):
        self.total_bet_this_round = amount
        self.total_money -= amount

    def set_hand(self, hand):
        self.hand = hand
        print("@@ Received cards: {}".format(hand))

    def start_betting_round(self, board):
        print("@@ Board cards: {}".format(board))
        self.board = board
        self.total_bet_this_round = 0

    def get_bet(self, call_amount, min_raise):
        raise NotImplementedError()
