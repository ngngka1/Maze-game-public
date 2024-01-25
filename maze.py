import itertools
import random
import json

def makemaze(maze_width: int, maze_height: int):

    global maze, goal_set
    goal_set = False # a flag that shows if the goal position is generated yet
    maze = []
    for row_num in range(maze_height):
        temp = []
        for col_num in range(maze_width):
            temp.append(1)
        maze.append(temp)
            
    max_path_sum = maze_generation(0, 0, maze, maze_width, maze_height)
    goal_generation(0, 0, maze, maze_width, maze_height, 0, max_path_sum)
    
    temp = []
    for i in range(0, maze_width + 1 + maze_width % 2):
        temp.append(1)
    print("length of row wall: ", len(temp))
        
    if maze_height % 2 == 1: # if the height of the maze was even, the last row will always not be visited and be 1, so no need wall appended
        maze.append(temp)
        maze.insert(0, temp)
    else:
        maze[-1] = temp
        maze.insert(0, temp)

    if maze_width % 2 == 1: # vice versa
        for i, row in enumerate(maze): # adding the wall surround the maze map
            if i != 0 and i != len(maze) - 1:
                maze[i].insert(0, 1)
                maze[i].append(1)
    else:
        for i, row in enumerate(maze): # adding the wall surround the maze map
            if i != 0 and i != len(maze) - 1:
                maze[i].insert(0, 1)
            
        
    
    with open("maze_map.json", "w") as maze_map_file:
        json.dump(maze, maze_map_file)
        
    return max_path_sum
    
def maze_generation(row_num, col_num, maze, map_width, map_height, path_sum=0) -> int: # return the maximum pathsum as well
    possible_path = []
    if row_num + 2 < map_height and maze[row_num + 2][col_num] == 1: # if can go down and unmaze
        possible_path.append((row_num + 2, col_num))
    if row_num - 2 >= 0 and maze[row_num - 2][col_num] == 1: # go up
        possible_path.append((row_num - 2, col_num))
    if col_num + 2 < map_width and maze[row_num][col_num + 2] == 1: # go right
        possible_path.append((row_num, col_num + 2))
    if col_num - 2 >= 0 and maze[row_num][col_num - 2] == 1: # go left
        possible_path.append((row_num, col_num - 2))
        
    max_path_sum = 0
    while possible_path:
        movable_pos = possible_path.pop(random.randint(0, len(possible_path) - 1))
        if maze[movable_pos[0]][movable_pos[1]] == 1: # check again to ensure it is not walked afterwards
            maze[row_num][col_num] = 0
            maze[(movable_pos[0] + row_num) // 2][(movable_pos[1] + col_num) // 2] = 0
            maze[movable_pos[0]][movable_pos[1]] = 0
            chosen_path_sum = maze_generation(movable_pos[0], movable_pos[1], maze, map_width, map_height, 2)
        max_path_sum = max(max_path_sum, chosen_path_sum)
    
    return path_sum + max_path_sum

def goal_generation(row_num, col_num, maze, map_width, map_height, curr_path_sum, max_path_sum):
    global goal_set
    if goal_set:
        return
    possible_path = []
    if row_num + 1 < map_height and maze[row_num + 1][col_num] == 0:
        possible_path.append((row_num + 1, col_num))
    if row_num - 1 >= 0 and maze[row_num - 1][col_num] == 0:
        possible_path.append((row_num - 1, col_num))
    if col_num + 1 < map_width and maze[row_num + 1][col_num] == 0:
        possible_path.append((row_num, col_num + 1))
    if col_num - 1 >= 0 and maze[row_num - 1][col_num] == 0:
        possible_path.append((row_num, col_num - 1))
        
    if not possible_path and curr_path_sum >= 0.01 * max_path_sum:
        maze[row_num][col_num] = 20
        goal_set = True
        return 
    else:
        while possible_path:
            movable_pos = possible_path.pop(random.randint(0, len(possible_path) - 1))
            if maze[movable_pos[0]][movable_pos[1]] == 0: # check again to ensure it is not walked afterwards
                print("curr path: ", curr_path_sum)
                goal_generation(movable_pos[0], movable_pos[1], maze, map_width, map_height, 1 + curr_path_sum, max_path_sum)
        
    
print(makemaze(20, 20))
for row in maze:
    print(" ".join(map(str, row)))
