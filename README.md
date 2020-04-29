# BattleSnakeArena
A modified, terminal based, [Battle Snake](https://play.battlesnake.io/) arena to bypass servers and have complete access to data.

## Requirements
- A Bash shell
- Python3
- A few packages for Python3 that you probably already have

## For Linux
- Open terminal in ./BattleSnakeArena
- run bash script using command ./requirements.sh

## For Windows (not recommended, GUI doesn't sync up properly)
- Assuming you have 64-bit Windows, head to Control Panel > Programs > Turn Windows Features On Or Off. Enable the “Windows Subsystem for Linux” option in the list, and then click the “OK” button.
- Click “Restart now” when you’re prompted to restart your computer. The feature won’t work until you reboot.
- After your computer restarts, open the Microsoft Store from the Start menu, and search for “Linux” in the store. Select "Ubuntu", Click “Get". 
- Click Launch to install. After launch you will be prompted to enter a username and password.
- Hold shift then right click in any directory, select "Open Linux shell here", type in the following commands:
	- sudo apt-get update
	- sudo apt-get upgrade
	- sudo apt-get install python3-pip
	- sudo pip3 install uuid
	- sudo pip3 install tqdm	
	- sudo pip3 install bottle

## Test Snakes
This repository comes with a few snakes for testing.

### battleJake2019
This was my snake entered into Battle Snake 2019.

### battleJake2018
This was my snake entered into Battle Snake 2018.

### simpleJake
A snake that only knows how to not hit walls and other snakes but has a good smell for food.

### hungryJake
A snake whos top priority is to "get that brunch".

## Adding Your Own Snake
Adding your own snake is simple! Your snake just needs to be written in python3.

1. Make a quick modification to your snake in the "move" function. (Don't worry, it can still function as a server)
```python3
def move(data=None):
    if not data:
        data = bottle.request.json
```

2. Add your snake to snakes.py
```python3
//The snake we are adding in this example is my_snake.py
import test_snakes.my_snake.main

#Make sure this append happens after SNAKES = []
SNAKES.append({
        "move": test_snakes.my_snake.main.move,
        "name": "mysnake",
        "color": COLORS["red"]
    })
```

Import your file and make a dictionary in the SNAKES list to tell the arena about your snake.

## Running A Game
There is a command line interface for running games through battleSnake.py. For help run:
```
python3 battlesnake.py -h
```

### Running A Single Game
"Run a game with the snakes battleJake2018 and battleJake2019"
```
python3 battlesnake.py -s battleJake2018 battleJake2019
```

### Running Many Games Without Board Output
"Run 10 games without board output at 100% speed with battleJake2018, battleJake2019, simpleJake, and hungryJake"
```
python3 battlesnake.py -g 10 -b -sp 100 -s battleJake2018 battleJake2019 simpleJake hungryJake
```
