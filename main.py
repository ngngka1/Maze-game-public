import pygame as pg
import pygame.camera as pgcam
import dfs
import toml
import sys
import json
import Astar_search as astar
import winsound
import os

class Game:
    def __init__(self, level=1, difficulty = "easy") -> None:
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Maze minigame")
        self.level = None
        self.current_activated_UI_stack: list[UI] = []
        self.difficulty = difficulty
        self.hint_activated = False
        self.hint_paths = None
        self.bgm_track_index = 0
        self.chosen_theme_index = 0 # white theme by default
          
    def get_level_properties(self, level = 1) -> None:
        global time_elapsed
        self.level = level
        level_prop = toml.load("level_properties.toml")
        
        # Map property
        map_size = level_prop[str(self.level)]["map_size"] # how many grids will be in the level
        width_to_height_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        main_col = int((map_size / (1 / width_to_height_ratio)) ** (1 / 2)) # w * (height-width ratio) * w = map.size -> w^2 * h/w = map.size -> w = (map.size / (h/w))^0.5
        main_row = int((map_size / width_to_height_ratio) ** (1 / 2)) # h * (width-height ratio) * h = map.size
        game_col = main_col + 1 + main_col % 2 # if there is even number of columns, right side must be wall
        game_row = main_row + 1 + main_row % 2 # if there is even number of rows, bottom must be wall
        grid_width = SCREEN_WIDTH // (game_col)
        grid_height = SCREEN_HEIGHT // (game_row) 
        
        dfs.makemaze(main_col, main_row) 
        with open("maze_map.json", "r") as maze_map_file:
            maze_map_2d = json.load(maze_map_file)
            self.hint_paths = set(astar.Astar_search(maze_map_2d, [1, 1], None, 1))
            maze_map = []
            for i, row in enumerate(maze_map_2d):    # convert the maze from a 2d-array to 1d
                for j, element in enumerate(row):
                    if (i, j) in self.hint_paths and element != 2:
                        maze_map.append(3)
                    else:
                        maze_map.append(element)
                
        self.get_new_game_class_objects(grid_width, grid_height)

        cursor = [0, 0]    
        for i in range(0, len(maze_map)):
            if maze_map[i] == 1: # if is wall
                wall.append_rect(pg.rect.Rect(cursor[0], cursor[1], wall.width, wall.height))
            elif maze_map[i] == 2: # if is goal
                goal.set_goal_rect(pg.rect.Rect(cursor[0], cursor[1], goal.width, goal.height))
            elif maze_map[i] == 3: # if it is the correct path to goal
                background.append_rect(pg.rect.Rect(cursor[0], cursor[1], background.width, background.height))
            if i != 0 and (i + 1) % game_col == 0: 
                cursor[0] = 0
                cursor[1] += grid_height
            else:
                cursor[0] += grid_width
   
    def get_new_game_class_objects(self, grid_width, grid_height) -> None:
        global wall, goal, player, camera, stats, background
        wall = Wall(grid_width, grid_height)
        goal = Goal(grid_width, grid_height)
        background = Hint(grid_width // 2, grid_height // 2)
        player = Player(grid_width / 2, grid_height / 2)
        camera_width = grid_width * 10
        camera_height = (grid_width * 10) // (SCREEN_WIDTH / SCREEN_HEIGHT) # substitution of: camera_width / camera_height = width_height ratio               
        camera = Camera(camera_width, camera_height)
        stats = Stats(self.level)
        
class Player:
    def __init__(self, width, height) -> None:
        self.HP = 10
        self.width = int(width)
        self.height = int(height)
        self.x = width * 2 + 1  # the parameter width and heigth are actually game_obj.grid_width & height divided by 2
        self.y = height * 2 + 1
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
        self.movement_speed = self.width // 3
        self.surface_unscaled = pg.image.load(PATH_TO_SPRITE)
        self.surface_scaled = pg.transform.scale(self.surface_unscaled, (self.width, self.height))
        self.hitbox = pg.Rect(self.x, self.y, self.width, self.height)
        
    def check_movement(self, event) -> None:

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RIGHT:
                self.move_right = True
            elif event.key == pg.K_LEFT:
                self.move_left = True
            if event.key == pg.K_DOWN:
                self.move_down = True
            elif event.key == pg.K_UP:
                self.move_up = True
            
        if event.type == pg.KEYUP:
            if event.key == pg.K_RIGHT:
                self.move_right = False
            if event.key == pg.K_LEFT:
                self.move_left = False
            if event.key == pg.K_DOWN:
                self.move_down = False
            if event.key == pg.K_UP:
                self.move_up = False
    
    def execute_movement(self) -> None:
        if not (self.move_up or self.move_down or self.move_left or self.move_right):
            return
        target_x = self.x
        target_y = self.y
        if self.move_up:
            target_y -= self.movement_speed
        if self.move_down:
            target_y += self.movement_speed
        if self.move_left:
            target_x -= self.movement_speed
        if self.move_right:
            target_x += self.movement_speed
            

        if target_x != self.x:
            self.hitbox.x = target_x
            for rect in wall.grid_rect_list:
                if self.hitbox.colliderect(rect):
                    self.hitbox.x = self.x
                    # if rect.x - self.width >= self.x:
                    #     self.hitbox.x = self.x + (rect.x - (self.x + self.width)) - 2
                    # else:
                    #     self.hitbox.x = self.x - (self.x - (rect.x + rect.width)) + 2
                    
            
        if target_y != self.y:
            self.hitbox.y = target_y
            for rect in wall.grid_rect_list:
                if self.hitbox.colliderect(rect):
                    self.hitbox.y = self.y
                    # if rect.y - self.height >= self.y:
                    #     self.hitbox.y = self.y + (rect.y - self.height - self.y) - 2
                    # else:
                    #     self.hitbox.y = self.y - (self.y - (rect.y + rect.height)) + 2

        self.x = self.hitbox.x
        self.y = self.hitbox.y
        
        self.pass_check()
        
        
    def pass_check(self):
        if self.hitbox.colliderect(goal.grid_rect):
            game_obj.get_level_properties(game_obj.level + 1)
            
    def freeze(self):
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
   
class Camera:
    def __init__(self, width, height) -> None:
        self.object = pgcam.Camera(pgcam.list_cameras()[0])
        self.width = width
        self.height = height
        self.surface = pg.Surface((self.width, self.height))
        self.x = player.x - self.width // 2
        self.y = player.y - self.height // 2
        
    def update(self) -> None:
        self.x = player.x - self.width // 2
        self.y = player.y - self.height // 2
        self.surface.fill(THEMES[game_obj.chosen_theme_index])
        self.surface.blit(game_obj.screen, (0, 0), (self.x, self.y, self.width, self.height))
        game_obj.screen.blit(pg.transform.scale(self.surface, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
      
class UI:
    def __init__(self, UI_name: str) -> None:
        self.UI_name = UI_name
        self.activated = False
        self.chosen_index = 0
        self.text_box_color_unchosen = (100, 100, 100)
        self.text_box_color_chosen = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.text_box = {}
        self.options_functions = []
        self.total_option = len(UIs["UI"][self.UI_name]["options"])
        self.get_options()
    
    def get_options(self):
        for i, option_name in enumerate(UIs["UI"][self.UI_name]["options"]):
            self.options_functions.append(UIs["function"][option_name])
            text_surface = FONT.render(option_name, True, self.text_color)
            text_rect = text_surface.get_rect()
            text_rects_distance = text_rect.height + 20 # There is a distance of 20 pixel between each rects
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - text_rects_distance * ((self.total_option // 2) - i))
            self.text_box[option_name] = {
                        "text_surface": text_surface,
                        "rect": text_rect
                    }
        
    def check_action(self, event):  # check if user changed action
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE and game_obj.current_activated_UI_stack[-1].UI_name != "main_menu":
                UI_return()
            elif event.key == pg.K_RETURN:
                self.execute_action(self.chosen_index)
            elif event.key == pg.K_UP:
                self.chosen_index -= 1
            elif event.key == pg.K_DOWN:
                self.chosen_index += 1
            self.chosen_index = max(0, self.chosen_index % self.total_option)
                
    def execute_action(self, i): # execute chosen action
        if type(self.options_functions[i]) == list:
            for function_str in self.options_functions[i]: # Used a for loop here for options that do multiple actions
                globals()[function_str]()
        else:
            globals()[self.options_functions[i]]()
             
    def update_UI(self) -> None:
        for i, option_name in enumerate(self.text_box):
            if i == self.chosen_index:
                pg.draw.rect(game_obj.screen, self.text_box_color_chosen, self.text_box[option_name]["rect"])
            else:
                pg.draw.rect(game_obj.screen, self.text_box_color_unchosen, self.text_box[option_name]["rect"], 0, 3)
            game_obj.screen.blit(self.text_box[option_name]["text_surface"], self.text_box[option_name]["rect"])
      
class Stats:
    def __init__(self, current_level, time_elapsed = 0):
        self.display = True
        self.level_display_surface = FONT.render(f"Current level: {current_level}", True, (0, 0, 0))
        self.level_display_rect = self.level_display_surface.get_rect(center = ((camera.x + SCREEN_WIDTH // 2) // 2, (camera.y + SCREEN_HEIGHT // 2) // 2 + 80))
        self.time_elapsed = time_elapsed
        self.time_display_surface = FONT.render(f"Time used: {time_elapsed:.3f}", True, (0, 0, 0))
        self.time_display_rect = self.time_display_surface.get_rect(center = ((camera.x + SCREEN_WIDTH // 2) // 2, (camera.y + SCREEN_HEIGHT // 2) // 2))
        
    def update_stats_overlay(self):
        self.time_elapsed = time_elapsed
        pg.draw.rect(game_obj.screen, (255, 255, 0), self.level_display_rect)
        game_obj.screen.blit(self.level_display_surface, self.level_display_rect)
        
        pg.draw.rect(game_obj.screen, (255, 255, 0), self.time_display_rect)
        self.time_display_surface = FONT.render(f"Time used: {self.time_elapsed}", True, (0, 0, 0))
        game_obj.screen.blit(self.time_display_surface, self.time_display_rect)
                  
class Rect_objects:
    def __init__(self, width, height) -> None:
        self.width = width
        self.height = height
        
class Wall(Rect_objects):
    def __init__(self, width, height) -> None:
        super().__init__(width, height)
        self.grid_rect_list = []
        self.color = (0, 0, 0)
        
    def append_rect(self, rect: pg.Rect) -> None:
        self.grid_rect_list.append(rect)
              
class Goal(Rect_objects):
    def __init__(self, width, height) -> None:
        super().__init__(width, height)
        self.grid_rect = None
        self.color = (0, 0, 255)
        
    def set_goal_rect(self, rect: pg.Rect) -> None:
        self.grid_rect = rect
        
class Hint(Rect_objects):
    def __init__(self, width, height) -> None:
        super().__init__(width, height)
        self.grid_rect_list = []
        self.color = (255, 0, 25)
        
    def append_rect(self, rect: pg.Rect) -> None:
        rect.center = (rect.x + self.width, rect.y + self.height)
        self.grid_rect_list.append(rect)
        

class Monster:
    def __init__(self, width, height, HP):
        self.width = width
        self.height = height
        self.HP = HP
      
def change_bgm():
    game_obj.bgm_track_index = game_obj.current_activated_UI_stack[-1].chosen_index
    pg.mixer.music.load(BGM[game_obj.bgm_track_index])
    pg.mixer.music.play()
  
def switch_hint():
    game_obj.hint_activated ^= 1
        
def draw_screen() -> None:
    if game_obj.current_activated_UI_stack:
        if game_obj.current_activated_UI_stack[0].UI_name == "main_menu":
            game_obj.screen.fill(THEMES[game_obj.chosen_theme_index])
        pg.draw.rect(game_obj.screen, (0, 0, 255), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, 40)
        game_obj.current_activated_UI_stack[-1].update_UI()
    else:
        game_obj.screen.fill(THEMES[game_obj.chosen_theme_index])

        draw_game_grid()
        
        camera.update()
        
        stats.update_stats_overlay()
    
    pg.display.update()
        
def draw_game_grid() -> None:
    for rectObj in wall.grid_rect_list:
        pg.draw.rect(game_obj.screen, wall.color, rectObj, 10)
    pg.draw.rect(game_obj.screen, goal.color, goal.grid_rect)
    
    if game_obj.hint_activated:
        for path_hint_rect in background.grid_rect_list:
            pg.draw.rect(game_obj.screen, background.color, path_hint_rect, 0, 5)
            
    
    game_obj.screen.blit(player.surface_scaled, (player.x, player.y))
    
def switch_UI(UI_object = None): 
    if not UI_object: # UIreturn
        game_obj.current_activated_UI_stack.pop().activated ^= 1
    else: # UIopen
        game_obj.current_activated_UI_stack.append(UI_object)
        UI_object.activated ^= 1

def UI_return(): # return to the previous UI
    switch_UI()
    
def UI_open(new_UI = None): # if no argument passed: opens the UI that is chosen; If with argument passed: opens the specified UI by getting the UI object with its name
    if not new_UI:
        current_UI = game_obj.current_activated_UI_stack[-1]
        new_UI = get_UI_object(UIs["UI"][current_UI.UI_name]["options"][current_UI.chosen_index]) # in toml file, the 1st letter of the UI's option is capitalized, so i just put lower() here to avoid key errors
    switch_UI(new_UI)
    
def get_UI_object(UI_object_name): # just a function to improve the readability of the program
    return UIs["UI"][UI_object_name.lower().replace(' ', '_')]["object"]

def UI_return_ultimate():
    current_UI = game_obj.current_activated_UI_stack[-1]
    for i in range(len(game_obj.current_activated_UI_stack)):
        game_obj.current_activated_UI_stack[i].activated ^= 1
        
    game_obj.current_activated_UI_stack = []
    
    if current_UI.UI_name == "return_main_menu": ## Note: if this function is called in the return_main_menu UI, 
        # it means the player confirmed to return to main menu; While if this function is not called from return_main_menu_UI,
        # it can just be other options using ultimate UI return function
        game_obj.screen.fill(THEMES[game_obj.chosen_theme_index])
        game_obj.current_activated_UI_stack.append(get_UI_object("main_menu"))
   
def new_game():
    game_obj.get_level_properties()
    switch_UI()

def exit_game(): # exit game
    pg.quit()
    sys.exit()

def change_theme():
    game_obj.chosen_theme_index ^= 1
    

def main():
    global time_elapsed
    clock = pg.time.Clock()
    time_elapsed = 0.00000
    total_paused_time = 0
    pause_start_time = 0
    running = True
    while running:
        clock.tick(FPS)
        if game_obj.current_activated_UI_stack:
            if pause_start_time == 0:
                pause_start_time = pg.time.get_ticks()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                exit_game()
            if event.type == pg.KEYDOWN:
                if game_obj.current_activated_UI_stack: # if UI is turned on
                    game_obj.current_activated_UI_stack[-1].check_action(event)
                else:
                    if event.key == pg.K_ESCAPE:
                        UI_open(get_UI_object("menu")) # turn on menu UI when it's currently in the main game
                        player.freeze() # freeze is needed as sprite.check_movement stops the sprite only when it detects KEYUP
                             
                    if pause_start_time != 0:
                        total_paused_time += pg.time.get_ticks() - pause_start_time
                        pause_start_time = 0
            
        if not game_obj.current_activated_UI_stack:
            player.check_movement(event)
            player.execute_movement()
        
        time_elapsed = (pg.time.get_ticks() - total_paused_time) / 1000.0
        draw_screen()
                   
def init_game() -> None:
    global game_obj
    game_obj = Game()

def init_UI():
    for UI_name in UIs["UI"]:
        UIs["UI"][UI_name]["object"] = UI(UI_name)
        
def init_config() -> None:
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, PATH_TO_SPRITE, PLAYER_HP, THEMES, FONT_FILE_PATH, FONT, UIs, BGM
    config = toml.load("config.toml")
    # Main game
    FPS = config["fps"]
    SCREEN_WIDTH = config["screen_width"]
    SCREEN_HEIGHT = config["screen_height"]
    THEMES = config["themes"]
    # Player
    PATH_TO_SPRITE = config["player"]["path"]
    PLAYER_HP = config["player"]["HP"]
    # Font
    pg.font.init()
    FONT_FILE_PATH = config["font"]["path"]
    FONT = pg.font.Font(FONT_FILE_PATH, 50) 
    # UIs
    with open("UI_options.json", "r") as UI_options_file:
        UIs = json.load(UI_options_file)
    # BGMs
    BGM = config["bgm"]["paths"]
    
    

if __name__ == "__main__":
    pg.init()
    pgcam.init()
    init_config()
    init_game()
    init_UI()
    game_obj.current_activated_UI_stack = [get_UI_object("main_menu")]
    change_bgm()
    main()