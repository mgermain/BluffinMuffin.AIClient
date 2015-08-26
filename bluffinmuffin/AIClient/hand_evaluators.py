import json


class PreflopHandEvaluator(object):
    def __init__(self, nb_players, probs_json_file):
        self.nb_players = nb_players
        self.all_probs = json.load(open(probs_json_file))
        self.probs = self.all_probs[str(nb_players)]

    def evaluate(self, hole_cards):
        hand = hole_cards[0][0] + hole_cards[1][0]
        reverse_hand = hole_cards[1][0] + hole_cards[0][0]

        if hole_cards[0][0] == hole_cards[1][0]:  # A pair
            pass
        elif hole_cards[0][1] == hole_cards[1][1]:  # Same suits
            hand += "s"
            reverse_hand += "s"
        else:
            hand += "o"
            reverse_hand += "o"

        if hand in self.probs:
            return self.probs[hand]

        # Try the other way around
        return self.probs[reverse_hand]
