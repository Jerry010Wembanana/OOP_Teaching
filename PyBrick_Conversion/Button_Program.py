from pybricks.hubs import PrimeHub
from pybricks.parameters import Button, Color
from pybricks.tools import wait

hub = PrimeHub()

# Emergency stop to LEFT + RIGHT,
# CENTER can be used for run/stop inside our menu.
hub.system.set_stop_button((Button.LEFT, Button.RIGHT))


# Wait until all buttons are released
def wait_for_release():
    while hub.buttons.pressed():
        wait(10)

# Check if center button is pressed during a program
def stop_requested():
    pressed = hub.buttons.pressed()

    if Button.CENTER in pressed:
        hub.display.text("STOP")
        wait_for_release()
        return True

    return False



# Program 1
def program_1():
    hub.light.on(Color.RED)
    hub.display.text("P1")

    # Example running loop
    for i in range(20):
        if stop_requested():
            break

        hub.display.number(i % 10)
        wait(300)

    hub.light.off()


# Program 2
def program_2():
    hub.light.on(Color.GREEN)
    hub.display.text("P2")

    # Example running loop
    for i in range(10):
        if stop_requested():
            break

        hub.display.text("GO")
        wait(500)

    hub.light.off()


# Program 3
def program_3():
    hub.light.on(Color.BLUE)
    hub.display.text("P3")

    # Example running loop
    while True:
        if stop_requested():
            break

        hub.display.text("RUN")
        wait(500)

    hub.light.off()


# Program list
programs = [
    ("P1", program_1),
    ("P2", program_2),
    ("P3", program_3),
]

selected = 0


# Main menu
while True:
    name, selected_program = programs[selected]

    hub.display.text(name)

    pressed = hub.buttons.pressed()

    # Right button: next program
    if Button.RIGHT in pressed:
        selected = selected + 1

        if selected >= len(programs):
            selected = 0

        wait_for_release()

    # Left button: previous program
    elif Button.LEFT in pressed:
        selected = selected - 1

        if selected < 0:
            selected = len(programs) - 1

        wait_for_release()

    # Center button: run selected program
    elif Button.CENTER in pressed:
        wait_for_release()

        hub.display.text("RUN")
        wait(300)

        selected_program()

        hub.display.text("END")
        wait(500)

    wait(50)