import pygame as pg
import maze
import toml
import sys
import json
import math

class Game:
    def __init__(self, level=1):
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Maze minigame")
        self.level = level
        self.get_level_properties()
        
        
    def get_level_properties(self):
        level_prop = toml.load("level_properties.toml")
        self.map_size = level_prop[str(self.level)]["map_size"] # it refers to how many grids will be in the level
        width_to_height_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        self.main_col = int((self.map_size / (1 / width_to_height_ratio)) ** (1 / 2))# ceil so that it wont take too few row
        self.main_row = int((self.map_size / width_to_height_ratio) ** (1 / 2))
        self.game_col = self.main_col + 1 + self.main_col % 2
        self.game_row = self.main_row + 1 + self.main_row % 2
        self.grid_width = SCREEN_WIDTH / (self.game_col)
        self.grid_height = SCREEN_HEIGHT / (self.game_row) 
        self.grid_rect = pg.rect.Rect(0, 0, self.grid_width, self.grid_height)
        maze.makemaze(int(self.main_col), int(self.main_row)) 
        
        
        with open("maze_map.json", "r+") as maze_map_file:
            self.maze_map = []
            Maze = json.load(maze_map_file)
            for row in Maze:
                self.maze_map += row
        

        

def draw_screen():
    gameObj.screen.fill(bg_color)
    
    draw_game_grid()
    
    pg.display.update()
        
def draw_game_grid():
    print_cursor = [0, 0]
    gameObj.grid_rect.x = 0
    gameObj.grid_rect.y = 0
    if gameObj.maze_map[0] == 1:
            pg.draw.rect(gameObj.screen, (0, 0, 0), gameObj.grid_rect)
    for i in range(1, len(gameObj.maze_map)):
        if i % gameObj.game_col == 0:
            print_cursor[0] = 0
            print_cursor[1] += gameObj.grid_height
        else:
            print_cursor[0] += gameObj.grid_width
        gameObj.grid_rect.x = print_cursor[0]
        gameObj.grid_rect.y = print_cursor[1]
        if gameObj.maze_map[i] == 1:
            pg.draw.rect(gameObj.screen, (0, 0, 0), gameObj.grid_rect)
        elif gameObj.maze_map[i] == 2:
            pg.draw.rect(gameObj.screen, (0, 0, 255), gameObj.grid_rect)
    
    
        
        
    
    

def main():
    running = True
    while running:
        clock = pg.time.Clock()
        clock.tick(FPS)
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                pg.quit()
                sys.exit()
        draw_screen()
                
def init_game():
    global gameObj
    gameObj = Game()
        
def init_config():
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, bg_color, screen
    config = toml.load("config.toml")
    FPS = config["fps"]
    SCREEN_WIDTH = config["screen_width"]
    SCREEN_HEIGHT = config["screen_height"]
    bg_color = config["default_background_color"]
    
    
    
if __name__ == "__main__":
    init_config()
    init_game()
    main()