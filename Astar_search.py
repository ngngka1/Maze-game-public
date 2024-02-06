# This program aims to find the shortest path to the goal with provided map and start position. To use it, run:
# Astar_search(map, start position)
# The function returns a stack by default which is the path to the goal.
# For more details, please refer to the documentation of the function.


import json
import pygame as pg
import sys
from typing import Sequence

DEFAULT_POSSIBLE_MOVES = {
    # With Diagonal moves
    0: {
        (-1, -1), # top left
        (0, -1), # top
        (1, -1), # top right
        (-1, 0), # left
        (1, 0), # right
        (-1, 1), # bottom left
        (0, 1), # bottom
        (1, 1) # bottom right
    },
    
    # Without diagonal moves
    1: {
        (0, -1), # top
        (-1, 0), # left
        (1, 0), # right
        (0, 1), # bottom
    },
}

class Node:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    def __eq__(self, other):
        if isinstance(other, Node):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, tuple):
            return (self.x, self.y) == other
        return False
    def __hash__(self):
        return hash((self.x, self.y))

def Astar_search(grid: list[list[int]], start_node: Node | Sequence, end_node: Node | Sequence = None, possible_moves: int | Sequence = 0, return_node: bool = False) -> list:
    """
    Parameters:\n
    grid: should be a 2d list with int values of (0, 1, 2) only, in which:
        0: Walkable path
        1: Wall
        2: Goal
    \n
    start_node: can be a Node object or simply a Sequence of length 2, 
    which contains the x and y value(or column and row number). For example, [x, y] or [column, row]
    \n
    end_node: optional, same as start_node but for the goal position.
    Will be calculated if argument is not provided or None is passed
    \n
    possible_moves: a Sequence of Sequence of possible moves of size 2, 
    in the format of [move in x-coordinate, move in y-coordinate]. Note that y - 1 refers to moving upwards (e.g. [0, -1])
    When 0 (int) is passed or no arguments are passed: possible moves include horizontal, vertical and diagonal moves.
    When 1 (int) is passed: possible moves include horizontal and vertical moves.
    \n
    return_node: a boolean value to specify return type
    True: return a list of Node objects
    False: return a list of tuples which are the row and column numbers of each path
    """
    
    map_height = len(grid)
    map_width = len(grid[0])
    if type(start_node) != Node:
        start_node = Node(start_node[0], start_node[1])
        
    if end_node:
        if type(end_node) != Node:
            end_node = Node(end_node[0], end_node[1])
    else:
        for i in range(map_height):
            for j in range(map_width):
                if grid[i][j] == 2:
                    end_node = Node(j, i)
                    break
                
    if possible_moves:
        if type(possible_moves) == int:
            if 0 <= possible_moves < 2:
                possible_moves = DEFAULT_POSSIBLE_MOVES[possible_moves]
            else:
                print("Invalid key to specify default possible moves")
                return None
    else:
        possible_moves = DEFAULT_POSSIBLE_MOVES[0]
    

    
    opened = {start_node,}
    closed = set([]) # refers to node which has been expanded
    
    parent = {}
    parent[start_node] = None
    
    g = {}
    g[start_node] = 0
    
    h = {}
    h[start_node] = Euclidean(start_node, end_node)
    
    f = {}
    f[start_node] = g[start_node] + h[start_node]
    
    while opened:
        current_node = None
        for node in opened:
            if current_node is None or (f[node] < f[current_node]):
                current_node = node
        
        opened.remove(current_node)
        closed.add(current_node)
        
        if end_node == current_node:
            break
        
        adjacent_nodes = get_adjacent_nodes(grid, map_height, map_width, current_node, possible_moves)
        for node in adjacent_nodes:
            if node in closed:
                continue
            node_g = g[current_node] + Euclidean(current_node, node)
            node_h = Euclidean(node, end_node)
            node_f = node_g + node_h
            if node not in opened or node_g < g[node]:
                g[node] = node_g
                h[node] = node_h
                f[node] = node_f
                opened.add(node)
                parent[node] = current_node
    
    if end_node in parent:
        path = []
        previous = end_node
        
        if return_node:
            while previous:
                path.append(previous)
                previous = parent[previous]
        else:
            while previous:
                path.append((previous.y, previous.x))
                previous = parent[previous]
        
        return path
    else:
        return None
         
def Euclidean(start_node: Node, end_node: Node) -> int:
    # Euclidean formula
    return int(((start_node.x - end_node.x) ** 2 + (start_node.y - end_node.y) ** 2) ** (0.5))

def get_adjacent_nodes(grid: list, map_height: int, map_width: int, start_node: Node, possible_moves: set | list) -> list:
    movable_nodes = []
    for move in possible_moves:
        target_node = Node(start_node.x + move[0], start_node.y + move[1])
        if can_move(grid, map_height, map_width, target_node):
            movable_nodes.append(target_node)
    return movable_nodes
    
def can_move(grid: list, map_height: int, map_width: int, target_node: Node) -> bool:
    return (0 <= target_node.x < map_width) and \
        (0 <= target_node.y < map_height) and \
        grid[target_node.y][target_node.x] != 1

def demonstration(grid: list, path: list):
    map_height = len(grid)
    map_width = len(grid[0])
    
    if not path:
        print("No path")
        return
    else:
        while path:
            grid_rect = path.pop()
            if grid[grid_rect[0]][grid_rect[1]] != 2:
                grid[grid_rect[0]][grid_rect[1]] = 3
        
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 700
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    grid_width = SCREEN_WIDTH // (map_width)
    grid_height = SCREEN_HEIGHT // (map_height)
    
    clock = pg.time.Clock()
    while True:
        clock.tick(10)
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
                break
                    
        screen.fill((255, 255, 255))
        cursor = Node(0, 0)
        for row in range(map_height):
            for col in range(map_width):
                if grid[row][col] == 1: #wall
                    pg.draw.rect(screen, (0, 0, 0), (cursor.x, cursor.y, grid_width, grid_height))
                elif grid[row][col] == 2: #goal
                    pg.draw.rect(screen, (0, 0, 255), (cursor.x, cursor.y, grid_width, grid_height))
                elif grid[row][col] == 3: #path
                    path_rect = pg.rect.Rect(cursor.x, cursor.y, grid_width * 0.8, grid_height * 0.8)
                    path_rect.center = (cursor.x + grid_width // 2, cursor.y + grid_height // 2)
                    pg.draw.rect(screen, (255, 0, 20), path_rect, 0, 3)
                cursor.x += grid_width
            cursor.x = 0
            cursor.y += grid_height
        pg.display.flip()
        
def main():
    with open("map.json") as map_file:
        grid = json.load(map_file)
    
    path = Astar_search(grid, [1, 1], None, DEFAULT_POSSIBLE_MOVES[1]) # returns a stack of path
    
    demonstration(grid, path)

    
if __name__ == "__main__":
    pg.init()
    main()