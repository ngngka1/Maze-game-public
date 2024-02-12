import dfs

ALGORITHMS = {
    "dfs": dfs.generate_maze,
    "": None
}

def generate_map(maze_width, maze_height, maze_generation_algorithm, item_appearance_rate):
    ALGORITHMS[maze_generation_algorithm](maze_width, maze_height, item_appearance_rate)