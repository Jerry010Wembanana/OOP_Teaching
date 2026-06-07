# This class represents one UNO card

class Card:
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def can_play_on(self, top_card):
        return self.color == top_card.color or self.value == top_card.value

    def get_color_code(self):
        color = self.color.lower()

        if color == "red":
            return "\033[31m"
        elif color == "blue":
            return "\033[34m"
        elif color == "green":
            return "\033[32m"
        elif color == "yellow":
            return "\033[33m"
        else:
            return "\033[0m"

    def get_card_lines(self):
        color_text = str(self.color).upper()
        value_text = str(self.value).upper()

        return [
            "╭───────────╮",
            f"│ {color_text:<9} │",
            "│           │",
            f"│ {value_text:^9} │",
            "│           │",
            f"│ {color_text:>9} │",
            "╰───────────╯"
        ]

    def get_colored_lines(self):
        color_code = self.get_color_code()
        reset_code = "\033[0m"

        colored_lines = []

        for line in self.get_card_lines():
            colored_line = color_code + line + reset_code
            colored_lines.append(colored_line)

        return colored_lines

    def __str__(self):
        return "\n".join(self.get_colored_lines())