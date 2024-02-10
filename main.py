import pygame as pg
import pygame.camera as pgcam
import dfs
import toml
import sys
import json
import Astar_search as astar
from typing import Union

class Game:
    instance: Union["Game", None] = None
    def __init__(self) -> None:
        if Game.instance is not None:
            raise Exception("Only 1 game object can be created!")
        Game.instance = self
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Maze minigame")
        self.level = None
        self.current_activated_UI_stack: list[UI] = []
        
        self.difficulty_scale = 1
        self.hint_activated = False
        self.hint_paths = None
        self.bgm_track_index = 0
        self.chosen_theme_index = 0
        self.chosen_sprite_index = 0
          
    def get_level_properties(self, level = 1) -> None:
        global time_elapsed
        self.level = level
        level_prop = toml.load("level_properties.toml")
        
        # Map property
        map_size = level_prop[str(self.level)]["map_size"] * self.difficulty_scale # how many grids will be in the level
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
        
    @staticmethod
    def new_game():
        Game.instance.get_level_properties()
        UI.switch_UI()

    @staticmethod
    def exit_game(): # exit game
        pg.quit()
        sys.exit()
        
    @staticmethod
    def change_difficulty():
        # Difficulty scale for "Easy", "Normal" and "Hard" are 1, 2, 3 respectively
        # indices for "Easy", "Normal" and "Hard" in the setting UI are 0, 1, 2; so adding one to it = difficulty scale
        Game.instance.difficulty_scale = Game.instance.current_activated_UI_stack[-1].chosen_index + 1
        
    @staticmethod
    def switch_hint():
        Game.instance.hint_activated ^= 1
        
    @staticmethod
    def load_bgm():
        pg.mixer.music.load(BGM[Game.instance.bgm_track_index])
        pg.mixer.music.play()
        pg.mixer.music.set_endevent(pg.USEREVENT)
            
    @staticmethod
    def change_bgm():
        Game.instance.bgm_track_index = Game.instance.current_activated_UI_stack[-1].chosen_index
        Game.load_bgm()
        
    @staticmethod
    def change_theme():
        Game.instance.chosen_theme_index ^= 1
        
    @staticmethod
    def change_sprite():
        Game.instance.chosen_sprite_index = (Game.instance.chosen_sprite_index + 1) % len(PATHS_TO_SPRITES)
        
class Player:
    def __init__(self, width, height) -> None:
        self.HP = 10
        self.width = int(width)
        self.height = int(height)
        self.x = width * 2 + 1  # the parameter width and heigth are actually Game.instance.grid_width & height divided by 2
        self.y = height * 2 + 1
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
        self.movement_speed = self.width // 3
        self.surface_unscaled = pg.image.load(PATHS_TO_SPRITES[Game.instance.chosen_sprite_index])
        self.surface_scaled = pg.transform.smoothscale(self.surface_unscaled, (self.width, self.height))
        self.hitbox = pg.Rect(self.x, self.y, self.width, self.height)
        
    def check_movement(self, event) -> None:

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RIGHT or event.key == pg.K_d:
                self.move_right = True
            if event.key == pg.K_LEFT or event.key == pg.K_a:
                self.move_left = True
            if event.key == pg.K_DOWN or event.key == pg.K_s:
                self.move_down = True
            if event.key == pg.K_UP or event.key == pg.K_w:
                self.move_up = True
            
        if event.type == pg.KEYUP:
            if event.key == pg.K_RIGHT or event.key == pg.K_d:
                self.move_right = False
            if event.key == pg.K_LEFT or event.key == pg.K_a:
                self.move_left = False
            if event.key == pg.K_DOWN or event.key == pg.K_s:
                self.move_down = False
            if event.key == pg.K_UP or event.key == pg.K_w:
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
            Game.instance.get_level_properties(Game.instance.level + 1)
            
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
        self.surface.fill(THEMES[Game.instance.chosen_theme_index])
        self.surface.blit(Game.instance.screen, (0, 0), (self.x, self.y, self.width, self.height))
        Game.instance.screen.blit(pg.transform.scale(self.surface, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
      
class UI:
    def __init__(self, instance_name_raw: str) -> None:
        self.instance_name_raw = instance_name_raw
        self.activated = False
        self.chosen_index = 0
        self.text_box_color_unchosen = (100, 100, 100)
        self.text_box_color_chosen = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.text_box = {}
        self.options_functions = []
        self.total_option = len(UIs[self.instance_name_raw]["options"])
        self.get_options()
    
    def get_options(self):
        for i, option_name in enumerate(UIs[self.instance_name_raw]["options"]):
            self.options_functions.append(FUNCTIONS[option_name])
            text_surface = FONT.render(option_name, True, self.text_color)
            text_rect = text_surface.get_rect()
            text_rects_distance = text_rect.height + 20 # There is a distance of 20 pixel between each rects
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - text_rects_distance * ((self.total_option // 2) - i))
            self.text_box[option_name] = {
                        "text_surface": text_surface,
                        "rect": text_rect
                    }
        
    @staticmethod
    def switch_UI(UI_object = None): 
        if not UI_object: # UIreturn
            Game.instance.current_activated_UI_stack.pop().activated ^= 1
        else: # UIopen
            Game.instance.current_activated_UI_stack.append(UI_object)
            UI_object.activated ^= 1
            
    @staticmethod
    def UI_return(): # return to the previous UI
        UI.switch_UI()
        
    @staticmethod
    def UI_open(new_UI = None): # if no argument passed: opens the UI that is chosen; If with argument passed: opens the specified UI by getting the UI object with its name
        if not new_UI:
            current_UI = Game.instance.current_activated_UI_stack[-1]
            new_UI = UI.get_instance(UIs[current_UI.instance_name_raw]["options"][current_UI.chosen_index]) # in toml file, the 1st letter of the UI's option is capitalized, so i just put lower() here to avoid key errors
        UI.switch_UI(new_UI)
        
    @staticmethod
    def get_instance(UI_instance_name_raw): # just a function to improve the readability of the program
        return UIs[UI_instance_name_raw.lower().replace(' ', '_')]["instance"] # lower() and replace() functions to change the raw instance name according to snake_case naming rules

    @staticmethod
    def UI_return_ultimate():
        current_UI = Game.instance.current_activated_UI_stack[-1]
        for i in range(len(Game.instance.current_activated_UI_stack)):
            Game.instance.current_activated_UI_stack[i].activated ^= 1
            
        Game.instance.current_activated_UI_stack = []
        
        if current_UI.instance_name_raw == "return_main_menu": ## Note: if this function is called in the return_main_menu UI, 
            # it means the player confirmed to return to main menu; While if this function is not called from return_main_menu_UI,
            # it can just be other options using ultimate UI return function
            Game.instance.screen.fill(THEMES[Game.instance.chosen_theme_index])
            Game.instance.current_activated_UI_stack.append(UI.get_instance("main_menu"))
        
    def check_action(self, event):  # check if user changed action
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE and Game.instance.current_activated_UI_stack[-1].instance_name_raw != "main_menu":
                UI.UI_return()
            elif event.key == pg.K_RETURN:
                self.execute_action(self.chosen_index)
            elif event.key == pg.K_UP or event.key == pg.K_w:
                self.chosen_index -= 1
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                self.chosen_index += 1
            self.chosen_index = max(0, self.chosen_index % self.total_option)
                
    def execute_action(self, i): # execute chosen action
        if type(self.options_functions[i]) == tuple:
            for function in self.options_functions[i]:
                function()
        else:
            self.options_functions[i]()
             
    def update_UI(self) -> None:
        for i, option_name in enumerate(self.text_box):
            if i == self.chosen_index:
                pg.draw.rect(Game.instance.screen, self.text_box_color_chosen, self.text_box[option_name]["rect"])
            else:
                pg.draw.rect(Game.instance.screen, self.text_box_color_unchosen, self.text_box[option_name]["rect"], 0, 3)
            Game.instance.screen.blit(self.text_box[option_name]["text_surface"], self.text_box[option_name]["rect"])
      
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
        pg.draw.rect(Game.instance.screen, (255, 255, 0), self.level_display_rect)
        Game.instance.screen.blit(self.level_display_surface, self.level_display_rect)
        
        pg.draw.rect(Game.instance.screen, (255, 255, 0), self.time_display_rect)
        self.time_display_surface = FONT.render(f"Time used: {self.time_elapsed}", True, (0, 0, 0))
        Game.instance.screen.blit(self.time_display_surface, self.time_display_rect)
                  
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
        
def draw_screen() -> None:
    if Game.instance.current_activated_UI_stack:
        if Game.instance.current_activated_UI_stack[0].instance_name_raw == "main_menu":
            Game.instance.screen.fill(THEMES[Game.instance.chosen_theme_index])
        pg.draw.rect(Game.instance.screen, (0, 0, 255), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, 40)
        Game.instance.current_activated_UI_stack[-1].update_UI()
    else:
        Game.instance.screen.fill(THEMES[Game.instance.chosen_theme_index])

        draw_game_grid()
        
        camera.update()
        
        stats.update_stats_overlay()
    
    pg.display.update()
        
def draw_game_grid() -> None:
    for rectObj in wall.grid_rect_list:
        pg.draw.rect(Game.instance.screen, wall.color, rectObj, 10)
    pg.draw.rect(Game.instance.screen, goal.color, goal.grid_rect)
    
    if Game.instance.hint_activated:
        for path_hint_rect in background.grid_rect_list:
            pg.draw.rect(Game.instance.screen, background.color, path_hint_rect, 0, 5)
            
    
    Game.instance.screen.blit(player.surface_scaled, (player.x, player.y))
                   
def init_game() -> None:
    Game()

def init_UI():
    global UIs, FUNCTIONS
    with open("UI_options.json", "r") as UI_options_file:
        UIs = json.load(UI_options_file)
    # For options to call function, new key-value pairs have to be added here, in which FUNCTIONS[option_name_raw] = function
    FUNCTIONS = {
        "New Game": Game.new_game,
        "Settings": UI.UI_open,
        "Exit": Game.exit_game,

        "Continue": UI.UI_return,
        "Return Main Menu": UI.UI_open,

        "Difficulty": UI.UI_open,
        "BGM": UI.UI_open,
        "Character": UI.UI_open,
        "Theme": UI.UI_open,
        "Hint": (Game.switch_hint, UI.UI_return_ultimate),

        "Return to main menu and lose current progress": UI.UI_return_ultimate,
        "No": UI.UI_return,

        "Easy": (Game.change_difficulty, UI.UI_return),
        "Normal": (Game.change_difficulty, UI.UI_return),
        "Hard": (Game.change_difficulty, UI.UI_return),

        "Track 1": (Game.change_bgm, UI.UI_return),
        "Track 2": (Game.change_bgm, UI.UI_return),
        "Track 3": (Game.change_bgm, UI.UI_return),

        "Sprite 1": (Game.change_sprite, UI.UI_return),
        "Sprite 2": (Game.change_sprite, UI.UI_return),

        "Dark": (Game.change_theme, UI.UI_return),
        "Light": (Game.change_theme, UI.UI_return)
    }
    for instance_name_raw in UIs:
        UIs[instance_name_raw]["instance"] = UI(instance_name_raw)
    del FUNCTIONS
        
def init_config() -> None:
    config = toml.load("config.toml")
    # Main game
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, THEMES
    FPS = config["fps"]
    SCREEN_WIDTH = config["screen_width"]
    SCREEN_HEIGHT = config["screen_height"]
    THEMES = config["themes"]
    # Player
    global PATHS_TO_SPRITES, PLAYER_HP
    PATHS_TO_SPRITES = config["player"]["paths"]
    PLAYER_HP = config["player"]["HP"]
    # Font
    global FONT_FILE_PATH, FONT
    pg.font.init()
    FONT_FILE_PATH = config["font"]["path"]
    FONT = pg.font.Font(FONT_FILE_PATH, 50) 
    # BGMs
    global BGM
    BGM = config["bgm"]["paths"]
    
def main():
    global time_elapsed
    clock = pg.time.Clock()
    time_elapsed = 0.000000
    total_paused_time = 0
    pause_start_time = 0
    running = True
    while running:
        pg.key.stop_text_input() # Stop text input to allow WASD key to control the sprite
        clock.tick(FPS)
        if Game.instance.current_activated_UI_stack:
            if pause_start_time == 0:
                pause_start_time = pg.time.get_ticks()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                Game.exit_game()
            if event.type == pg.USEREVENT:
                Game.load_bgm()
            if event.type == pg.KEYDOWN:
                if Game.instance.current_activated_UI_stack: # if UI is turned on
                    Game.instance.current_activated_UI_stack[-1].check_action(event)
                else:
                    if event.key == pg.K_ESCAPE:
                        UI.UI_open(UI.get_instance("menu")) # turn on menu UI when it's currently in the main game
                        player.freeze() # freeze is needed as sprite.check_movement stops the sprite only when it detects KEYUP
            
        if not Game.instance.current_activated_UI_stack:
            if pause_start_time != 0:
                total_paused_time += pg.time.get_ticks() - pause_start_time
                pause_start_time = 0
            player.check_movement(event)
            player.execute_movement()
        
        time_elapsed = (pg.time.get_ticks() - total_paused_time) / 1000.0
        draw_screen()

if __name__ == "__main__":
    pg.init()
    pgcam.init()
    init_config()
    init_game()
    init_UI()
    Game.instance.current_activated_UI_stack = [UI.get_instance("main_menu")]
    Game.load_bgm()
    main()