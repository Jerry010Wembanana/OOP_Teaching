import os

from deck import Deck
from player import Player

def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def print_cards_side_by_side(cards):
    rendered_cards = []

    for card in cards:
        rendered_cards.append(card.get_colored_lines())

    for line_number in range(7):
        for card_lines in rendered_cards:
            print(card_lines[line_number], end="  ")
        print()


def print_hand(player):
    print(f"{player.name}'s hand:")

    print_cards_side_by_side(player.hand)

    for i in range(len(player.hand)):
        print(f"     [{i}]     ", end="  ")

    print()


def get_card_choice(player):
    while True:
        try:
            choice = int(input("Choose a card index: "))

            if 0 <= choice < len(player.hand):
                return choice
            else:
                print("That card index is not in your hand.")

        except ValueError:
            print("Please enter a valid number.")


deck = Deck()
player1 = Player("Player 1")
player2 = Player("Player 2")

for i in range(5):
    player1.draw_card(deck)
for i in range(5):
    player2.draw_card(deck)

top_card = deck.draw()

while True:
    input("Press Enter to clear the screen and start your turn...")
    clear_screen()

    print("Top card:")
    print(top_card)

    print_hand(player1)

    choice = get_card_choice(player1)
    chosen_card = player1.hand[choice]

    print("You chose:")
    print(chosen_card)

    if chosen_card.can_play_on(top_card):

        top_card = player1.play_card(choice)
        if player1.hand == []:
            print(f"{player1.name} wins!")
            break
        print("New top card:")
        print(top_card)

    else:
        print("You cannot play this card.")
        print("You need to draw a card.")

        player1.draw_card(deck)

        print("Your hand after drawing:")
        print_hand(player1)
    
    input("Press Enter to clear the screen and start your turn...")
    clear_screen()

    print("Top card:")
    print(top_card)

    print_hand(player2)

    choice = get_card_choice(player2)
    chosen_card = player2.hand[choice]

    print("You chose:")
    print(chosen_card)

    if chosen_card.can_play_on(top_card):

        top_card = player2.play_card(choice)
        if player2.hand == []:
            print(f"{player2.name} wins!")
            break
        print("New top card:")
        print(top_card)

    else:
        print("You cannot play this card.")
        print("You need to draw a card.")

        player2.draw_card(deck)

        print("Your hand after drawing:")
        print_hand(player2)