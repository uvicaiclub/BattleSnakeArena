
###########################################
###### UVIC AI CLUB BATTLESNAKE 2020 ######
###########################################

import os
import random
import cherrypy


#Conversion from online to offline arena
def move(data):
    snake = Battlesnake()
    return snake.move(data)


######################################
###### INCLUDED STARTER METHODS ######
######################################

class Battlesnake(object):
    @cherrypy.expose
    def index(self):
        # If you open your snake URL in a browser you should see this message.
        return "Your Battlesnake is alive!"


    @cherrypy.expose
    def ping(self):
        # The Battlesnake engine calls this function to make sure your snake is working.
        return "pong"


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def start(self):
        # This function is called everytime your snake is entered into a game.
        # cherrypy.request.json contains information about the game that's about to be played.
        # TODO: Use this function to decide how your snake is going to look on the board.
        data = cherrypy.request.json
        print("START")
        return {"color": "#888888", "headType": "regular", "tailType": "regular"}


######################################
######### MOVE COMMAND BEGINS ########
######################################

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def move(self, data=None):

        #Allows offline use
        if data == None:
            data = cherrypy.request.json


        ######################################
        ############# GATHER DATA ############
        ######################################

        #Standard information about our snake
        you = data['you']
        you['name'] = you['name']
        you['body'] = [ (b['x'], b['y']) for b in you['body'] ]
        you['head'] = you['body'][0]
        you['tail'] = you['body'][-1]
        you['size'] = len(you['body'])
        position = (you["head"][0], you["head"][1])

        #Standard information about our environment
        food = [(f['x'], f['y']) for f in data['board']['food']]
        board = data['board']
        snakes = data["board"]["snakes"]
        turn = data['turn']
        opponents = len(snakes) - 1

        #Hunger threshold
        hungry = False
        health = you["health"]
        if health <= 50:
            hungry = True

        #Tracks which snakes have recently eaten food
        #Useful because their tail will stay in place next round
        snake_ate = {}
        for s in snakes:
            if s["health"] == 100:
                snake_ate[s["name"]] = True
                continue
            snake_ate[s["name"]] = False

        #Locates snake tails
        tails = []
        for snake in snakes:
            tails.append((snake["body"][-1]['x'], snake["body"][-1]['y']))

        #Locates snake heads (Excludes ours)
        heads = []
        for snake in snakes:
            if snake["name"] != you['name']:
                heads.append((snake["body"][0]['x'], snake["body"][0]['y']))
        
        #Snakes that are bigger than Dubby
        bigger_snakes = []
        for snake in snakes:
            if snake["name"] == you['name']: continue
            if len(snake["body"]) >= you["size"]:
                bigger_snakes.append(snake["name"])


        #################################
        ######### GROW SEQUENCE #########
        #################################

        #Used to initiate grow sequence (become bigger than other snakes)
        grow = False
        for snake in snakes:
            if snake["name"] == you['name']: continue
            if len(snake["body"]) >= you["size"] - 2:
                grow = True

        #Don't try to compete with glutenous snakes
        for snake in snakes:
            if snake["name"] == you['name']: continue
            if len(snake["body"]) >= you["size"] + 2 + (6 / opponents):
                grow = False


        ############################################
        ######### STANDARD DATA PROCESSING #########
        ############################################

        #All the available board space
        all_available = self.allAvailableSpace(board)

        #adds tails space that will move to available space
        if turn >= 2:
            for snake in snakes:
                if snake_ate[snake["name"]] == False:    
                        snake_tail = (snake["body"][-1]['x'], snake["body"][-1]['y'])
                        all_available.append(snake_tail)

        #Dictionary of tuple -> move string
        possible_moves = self.possibleMoves(position, all_available)

        #Dictionary of move string -> tuple
        inverse_possible_moves = self.InversePossibleMoves(position, all_available)

        #Sorts adjacent moves based on next turn availability
        safe_moves, limiting_moves, restricted_moves, dead_ends = self.safeMoves(position, inverse_possible_moves, all_available)

        #All possible moves (excluding walls and bodys)
        moves = list(possible_moves.keys())

        #Moves where snakes could kill us
        critical_moves =  self.criticalMoves(position, board, snakes, bigger_snakes)
        non_critical_moves = self.setDifference(moves, critical_moves)

        #Finds the closest food
        closest_food = []
        closest_food.append(self.closestFood(you, board))
        
        #Finds the most direct route to closest food
        food_move = []
        if closest_food != [[]]:
            closest_food = self.setDifference(closest_food, self.allCorners(board))
            try:
                food_move.append(inverse_possible_moves[(self.breadthFirst(all_available, board, position, closest_food[0]))[0]])
            except:
                pass

        #used to coil snake
        tail_move = self.leanTail(position, you["tail"])
        tail_move = self.setIntersection(tail_move, moves)

        #lean towards board centre
        centre_board_move = self.leanBoard(position, board)
        centre_board_move = self.setIntersection(centre_board_move, moves)

        # Lean away from snake head
        if opponents > 0:
            closest_enemy = self.closestEnemy(position, snakes, you["name"])
            defensive_move = self.leanEnemy(position, closest_enemy)
            defensive_move = self.setIntersection(defensive_move, moves)

        #Preemptive area fill
        all_available1 = all_available.copy()
        for h in heads:
            temp = self.adjacentMoves(h, all_available)
            for i in temp:
                try:
                    all_available1.remove(i)
                except:
                    pass

        #Fill algorithm on current board state (resource intensive and not currently used)
        direction_area0 = self.directionArea(position, possible_moves, board, all_available)        
        new_direction_area0, nda_index0 = self.think(direction_area0)
        area_moves0 = []
        non_critical_area_moves0 = []
        for i in nda_index0:
            if area_moves0 == []:
                area_moves0 = new_direction_area0[i]
            non_critical_area_moves0 = self.setIntersection(non_critical_moves, new_direction_area0[i])
            if non_critical_area_moves0 != []:
                break

        #Fill algorithm on possible next turn board state
        direction_area1 = self.directionArea(position, possible_moves, board, all_available1)
        new_direction_area1, nda_index1 = self.think(direction_area1)
        area_moves1 = []
        non_critical_area_moves1 = []
        for i in nda_index1:
            if area_moves1 == []:
                area_moves1 = new_direction_area1[i]
            non_critical_area_moves1 = self.setIntersection(non_critical_moves, new_direction_area1[i])
            if non_critical_area_moves1 != []:
                break


        #########################################
        ######### IMPLIMENTED BEHAVIOUS #########
        #########################################

        #Combines Non-critical moves with safe moves
        non_critical_moves = self.setIntersection(non_critical_moves, non_critical_area_moves1)
        non_critical_safe_moves = self.setIntersection(safe_moves, non_critical_moves)
        non_critical_safe_moves = self.setIntersection(non_critical_safe_moves, moves)

        #Determines attack moves and safe attack moves
        attack_move_safe = []
        attack_move = []
        if len(snakes) > 1:
            attack_move = self.attackSnake(position, snakes, bigger_snakes, closest_enemy)
            attack_move = self.setIntersection(non_critical_moves, attack_move)
            attack_move = self.setDifference(attack_move, restricted_moves)
            attack_move = self.setDifference(attack_move, dead_ends)
            attack_move_safe = self.setIntersection(attack_move, non_critical_safe_moves)

        #Modify tail move and implements safe tail moves
        tail_move = self.setDifference(tail_move, dead_ends)
        tail_move = self.setDifference(tail_move, critical_moves)
        tail_move_safe = self.setDifference(tail_move, restricted_moves)
        tail_move_safe = self.setIntersection(tail_move_safe, non_critical_area_moves1)
        tail_move_safe = self.setIntersection(tail_move_safe, centre_board_move)

        #Modify food move and implements safe food move
        food_move = self.setDifference(food_move, dead_ends)
        food_move = self.setIntersection(food_move, non_critical_area_moves1)
        food_move_safe = self.setDifference(food_move, restricted_moves)
        food_move_safe = self.setDifference(food_move_safe, critical_moves)

        #Modify defensive move
        if opponents > 0:
            defensive_move = self.setIntersection(defensive_move, non_critical_area_moves0)
            defensive_move = self.setIntersection(defensive_move, centre_board_move)

        #Seed for random
        random.seed()


        ########################################
        ###### INITIATE PRIORITY SEQUENCE ######
        ########################################

        #Priority 0: Eat food safely when hungry or to grow
        priority = 0
        if (hungry == True) or (grow == True):
            if food_move_safe !=[]:
                # print("Priority {}".format(priority))
                return {
                'move': food_move_safe[0],
                'taunt': 'RAWR!'
                }

        #Priority 1: Attack snakes when they are restricted
        if attack_move !=[]:
            ce_inverse_possible_moves = self.InversePossibleMoves(closest_enemy, all_available)
            ce_safe_moves, ce_limiting_moves, ce_restricted_moves, ce_dead_ends = self.safeMoves(closest_enemy, ce_inverse_possible_moves, all_available)
            if len(ce_restricted_moves) == 1:
                # print("Priority {}".format(priority))
                rand = random.choice(attack_move)
                return {
                'move': rand,
                'taunt': 'RAWR!'
                }

        #Priority 2: Attack snakes safely
        priority += 1
        if attack_move_safe != []:
            # print("Priority {}".format(priority))
            rand = random.choice(attack_move_safe)
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }

        #Priority 3: Attack snakes
        priority += 1
        if attack_move != []:
            # print("Priority {}".format(priority))
            rand = random.choice(attack_move)
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }

        #Priority 4: Coil safely
        priority += 1
        if tail_move_safe != []:
            # print("Priority {}".format(priority))
            rand = random.choice(tail_move_safe)
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }
        
        #Priority 5: Stay safe
        priority += 1
        if non_critical_safe_moves != []:
            # print("Priority {}".format(priority))
            rand = random.choice(non_critical_safe_moves)
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }

        #Priority 6: Non-Critical moves
        priority += 1
        if non_critical_moves !=[]:
            # print("Priority {}".format(priority))
            rand = random.choice(non_critical_moves)
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }

        #Priority 7: Hard Coil: Ignores area fill
        priority += 1
        tail_move = []
        try:
            tail_move.append(inverse_possible_moves[(self.breadthFirst(all_available, board, position, you['tail']))[0]])
        except:
            pass
        if tail_move !=[]:
            # print("Priority {}".format(priority))
            return {
            'move': tail_move[0],
            'taunt': 'RAWR!'
            }

        #Priority 8: Critically available
        priority += 1
        #Automatically move towards tail
        if you["tail"] in self.adjacentMoves(position, all_available):
            # print("Priority {}".format(priority))
            return {
            'move': list(possible_moves.keys())[list(possible_moves.values()).index(you["tail"])],
            'taunt': 'RAWR!'
            }

        #Priority 9: Any good critical moves?
        priority += 1
        if self.setIntersection(list(possible_moves.keys()), tail_move) != []:
            # print("Priority {}".format(priority))
            rand = random.choice(self.setIntersection(list(possible_moves.keys()), tail_move))
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }

        #Priority 10: Desperation
        priority += 1
        try:
            rand = random.choice(self.desperation(position, possible_moves, tails, heads))
            # print("Priority {}".format(priority))
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }

        #Priority 11: GG
        except:
            priority += 1
            # print("Priority {}".format(priority))
            rand = random.choice(["up", "down", "left", "right"])
            return {
            'move': rand,
            'taunt': 'RAWR!'
            }


    #################################
    ######### FUNCTIONS #############
    #################################

    #Returns the list union
    def setUnion(self, A, B):
        return list(set(A).union(set(B)))


    #Returns the list intersection
    def setIntersection(self, A, B):
        return list(set(A).intersection(set(B)))
    

    #Returns the list difference
    def setDifference(self, A, B):
        return list(set(A).difference(set(B)))


    # Returns the amount of available space available
    # depending on the direction taken.
    def directionArea(self, position, moves, board, all_available):  

        #creates a dictionary where the directions return
        # the size of free space available.
        d_lengths = {}
        for m in moves:
            if m == "up":
                d = (position[0], position[1] - 1)
            if m == "down":
                d = (position[0], position[1] + 1)
            if m == "left":
                d = (position[0] - 1, position[1])
            if m == "right":
                d = (position[0] + 1, position[1])

            #Initiate recursive fill
            d_lengths[m] = len(self.fill_recursion(all_available, board, d, [], []))

        return d_lengths


    # Executed exclusivly in directionArea() as the recursive portion of fill algorithm. 
    # Operates on first in first out breadth first search.
    def fill_recursion(self, all_available, board, position, unexplored = [], explored = []):

        #All adjacent squares
        moves = []
        moves.append((position[0], position[1] - 1))
        moves.append((position[0], position[1] + 1))
        moves.append((position[0] - 1, position[1]))
        moves.append((position[0] + 1, position[1]))

        #update the explored and unexplored portion
        explored.append(position)
        if position in unexplored:
            unexplored.remove(position)
            
        #add available squares to unexplored
        for i in moves:
            if i not in all_available:
                continue
            if i in explored:
                continue
            if i in unexplored:
                continue
            unexplored.append(i)
        
        #Recursion as long as there are unexplored squares, repeat
        if unexplored != []:
            try:
                return self.fill_recursion(all_available, board, unexplored[0], unexplored, explored)
            except:
                return explored
        return explored


    # Used to find the direction which would lead to an objective square the fastest
    def breadthFirst(self, all_available, board, position, target):

        #The target location
        if target == []:
            return []

        #variables used in operation
        breath_tree = {}
        breath_tree[position] = {"parent": None, "children": []}
        explored = []
        parents = {}
        temp = []
        count = 0
        p = 0

        #Start the tree
        explored.append(position)
        temp2 = self.adjacentMoves(position, all_available)
        
        #Explore the first nodes
        for x in temp2:
            if x not in explored:
                explored.append(x)
                breath_tree[position]["children"].append(x)
                breath_tree[x] = {"parent": position, "children": []}

        #Explore the rest of the tree
        while (target not in list(breath_tree.keys())):
            for x in breath_tree:
                if breath_tree[x]["children"] == []:
                    temp2 = self.adjacentMoves(x, all_available)
                    for y in temp2:
                        if y not in explored:
                            explored.append(y)
                            breath_tree[x]["children"].append(y)
                            temp.append(y)
                            parents[y] = x
            for i in temp:
                breath_tree[i] = {"parent": parents[i], "children": []}
            count += 1
            if count == board["width"] * board["height"]:
                return []

        #Climb tree to find best move
        temp = target
        while p != position:
            # print(temp)
            p = breath_tree[temp]["parent"]
            if p == position:
                break
            temp = breath_tree[temp]["parent"]

        #Returns the next closest postiion to food
        a = []
        a.append(temp)
        return a
        

    #Takes direction_area, returns inverse dictionary with index
    def think(self, da):
        nda = {}
        for k in da:
            try:
                nda[da[k]].append(k)
            except:
                nda[da[k]] = [k]

        index = list(nda.keys())
        index.sort(reverse = True)

        return nda, index


    #Returns a dictionary of moves to adjacent positions
    def possibleMoves(self, position, all_available):
        possible_moves = {
            "right": (position[0] + 1, position[1]),
            "left": (position[0] - 1, position[1]),
            "down": (position[0], position[1] + 1),
            "up": (position[0], position[1] - 1),
        }

        temp = []
        for key in possible_moves:
            if possible_moves[key] not in all_available:
                temp.append(key)
        for key in temp:
            del possible_moves[key]
        return possible_moves


    #Returns a dictionary of adjacent postitions to moves
    def InversePossibleMoves(self, position, all_available):
        inverse_possible_moves = {
            (position[0] + 1, position[1]): "right",
            (position[0] - 1, position[1]): "left" ,
            (position[0], position[1] + 1): "down" ,
            (position[0], position[1] - 1): "up",
        }
        
        temp = []
        for key in inverse_possible_moves:
            if key not in all_available:
                temp.append(key)
        for key in temp:
            del inverse_possible_moves[key]
        return inverse_possible_moves


    #Converts position list to string list
    def positionToString(self, inverse_possible_moves, position_list):
        string_list = []
        for x in position_list:
            string_list.append(inverse_possible_moves[x])
        return string_list


    #A last resort for survival, crashes snake into tails, or else heads
    def desperation(self, position, possible_moves, tails, heads):
        move_t = []
        move_h = []

        if possible_moves != {}:
            return list(possible_moves.keys())

        #Crash into tail if possible
        if (position[0] + 1, position[1]) in tails:
            move_t.append("right")
        if (position[0] - 1, position[1]) in tails:
            move_t.append("left")
        if (position[0], position[1] - 1) in tails:
            move_t.append("up")
        if (position[0], position[1] + 1) in tails:
            move_t.append("down")          
        if move_t != []:
            return move_t

        #otherwise crash into head
        if (position[0] + 1, position[1]) in heads:
            move_h.append("right")
        if (position[0] - 1, position[1]) in heads:
            move_h.append("left")
        if (position[0], position[1] - 1) in heads:
            move_h.append("up")
        if (position[0], position[1] + 1) in heads:
            move_h.append("down") 
        if move_h != []:
            return move_h


    #These can be game ending moves, they are represent head-to-head with a larger snake
    def criticalMoves(self, position, board, snakes, bigger_snakes):
        critical_moves = []
        for snake in snakes:
            if snake["name"] in bigger_snakes:
                enemy_head = (snake['body'][0]['x'], snake['body'][0]['y'])
                
                if enemy_head == (position[0], position[1] - 2):
                    critical_moves.append("up")
                if enemy_head == (position[0], position[1] + 2):
                    critical_moves.append("down")
                if enemy_head == (position[0] - 2, position[1]):
                    critical_moves.append("left")
                if enemy_head == (position[0] + 2, position[1]):
                    critical_moves.append("right")

                if enemy_head == (position[0] + 1, position[1] + 1):
                    critical_moves.append("down")
                    critical_moves.append("right")
                if enemy_head == (position[0] - 1, position[1] + 1):
                    critical_moves.append("down")
                    critical_moves.append("left")
                if enemy_head == (position[0] - 1, position[1] - 1):
                    critical_moves.append("left")
                    critical_moves.append("up")
                if enemy_head == (position[0] + 1, position[1] - 1):
                    critical_moves.append("up")
                    critical_moves.append("right")

        return list(set(critical_moves))


    #Returns moves which could kill smaller snakes.
    def attackMoves(self, position, board, snakes, bigger_snakes):
        attack_moves = []
        for snake in snakes:
            if snake["name"] not in bigger_snakes:
                enemy_head = (snake['body'][0]['x'], snake['body'][0]['y'])
                
                if enemy_head == (position[0], position[1] - 2):
                    attack_moves.append("up")
                if enemy_head == (position[0], position[1] + 2):
                    attack_moves.append("down")
                if enemy_head == (position[0] - 2, position[1]):
                    attack_moves.append("left")
                if enemy_head == (position[0] + 2, position[1]):
                    attack_moves.append("right")

                if enemy_head == (position[0] + 1, position[1] + 1):
                    attack_moves.append("down")
                    attack_moves.append("right")
                if enemy_head == (position[0] - 1, position[1] + 1):
                    attack_moves.append("down")
                    attack_moves.append("left")
                if enemy_head == (position[0] - 1, position[1] - 1):
                    attack_moves.append("left")
                    attack_moves.append("up")
                if enemy_head == (position[0] + 1, position[1] - 1):
                    attack_moves.append("up")
                    attack_moves.append("right")

        return list(set(attack_moves))


    #Returns multiple move lists based on how many adjacent moves that move has
    def safeMoves(self, position, inverse_possible_moves, all_available):
        safe_moves = []
        limiting_moves = []
        restricted_moves = []
        dead_ends = []

        adjacent_moves = self.adjacentMoves(position, all_available)

        for am in adjacent_moves:
            if len(self.adjacentMoves(am, all_available)) == 3:
                safe_moves.append(am)
            if len(self.adjacentMoves(am, all_available)) == 2:
                limiting_moves.append(am)
            if len(self.adjacentMoves(am, all_available)) == 1:
                restricted_moves.append(am)        
            if len(self.adjacentMoves(am, all_available)) == 0:
                dead_ends.append(am)   

        #converts positions into direction strings
        safe_moves_str = self.positionToString(inverse_possible_moves, safe_moves)
        limiting_moves_str = self.positionToString(inverse_possible_moves, limiting_moves)
        restricted_moves_str = self.positionToString(inverse_possible_moves, restricted_moves)
        dead_ends_str = self.positionToString(inverse_possible_moves, dead_ends)

        return safe_moves_str, limiting_moves_str, restricted_moves_str, dead_ends_str


    #returns all the positions that are available
    def adjacentMoves(self, position, all_available):
        adjacent_moves = []

        if (position[0] + 1, position[1]) in all_available:
            adjacent_moves.append((position[0] + 1, position[1]))
        if (position[0] - 1, position[1]) in all_available:
            adjacent_moves.append((position[0] - 1, position[1]))
        if (position[0], position[1] + 1) in all_available:
            adjacent_moves.append((position[0], position[1] + 1))
        if (position[0], position[1] - 1) in all_available:
            adjacent_moves.append((position[0], position[1] - 1))                
        
        return adjacent_moves


    #Generates all available nodes from board
    def allAvailableSpace(self, board):
        all_available = []
        for i in range(0, board["height"]):
            for j in range(0, board["width"]):
                all_available.append((i,j))

        #removes obstacles for fill
        for snake in board["snakes"]:
            for body in snake["body"]:
                if (body['x'], body['y']) in all_available:
                    del all_available[all_available.index((body['x'], body['y']))]

        return all_available


    #takes the possible moves and returns the available adjacent spaces.
    def obstacles(self, position, moves, board):

        #removes walls
        if (position[0] - 1 <= 0): # 0 -> 1
            moves.remove("left")
        if (position[0] + 1 >= board['width']):
            moves.remove("right")
        if (position[1] - 1 <= 0): # 0 -> 1
            moves.remove("up")
        if (position[1] + 1 >= board['height']):
            moves.remove("down")

        #removes the adjacent snake body obstacles
        for snake in board["snakes"]:
            for body in snake["body"]:
                try:
                    if body == (position[0] - 1, position[1]):
                        moves.remove("left")
                    if body == (position[0] + 1, position[1]):
                        moves.remove("right")
                    if body == (position[0], position[1] - 1):
                        moves.remove("up")
                    if body == (position[0], position[1] + 1):
                        moves.remove("down")
                except:
                    pass

        return moves


    #find the closest food
    def closestFood(self, you, board):
        closest_food = {}
        temp = []
        if board["food"] == []:
            return temp

        distance_to_food = board['height']*2
        for i in board["food"]:
            temp = abs(i["x"] - you["head"][0]) + abs(i["y"] - you["head"][1])
            if temp < distance_to_food:
                #New closest food
                distance_to_food = temp
                closest_food = i
        temp = (closest_food['x'], closest_food['y'])
        return temp


    #Finds best move(s) for moving towards food. 
    #Doesn't account for snake made walls.
    def foodMove(self, position, closest_food):
        food_move = []

        if closest_food != []:
            #left and right
            if position[0] < closest_food[0]:
                food_move.append("right")
            if position[0] > closest_food[0]:
                food_move.append("left")
            if position[1] > closest_food[1]:
                food_move.append("up")
            if position[1] < closest_food[1]:
                food_move.append("down")
        
        return food_move


    #find the closest enemy
    def closestEnemy(self, position, snakes, our_name):
        closest_enemy = None
        dist_to_enemy = 999
        for snake in snakes:
            if snake["name"] == our_name: continue
            enemy_head = (snake['body'][0]['x'], snake['body'][0]['y'])
            temp = abs(enemy_head[0] - position[0]) + abs(enemy_head[1] - position[1])
            if temp < dist_to_enemy:
                dist_to_enemy = temp
                closest_enemy = enemy_head
        return closest_enemy


    #Leans snake away from enemy
    def leanEnemy(self, position, closest_enemy):
        lean_enemy = []

        if closest_enemy != ():
            #lean based on enemy position
            if position[0] < closest_enemy[0]:
                lean_enemy.append("left")
            if position[0] > closest_enemy[0]:
                lean_enemy.append("right")
            if position[1] > closest_enemy[1]:
                lean_enemy.append("down")
            if position[1] < closest_enemy[1]:
                lean_enemy.append("up")
        
        return lean_enemy


    #Leans snake toward enemy head 
    def attackSnake(self, position, snakes, bigger_snakes, closest_enemy):
        attack_moves = []
        for snake in snakes:
            if snake["name"] not in bigger_snakes:
                enemy_head = (snake['body'][0]['x'], snake['body'][0]['y'])
                if enemy_head == closest_enemy:
                    if position[0] < closest_enemy[0]:
                        attack_moves.append("right")
                    if position[0] > closest_enemy[0]:
                        attack_moves.append("left")
                    if position[1] > closest_enemy[1]:
                        attack_moves.append("up")
                    if position[1] < closest_enemy[1]:
                        attack_moves.append("down")

        return list(set(attack_moves))


    #Leans snake towards tail
    def leanTail(self, position, tail):
        lean_tail = []

        #lean based on enemy position
        if position[0] < tail[0]:
            lean_tail.append("right")
        if position[0] > tail[0]:
            lean_tail.append("left")
        if position[1] > tail[1]:
            lean_tail.append("up")
        if position[1] < tail[1]:
            lean_tail.append("down")
        
        return lean_tail


    #Leans snake towards board centre
    def leanBoard(self, position, board):
        lean_board = []

        #lean based on board position
        if position[1] <= board["height"] / 2:
            lean_board.append("down")
        if position[1] > board["height"] / 2:
            lean_board.append("up")
        if position[0] <= board["width"] / 2:
            lean_board.append("right")
        if position[0] > board["width"] / 2:
            lean_board.append("left")
        
        return lean_board


    #Returns a list of all board edges
    def excludeEdges(self, position, board):
        exclude_edges = []

        if position[1] >= board["height"] - 2:
            exclude_edges.append("down")
        if position[1] <= 2:
            exclude_edges.append("up")
        if position[0] >= board["width"] - 2:
            exclude_edges.append("right")
        if position[0] <= 2:
            exclude_edges.append("left")

        return exclude_edges


    #Returns a list of all board corners
    def allCorners(self, board):
        corners = [(0,0), (0, board["height"]-1), (0, board["width"]-1), (board["height"]-1, board["width"]-1)]
        return corners


    ##############################
    ##### INCLUDED METHOD ########
    ##############################

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def end(self):
        # This function is called when a game your snake was in ends.
        # It's purely for informational purposes, you don't have to make any decisions here.
        data = cherrypy.request.json
        print("END")
        return "ok"


#####################################
##### INCLUDED MAIN FUNCTION ########
#####################################

if __name__ == "__main__":
    server = Battlesnake()
    cherrypy.config.update({"server.socket_host": "0.0.0.0"})
    cherrypy.config.update(
        {"server.socket_port": int(os.environ.get("PORT", "8080")),}
    )
    print("Starting Battlesnake Server...")
    cherrypy.quickstart(server)
