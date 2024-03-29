
import test_snakes.dubbyOnline.main
import test_snakes.dubbyOnline2.main
import test_snakes.dubbyOnline3.main


COLORS = {
    "black": "\033[1;37;40m",
    "red": "\033[1;37;41m",
    "green": "\033[1;37;42m",
    "yellow": "\033[1;37;43m",
    "blue": "\033[1;37;44m",
    "purple": "\033[1;37;45m",
    "cyan": "\033[1;37;46m",
    "grey": "\033[1;37;47m",
    "default": "\033[0m"
    }

"""
{
 "move": The function that responds to the /move request,
 "name": The snakes name, must be unique,
 "color": A color from the list of colors
 }
"""

SNAKES = []

SNAKES.append({
        "move": test_snakes.dubbyOnline.main.move,
        "name": "dubbyOnline",
        "color": COLORS["red"]
    })

SNAKES.append({
        "move": test_snakes.dubbyOnline2.main.move,
        "name": "dubbyOnline2",
        "color": COLORS["cyan"]
    })

SNAKES.append({
        "move": test_snakes.dubbyOnline3.main.move,
        "name": "dubbyOnline3",
        "color": COLORS["purple"]
    })