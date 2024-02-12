import random
import json

def generate_maze(maze_width: int, maze_height: int, item_appearance_rate):
    """generate maze with dfs algorithm

    Args:
        maze_width (int): width of the maze (number of columns)
        maze_height (int): height of the maze (number of rows)

    Returns:
        _type_: list of list containing 0, 1, 2, 3, in which:
        0: walkable path,
        1: wall,
        2: goal,
        3: mysterious items
    """

    goal = {
        "coordinate": (0, 0),
        "path_sum": 0
    } # stores the coordinate of the goal as well as its path sum
    maze = []
    
    for _ in range(maze_height):    
        maze.append(list(map(int, list("1" * maze_width))))
            
    max_path_sum = dfs(maze, goal, 1, 1, maze_width, maze_height, item_appearance_rate)
    maze[goal["coordinate"][0]][goal["coordinate"][1]] = 2
    
    with open("maze_map.json", "w") as maze_map_file:
        json.dump(maze, maze_map_file)
        
    return max_path_sum
    
def dfs(maze, goal, row_num, column_num, map_width, map_height, item_appearance_rate, curr_path_sum=0, path_sum=0) -> int: # return the maximum pathsum as well
    possible_path = []
    if row_num + 2 < map_height - 1 and maze[row_num + 2][column_num] == 1: # if can go down and unmaze
        possible_path.append((row_num + 2, column_num))
    if row_num - 2 > 0 and maze[row_num - 2][column_num] == 1: # go up
        possible_path.append((row_num - 2, column_num))
    if column_num + 2 < map_width - 1 and maze[row_num][column_num + 2] == 1: # go right
        possible_path.append((row_num, column_num + 2))
    if column_num - 2 > 0 and maze[row_num][column_num - 2] == 1: # go left
        possible_path.append((row_num, column_num - 2))
        
    max_path_sum = 0
    while possible_path:
        movable_pos = possible_path.pop(random.randint(0, len(possible_path) - 1))
        if maze[movable_pos[0]][movable_pos[1]] == 1: # check again to ensure it is not walked afterwards
            maze[row_num][column_num] = 0
            maze[(movable_pos[0] + row_num) // 2][(movable_pos[1] + column_num) // 2] = 0
            maze[movable_pos[0]][movable_pos[1]] = 0
            chosen_path_sum = dfs(maze, goal, movable_pos[0], movable_pos[1], map_width, map_height, item_appearance_rate, 2 + curr_path_sum, 2)
        max_path_sum = max(max_path_sum, chosen_path_sum)
        
    if curr_path_sum > goal["path_sum"]:
        goal["coordinate"] = (row_num, column_num)
        goal["path_sum"] = curr_path_sum
    elif random.random() < item_appearance_rate and max_path_sum == 0:
        maze[row_num][column_num] = 3
        
    
    return path_sum + max_path_sum
 
####### for testing  
# print(makemaze(20, 20))
# for row in maze:
#     print(" ".join(map(str, row)))
