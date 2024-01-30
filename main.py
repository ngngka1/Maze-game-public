import pygame as pg
import pygame.camera as pgcam
import dfs
import toml
import sys
import json
import re
import math

class Game:
    def __init__(self, level=1) -> None:
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Maze minigame")
        self.level = level
        self.current_activated_UI_stack: list[UI] = []
        self.get_level_properties()
     
    # switch_UI() turns off the current UI without arguments passed, and append new UI if called with arguments passed
    def switch_UI(self, UI_instance = None) -> None: # switch_UI() is in class Game because I realized that it would be better for overall management of classes
        if not UI_instance: 
            self.current_activated_UI_stack.pop().activated ^= 1
        else:
            self.current_activated_UI_stack.append(UI_instance)
            UI_instance.activated ^= 1
          
    def get_level_properties(self) -> None:
        global wall, goal, sprite, camera, menu, settings
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
        camera_width = grid_width * 10
        camera_height = (grid_width * 10) // width_to_height_ratio # substitution of: camera_width / camera_height = width_height ratio
        dfs.makemaze(main_col, main_row) 
        with open("maze_map.json", "r") as maze_map_file:
            maze_map = []
            for row in json.load(maze_map_file):    # convert the maze from a 2d-array to 1d
                maze_map += row

        # Global class objects
        wall = Wall(grid_width, grid_height)
        goal = Goal(grid_width, grid_height)
        sprite = Sprite(grid_width / 2, grid_height / 2)
        camera = Camera(camera_width, camera_height)
        settings = UI("settings") 
        menu = UI("menu")
        self.UI_str_list = {"settings": settings, "menu": menu}
        
        
        cursor = [0, 0]    
        for i in range(0, len(maze_map)):
            if maze_map[i] == 1: # if is wall
                wall.append_wall_rect(pg.rect.Rect(cursor[0], cursor[1], grid_width, grid_height))
            elif maze_map[i] == 2: # if is goal
                goal.set_goal_rect(pg.rect.Rect(cursor[0], cursor[1], grid_width, grid_height))
            if i != 0 and (i + 1) % game_col == 0: 
                cursor[0] = 0
                cursor[1] += grid_height
            else:
                cursor[0] += grid_width
                       
class Sprite:
    def __init__(self, width, height) -> None:
        self.path = PATH_TO_SPRITE
        self.width = int(width)
        self.height = int(height)
        self.x = width * 2 + 1  # the parameter width and heigth are actually game_obj.grid_width & height divided by 2
        self.y = height * 2 + 1
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
        self.movement_speed = self.width // 3
        self.surface_unscaled = pg.image.load(self.path)
        self.surface_scaled = pg.transform.scale(self.surface_unscaled, (self.width, self.height))
        self.hitbox = pg.Rect(self.x, self.y, self.width, self.height)
        
    def check_movement(self, event) -> None:

        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RIGHT:
                self.move_right = True
            if event.key == pg.K_LEFT:
                self.move_left = True
            if event.key == pg.K_DOWN:
                self.move_down = True
            if event.key == pg.K_UP:
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
        elif self.move_down:
            target_y += self.movement_speed
        if self.move_left:
            target_x -= self.movement_speed
        elif self.move_right:
            target_x += self.movement_speed
            

        if target_x != self.x:
            self.hitbox.x = target_x
            for rect in wall.grid_rect_list:
                if self.hitbox.colliderect(rect):
                    self.hitbox.x = self.x
                    
            
        if target_y != self.y:
            self.hitbox.y = target_y
            for rect in wall.grid_rect_list:
                if self.hitbox.colliderect(rect):
                    self.hitbox.y = self.y

        self.x = self.hitbox.x
        self.y = self.hitbox.y
        
        self.pass_check()
        
        
    def pass_check(self):
        if self.hitbox.colliderect(goal.grid_rect):
            game_obj.level += 1
            game_obj.get_level_properties()
            
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
        self.x = sprite.x - self.width // 2
        self.y = sprite.y - self.height // 2
        
    def update(self) -> None:
        self.x = sprite.x - self.width // 2
        self.y = sprite.y - self.height // 2
        self.surface.fill(bg_color)
        self.surface.blit(game_obj.screen, (0, 0), (self.x, self.y, self.width, self.height))
        game_obj.screen.blit(pg.transform.scale(self.surface, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
      
class UI:
    def __init__(self, UItype: str) -> None:
        self.options = OPTIONS_ALL_UI[UItype] ## this specifies if the UI is pause menu/settings; have room for improvement for modularity
        self.activated = False
        self.chosen_index = 0
        self.text_box_color_unchosen = (100, 100, 100)
        self.text_box_color_chosen = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.FONT = pg.font.Font(FONT_FILE_PATH, 50) ####
        self.text_box = {}
        self.actions = []
        self.get_options()
        self.total_action = len(self.actions)
        
    def get_options(self):
        for option in self.options:
            self.actions.append(self.get_action_function(option))
        
        for i, option in enumerate(self.options):
            text_surface = self.FONT.render(option, True, self.text_color)
            text_rect = text_surface.get_rect()
            text_rects_distance = text_rect.height + 20 # There is a distance of 20 pixel between each rects
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - text_rects_distance * ((len(self.actions) // 2) - i))
            self.text_box[option] = {
                        "text_surface": text_surface,
                        "rect": text_rect
                    }
        
    def get_action_function(self, option_str): # get the function of the respective UI option
        if re.search(r"\bcontinue\b", option_str, re.IGNORECASE): # Note: \b finds exact match only
            return UIreturn
        if re.search(r"\bsettings\b", option_str, re.IGNORECASE):
            return UIopen # the first element is the function, remaining is the argument
        if re.search(r"\bexit\b", option_str, re.IGNORECASE):
            return exit_game
        if re.search(r"\bdifficulty\b", option_str, re.IGNORECASE):
            return print("difficulty option found") # temp
        if re.search(r"\bbackground\b", option_str, re.IGNORECASE):
            return print("background option found") # temp
        if re.search(r"\bcharacter\b", option_str, re.IGNORECASE):
            return print("character option found") # temp
        if re.search(r"\btheme\b", option_str, re.IGNORECASE):
            return print("theme option found") # temp
        
    def check_action(self, event):  # check if user changed action
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.execute_action(self.chosen_index)
            elif event.key == pg.K_UP:
                self.chosen_index -= 1
            elif event.key == pg.K_DOWN:
                self.chosen_index += 1
            self.chosen_index = max(0, self.chosen_index % self.total_action)
                
    def execute_action(self, i): # execute chosen action
        if callable(self.actions[i]): # if the action is a list, it contains the function and the arguments
            self.actions[i]()
        else:
            self.actions[i][0](self.actions[i][1:]) ## calls the function and pass the arguments as a list
             
    def update_UI(self) -> None:
        for i, option in enumerate(self.options):
            if i == self.chosen_index:
                pg.draw.rect(game_obj.screen, self.text_box_color_chosen, self.text_box[option]["rect"])
            else:
                pg.draw.rect(game_obj.screen, self.text_box_color_unchosen, self.text_box[option]["rect"], 0, 3)
            game_obj.screen.blit(self.text_box[option]["text_surface"], self.text_box[option]["rect"])
                
class Collision_object:
    def __init__(self, width, height) -> None:
        self.width = width
        self.height = height
        
class Wall(Collision_object):
    def __init__(self, width, height) -> None:
        super().__init__(width, height)
        self.grid_rect_list = []
        self.color = (0, 0, 0)
        
    def append_wall_rect(self, rect) -> None:
        self.grid_rect_list.append(rect)
              
class Goal(Collision_object):
    def __init__(self, width, height) -> None:
        super().__init__(width, height)
        self.grid_rect = None
        self.color = (0, 0, 255)
        
    def set_goal_rect(self, rect) -> None:
        self.grid_rect = rect
        
def draw_screen() -> None:
    if game_obj.current_activated_UI_stack:
        pg.draw.rect(game_obj.screen, (0, 0, 255), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, 40)
        game_obj.current_activated_UI_stack[-1].update_UI()
    else:
        game_obj.screen.fill(bg_color)
        
        draw_game_grid()
        
        camera.update()
    
    pg.display.update()
        
def draw_game_grid() -> None:
    for rectObj in wall.grid_rect_list:
        pg.draw.rect(game_obj.screen, wall.color, rectObj, 10)
    pg.draw.rect(game_obj.screen, goal.color, goal.grid_rect)
    
    game_obj.screen.blit(sprite.surface_scaled, (sprite.x, sprite.y))
    
def UIreturn():
    game_obj.switch_UI()
    
def UIopen(new_UI = None): ##readablity can be improved, anyways this opens the UI with the name of the chosen option
    if not new_UI:
        current_UI = game_obj.current_activated_UI_stack[-1]
        new_UI = game_obj.UI_str_list[current_UI.options[current_UI.chosen_index].lower()] # in toml file, the 1st letter of the UI's option is capitalized, so i just put lower() here to avoid key errors
    game_obj.switch_UI(new_UI)
    
def open_settings_UI():
    game_obj.switch_UI(settings)
    
        

def exit_game():
    pg.quit()
    sys.exit()
    
def main():
    running = True
    while running:
        clock = pg.time.Clock()
        clock.tick(FPS)
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                exit_game()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    if not game_obj.current_activated_UI_stack:
                        UIopen(menu) # turn on menu UI when it's currently in the main game
                    else:
                        UIreturn() # turn off the last opened UI (Please see UI.switch_UI() for reference, default argument is game_obj.current_activated_UI_stack[-1])
            if game_obj.current_activated_UI_stack: # if UI is turned on
                sprite.freeze() # freeze is needed as sprite.check_movement stops the sprite only when it detects KEYUP
                game_obj.current_activated_UI_stack[-1].check_action(event)
            else:
                sprite.check_movement(event)
        sprite.execute_movement()
            
        draw_screen()
                
def init_game() -> None:
    global game_obj
    game_obj = Game()
    init_UI()
    
def init_UI():
    ## IMPORATANT: each UI object has to be declared in reverse order, as the outer UI (e.g. menu) links to inner UI (e.g. settings), without declaring settings first, initialization of menu will return error. Refer to line 199
    global menu, settings
    settings = UI("settings") 
    menu = UI("menu") 
        
def init_config() -> None:
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, PATH_TO_SPRITE, bg_color, FONT_FILE_PATH, OPTIONS_ALL_UI
    config = toml.load("config.toml")
    FPS = config["fps"]
    SCREEN_WIDTH = config["screen_width"]
    SCREEN_HEIGHT = config["screen_height"]
    bg_color = config["default_background_color"]
    PATH_TO_SPRITE = config["sprite"]["path"]
    # Font
    pg.font.init()
    FONT_FILE_PATH = config["font"]["path"]
    # Menu
    OPTIONS_ALL_UI = {
        "menu": config["menu"]["options"],
        "settings": config["settings"]["options"],
    }
    
    
    
if __name__ == "__main__":
    global camera
    pg.init()
    pgcam.init()
    init_config()
    init_game()
    main()