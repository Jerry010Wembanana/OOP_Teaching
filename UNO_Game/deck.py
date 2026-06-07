import random
from card import Card

class Deck:
    def __init__(self):
        self.cards = []
        self.create_deck()
        self.shuffle()

    def create_deck(self):
        colors = ["Red", "Blue", "Green", "Yellow"]
        values = list(range(0,9))
        for color in colors:
            for value in values:
                self.cards.append(Card(color, value))

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()