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
        self.camera_size = 0
        self.current_activated_UI_stack = []
        self.get_level_properties()
     
    # switch_UI() turns off the current UI without arguments passed, and append new UI if called with arguments passed
    def switch_UI(self, UI_instance = None) -> None: # switch_UI() is in class Game because I realized that it would be better for overall management of classes
        if type(UI_instance) == list:
            UI_instance = UI_instance[0]

        
        if not UI_instance: # we only call switch_UI() without arguments when UI has already been activated, so there should be elements in the stack
            self.current_activated_UI_stack.pop().activated ^= 1
        else:
            self.current_activated_UI_stack.append(UI_instance)
            UI_instance.activated ^= 1
          
    def get_level_properties(self) -> None:
        global wall, goal, sprite, camera
        level_prop = toml.load("level_properties.toml")
        
        # Camera property
        self.camera_size = level_prop[str(self.level)]["camera_size"]
        # Map property
        self.map_size = level_prop[str(self.level)]["map_size"] # how many grids will be in the level
        width_to_height_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        self.main_col = int((self.map_size / (1 / width_to_height_ratio)) ** (1 / 2)) # w + (height-width ratio) * w = map.size^2
        self.main_row = int((self.map_size / width_to_height_ratio) ** (1 / 2)) # h + (width-height ratio) * h = map.size^2
        self.game_col = self.main_col + 1 + self.main_col % 2 # if there is even number of columns, right side must be wall
        self.game_row = self.main_row + 1 + self.main_row % 2 # if there is even number of rows, bottom must be wall
        self.grid_width = SCREEN_WIDTH // (self.game_col)
        self.grid_height = SCREEN_HEIGHT // (self.game_row) 
        self.grid_rect = pg.rect.Rect(0, 0, self.grid_width, self.grid_height) 
        dfs.makemaze(self.main_col, self.main_row) 
        with open("maze_map.json", "r") as maze_map_file:
            self.maze_map = []
            for row in json.load(maze_map_file):    # convert the maze from a 2d-array to 1d
                self.maze_map += row
        # The above map property will likely be removed to improve memory usage in the future

        # Global class objects
        wall = Wall(self.grid_width, self.grid_height)
        goal = Goal(self.grid_width, self.grid_height)
        sprite = Sprite(self.grid_width / 2, self.grid_height / 2)
        camera = Camera(self.camera_size)
        
        cursor = [0, 0]    
        for i in range(0, len(self.maze_map)):
            if self.maze_map[i] == 1: # if is wall
                wall.append_wall_rect(pg.rect.Rect(cursor[0], cursor[1], self.grid_width, self.grid_height))
            elif self.maze_map[i] == 2: # if is goal
                goal.set_goal_rect(pg.rect.Rect(cursor[0], cursor[1], self.grid_width, self.grid_height))
            if i != 0 and (i + 1) % self.game_col == 0: 
                cursor[0] = 0
                cursor[1] += self.grid_height # As pg rect only process integer, the grid spacings are corrected to decimal places
            else:
                cursor[0] += self.grid_width
                       
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
    def __init__(self, camera_size) -> None:
        self.object = pgcam.Camera(pgcam.list_cameras()[0])
        self.width = SCREEN_WIDTH * camera_size
        self.height = SCREEN_HEIGHT * camera_size
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
        self.UItype = UItype ## this specifies if the UI is pause menu/settings; have room for improvement for modularity
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
        for option in OPTIONS[self.UItype]:
            self.actions.append(self.get_action_function(option))
        
        for i, option in enumerate(OPTIONS[self.UItype]):
            text_surface = self.FONT.render(option, True, self.text_color)
            text_rect = text_surface.get_rect()
            text_rects_distance = text_rect.height + 20 # There is a distance of 20 pixel between each rects
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - text_rects_distance * ((len(self.actions) // 2) - i))
            self.text_box[option] = {
                        "text_surface": text_surface,
                        "rect": text_rect
                    }
        
    def get_action_function(self, action_str): # get the function of the respective UI option
        if re.search(r"\bcontinue\b", action_str, re.IGNORECASE): # Note: \b finds exact match only
            return game_obj.switch_UI
        if re.search(r"\bsettings\b", action_str, re.IGNORECASE):
            return [game_obj.switch_UI, settings] # the first element is the function, remaining is the argument
        if re.search(r"\bexit\b", action_str, re.IGNORECASE):
            return exit_game
        if re.search(r"\bdifficulty\b", action_str, re.IGNORECASE):
            return print("difficulty option found") # temp
        if re.search(r"\bbackground\b", action_str, re.IGNORECASE):
            return print("background option found") # temp
        if re.search(r"\bcharacter\b", action_str, re.IGNORECASE):
            return print("character option found") # temp
        if re.search(r"\btheme\b", action_str, re.IGNORECASE):
            return print("theme option found") # temp
        
    def check_action(self, event):  # check if user changed action
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.execute_action(self.chosen_index)
            elif event.key == pg.K_UP:
                self.chosen_index -= 1
            elif event.key == pg.K_DOWN:
                self.chosen_index += 1
            self.chosen_index = max(0, min(self.chosen_index, self.total_action - 1))
            ## Bitwise operation to make -1 become total_action -1, and make total_action become 0
            ## self.chosen_index = self.chosen_index = self.chosen_index = (self.chosen_index == -1) * (self.total_action - 1) + (self.chosen_index == self.total_action) * 0 + (self.chosen_index != -1) * (self.chosen_index != self.total_action) * self.chosen_index
    
            #1111 (-1)
            #0000 (0)
            #0001 (1)
            #0010 (2)
            #0011 (3)
            #0100 (4)
                
    def execute_action(self, i): # execute chosen action
        if callable(self.actions[i]): # if the action is a list, it contains the function and the arguments
            self.actions[i]()
        else:
            self.actions[i][0](self.actions[i][1:]) ## calls the function and pass the arguments as a list
            
        
    def update_UI(self) -> None:
        for i, option in enumerate(OPTIONS[self.UItype]):
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
        pg.draw.rect(game_obj.screen, (0, 0, 255), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, 4)
        game_obj.current_activated_UI_stack[-1].update_UI()
    else:
        game_obj.screen.fill(bg_color)
        
        draw_game_grid()
        
        camera.update()
    
    pg.display.flip()
        
def draw_game_grid() -> None:
    for rectObj in wall.grid_rect_list:
        pg.draw.rect(game_obj.screen, wall.color, rectObj, 10)
    pg.draw.rect(game_obj.screen, goal.color, goal.grid_rect)
    
    game_obj.screen.blit(sprite.surface_scaled, (sprite.x, sprite.y))
    
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
                        game_obj.switch_UI(menu) # turn on menu UI when it's currently in the main game
                    else:
                        game_obj.switch_UI() # turn off the last opened UI (Please see UI.switch_UI() for reference, default argument is game_obj.current_activated_UI_stack[-1])
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
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, PATH_TO_SPRITE, bg_color, FONT_FILE_PATH, OPTIONS
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
    OPTIONS = {
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