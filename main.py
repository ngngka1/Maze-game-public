import pygame as pg
import pygame.camera as pgcam
from config import *
from makemaze import generate_map
from collections import OrderedDict
import sys
import json
from Astar_search import Astar_search
from typing import Union
from ListNode import ListNode
import threading
import time
import random
import inspect

def time_count():
    seconds = 5
    for i in range(0, seconds * 20):
        # remaining_time = seconds - i # might be used in the future
        if terminate_thread_event.is_set(): # if need to terminate
            return
        time.sleep(0.05)
        
def center_wrapper(func):
    def center(object: SurfaceObject | RectObject, *args):
        object.x += (Game.instance.grid_width - object.width) // 2
        object.y += (Game.instance.grid_height - object.height) // 2
        if type(object) is RectObject:
            object.rect.x = object.x
            object.rect.y = object.y
        return func(object, *args)
    return center

class Game:
    instance: Union["Game", None] = None
    def __init__(self) -> None:
        if Game.instance is not None:
            raise Exception("Only 1 game object can be created!")
        Game.instance = self
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Maze minigame")
        self.level = None
        
        self.difficulty = 0
        self.bgm_track_index = 0
        self.chosen_theme_index = 0
        self.chosen_sprite_index = 0
          
    def get_level_properties(self, level = 1) -> None:
        global time_elapsed
        self.level = level
        maze_generation_algorithm = LEVEL_PROPERTIES["difficulty"][str(self.difficulty)]["algorithm"]
        map_enlargement_scale = LEVEL_PROPERTIES["difficulty"][str(self.difficulty)]["map_enlargement_scale"]
        item_appearance_rate = LEVEL_PROPERTIES["difficulty"][str(self.difficulty)]["item_appearance_rate"]
        
        # Map property
        map_size = LEVEL_PROPERTIES[str(self.level)]["map_size"] * map_enlargement_scale # how many grids (will be rounded) will be in the level
        width_to_height_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
        maze_column = int((map_size / (1 / width_to_height_ratio)) ** (1 / 2)) # w * (height-width ratio) * w = map.size -> w^2 * h/w = map.size -> w = (map.size / (h/w))^0.5
        maze_row = int((map_size / width_to_height_ratio) ** (1 / 2)) # h * (width-height ratio) * h = map.size
        maze_column += (maze_column + 1) % 2
        maze_row += (maze_row + 1) % 2
        self.grid_width = SCREEN_WIDTH // (maze_column)
        self.grid_height = SCREEN_HEIGHT // (maze_row)
        
        generate_map(maze_column, maze_row, maze_generation_algorithm, item_appearance_rate)
        with open("maze_map.json", "r") as maze_map_file:
            self.maze_map = json.load(maze_map_file)
                
        self.get_new_game_class_objects(self.grid_width, self.grid_height)

        cursor = [0, 0]    # refers to printing coordinate [x, y]
        for row_num in range(0, maze_row):
            cursor = [0, row_num * self.grid_height]
            for column_num in range(0, maze_column):
                if self.maze_map[row_num][column_num] == 1: # if is wall
                    wall.append_rect_object(RectObject(cursor[0], cursor[1], wall.default_width, wall.default_height, (0, 0, 0), 5, 2))
                elif self.maze_map[row_num][column_num] == 2: # if is goal
                    goal.append_rect_object(RectObject(cursor[0], cursor[1], goal.default_width, goal.default_height, (0, 0, 255), 0, 2))
                elif self.maze_map[row_num][column_num] == 3: # if is item
                    items.append_surface_object(SurfaceObject(cursor[0], cursor[1], items.default_width, items.default_height))
                cursor[0] += self.grid_width
   
    def get_new_game_class_objects(self, grid_width, grid_height) -> None:
        global wall, goal, player, hint, items, GAME_OBJECTS, camera, stats
        wall = Wall(grid_width, grid_height)
        goal = Goal(grid_width, grid_height)
        hint = Hint(grid_width // 2, grid_height // 2)
        items = Items(grid_width // 2, grid_height // 2)
        
        GAME_OBJECTS = (wall, goal, hint, items)
        
        if self.level > 1:
            player = Player(grid_width / 2, grid_height / 2, player.HP)
        else:
            player = Player(grid_width / 2, grid_height / 2, PLAYER_DEFAULT_HP)
        camera = Camera(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        stats = Stats(self.level)
        
    @staticmethod
    def new_game():
        Game.instance.get_level_properties()
        UIFactory.switch_UI()

    @staticmethod
    def exit_game(): # exit game
        pg.quit()
        sys.exit()
        
    @staticmethod
    def change_difficulty():
        # Difficulty scale for "Easy", "Normal" and "Hard" are 1, 2, 3 respectively
        # indices for "Easy", "Normal" and "Hard" in the setting UI are 0, 1, 2;
        Game.instance.difficulty = UIFactory.get_chosen_option()
        
    @staticmethod
    def activate_hint(item_surface_object): # I have to seaparate activate and deactivate due to possiblity
        hint.activated = True # that player might get two path hint item in a short period of time
        hint.get_hint(item_surface_object)
        
    @staticmethod
    def deactivate_hint():
        hint.activated = False
        
    @staticmethod
    def load_bgm(i=0):
        pg.mixer.music.load(BGM[Game.instance.bgm_track_index])
        pg.mixer.music.play()
        pg.mixer.music.set_endevent(pg.USEREVENT)
            
    @staticmethod
    def change_bgm():
        Game.instance.bgm_track_index = UIFactory.get_chosen_option()
        Game.load_bgm()
        
    @staticmethod
    def change_theme():
        Game.instance.chosen_theme_index = UIFactory.get_chosen_option()
        
    @staticmethod
    def change_sprite():
        Player.sprite_surface = pg.image.load(PATHS_TO_SPRITES[UIFactory.activated_UI[-1].chosen_index])
        if Game.instance.level is not None:
            player.surface_scaled = pg.transform.smoothscale(Player.sprite_surface, (player.width, player.height))

    @staticmethod 
    def heal_player():
        player.HP += 1
        
class Player:
    sprite_surface = pg.image.load(PATHS_TO_SPRITES[0])
    def __init__(self, width, height, current_HP = None) -> None:
        self.HP = current_HP
        self.width = int(width)
        self.height = int(height)
        self.x = width * 2 + 1  # the parameter width and heigth are actually Game.instance.grid_width & height divided by 2
        self.y = height * 2 + 1
        self.move_up = False
        self.move_down = False
        self.move_left = False
        self.move_right = False
        self.movement_speed = self.width // 3
        self.surface_scaled = pg.transform.smoothscale(self.sprite_surface, (self.width, self.height))
        self.hitbox = pg.Rect(self.x, self.y, self.width, self.height)
        
    def check_movement(self) -> None:
        keys = pg.key.get_pressed()
        self.move_right = keys[pg.K_RIGHT] and not keys[pg.K_LEFT]
        self.move_left = not keys[pg.K_RIGHT] and keys[pg.K_LEFT]
        self.move_down = keys[pg.K_DOWN] and not keys[pg.K_UP]
        self.move_up = not keys[pg.K_DOWN] and keys[pg.K_UP]
            
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
            for rect_object in wall.rect_object_list:
                if self.hitbox.colliderect(rect_object.rect):
                    if self.x + self.width <= rect_object.x:
                        self.hitbox.x -= (self.hitbox.x + self.width) - rect_object.x
                    else:
                        self.hitbox.x += (rect_object.x + rect_object.width) - self.hitbox.x
                    
        if target_y != self.y:
            self.hitbox.y = target_y
            for rect_object in wall.rect_object_list:
                if self.hitbox.colliderect(rect_object.rect):
                    if self.y + self.height <= rect_object.y:
                        self.hitbox.y -= (self.hitbox.y + self.height) - rect_object.y
                    else:
                        self.hitbox.y += (rect_object.y + rect_object.height) - self.hitbox.y

        self.x = self.hitbox.x
        self.y = self.hitbox.y
        self.move_right = False
        self.move_left = False
        self.move_down = False
        self.move_up = False
        self.obtained_item_check()
        self.pass_check()
        
    def pass_check(self):
        if self.hitbox.colliderect(goal.rect_object_list[0].rect):
            terminate_thread_event.set()
            while threading.active_count() != 1: # 1 because the main thread also count as a thread
                thread.join()
                continue
            Game.instance.get_level_properties(Game.instance.level + 1)
            
    def obtained_item_check(self):
        for item_node in items.surface_object_list.nodes():
            item: SurfaceObject = item_node.val
            if self.hitbox.colliderect(pg.rect.Rect(item.x, item.y, item.width, item.height)):
                ListNode.pop(item_node)
                items.obtained(**{"item_surface_object": item})
                break
   
class Camera:
    def __init__(self, width, height) -> None:
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
      
class UIFactory:
    activated_UI: list["UI"] = []
    UI_list: list["UI"] = {}
    
    @staticmethod
    def switch_UI(UI_object = None): 
        if not UI_object: # UIreturn
            UIFactory.activated_UI.pop().activated ^= 1
        else: # UIopen
            UIFactory.activated_UI.append(UI_object)
            UI_object.activated ^= 1
    
    @staticmethod
    def UI_return(): # return to the previous UI
        UIFactory.switch_UI()
        
    @staticmethod
    def UI_open(new_UI = None): # if no argument passed: opens the UI that is chosen; If with argument passed: opens the specified UI by getting the UI object with its name
        if not new_UI:
            new_UI = UIFactory.get_chosen_option() # in toml file, the 1st letter of the UI's option is capitalized, so i just put lower() here to avoid key errors
        UIFactory.switch_UI(new_UI)
        
    @staticmethod
    def get_instance(UI_instance_name_raw): # just a function to improve the readability of the program
        parsed_name = UI_instance_name_raw.lower().replace(' ', '_')
        if parsed_name in UIFactory.UI_list:
            return UIFactory.UI_list[parsed_name] # lower() and replace() functions to change the raw instance name according to snake_case naming rules
        else:
            return None
    @staticmethod
    def get_chosen_option():
        """ This return the chosen option either in UI/int, for example,
        if option "setting" is chosen, it returns an UI object; If option
        "Easy" is chosen in the difficulty setting, where no UI object is 
        associated with the choice, the chosen index will be returned.

        Returns:
            _type_: UI | int
        """
        current_UI = UIFactory.activated_UI[-1]
        instance = UIFactory.get_instance(current_UI.options[current_UI.chosen_index]["name"])
        if instance:
            return instance
        else:
            return current_UI.chosen_index
        
    @staticmethod
    def UI_return_ultimate():
        current_UI = UIFactory.activated_UI[-1]
        for i in range(len(UIFactory.activated_UI)):
            UIFactory.activated_UI[i].activated ^= 1
            
        UIFactory.activated_UI = []
        
        if current_UI.instance_name_raw == "return_main_menu": ## Note: if this function is called in the return_main_menu UI, 
            # it means the player confirmed to return to main menu; While if this function is not called from return_main_menu_UI,
            # it can just be other options using ultimate UI return function
            Game.instance.screen.fill(THEMES[Game.instance.chosen_theme_index])
            UIFactory.activated_UI.append(UIFactory.get_instance("main_menu"))
      
class UI:
    __functions = {
        "New Game": Game.new_game,
        "Settings": UIFactory.UI_open,
        "Exit": Game.exit_game,

        "Continue": UIFactory.UI_return,
        "Return Main Menu": UIFactory.UI_open,

        "Difficulty": UIFactory.UI_open,
        "BGM": UIFactory.UI_open,
        "Character": UIFactory.UI_open,
        "Theme": UIFactory.UI_open,
        # "Hint": (Game.switch_hint, UIFactory.UI_return_ultimate),

        "Return to main menu and lose current progress": UIFactory.UI_return_ultimate,
        "No": UIFactory.UI_return,

        "Easy": (Game.change_difficulty, UIFactory.UI_return),
        "Normal": (Game.change_difficulty, UIFactory.UI_return),
        "Hard": (Game.change_difficulty, UIFactory.UI_return),

        "Track 1": (Game.change_bgm, UIFactory.UI_return),
        "Track 2": (Game.change_bgm, UIFactory.UI_return),
        "Track 3": (Game.change_bgm, UIFactory.UI_return),

        "Sprite 1": (Game.change_sprite, UIFactory.UI_return),
        "Sprite 2": (Game.change_sprite, UIFactory.UI_return),

        "Dark": (Game.change_theme, UIFactory.UI_return),
        "Light": (Game.change_theme, UIFactory.UI_return)
    }
    def __init__(self, instance_name_raw: str, options) -> None:
        self.instance_name_raw = instance_name_raw
        self.activated = False
        self.text_box_color_unchosen = (100, 100, 100)
        self.text_box_color_chosen = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.text_box = []
        self.options = []
        self.total_option = len(options)
        self.get_options(options)
        self.chosen_index = 0
    
    def get_options(self, options):
        for i, option_name in enumerate(options):
            self.options.append({
                "name": option_name,
                "function": UI.__functions[option_name]
            })
            text_surface = FONT.render(option_name, True, self.text_color)
            text_rect = text_surface.get_rect()
            text_rects_distance = text_rect.height + 20 # There is a distance of 20 pixel between each rects
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - text_rects_distance * ((self.total_option // 2) - i))
            self.text_box.append({
                        "text_surface": text_surface,
                        "rect": text_rect
                    })
        
    def check_action(self, event):  # check if user changed action
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE and UIFactory.activated_UI[-1].instance_name_raw != "main_menu":
                UIFactory.UI_return()
            elif event.key == pg.K_RETURN:
                self.execute_action(self.chosen_index)
            elif event.key == pg.K_UP or event.key == pg.K_w:
                self.chosen_index -= 1
            elif event.key == pg.K_DOWN or event.key == pg.K_s:
                self.chosen_index += 1
            self.chosen_index = max(0, self.chosen_index % self.total_option)
                
    def execute_action(self, i): # execute chosen action
        if type(self.options[i]["function"]) == tuple:
            for function in self.options[i]["function"]:
                function()
        else:
            self.options[i]["function"]()
             
    def update_UI(self) -> None:
        for i in range(len(self.options)):
            if i == self.chosen_index:
                pg.draw.rect(Game.instance.screen, self.text_box_color_chosen, self.text_box[i]["rect"])
            else:
                pg.draw.rect(Game.instance.screen, self.text_box_color_unchosen, self.text_box[i]["rect"], 0, 3)
            Game.instance.screen.blit(self.text_box[i]["text_surface"], self.text_box[i]["rect"])
      
class Stats:
    def __init__(self, current_level, time_elapsed = 0):
        self.display = True
        cursor_x = (camera.x + SCREEN_WIDTH // 2) // 2
        cursor_y = (camera.y + SCREEN_HEIGHT // 2) // 2
        self.time_elapsed = time_elapsed
        self.time_display_surface = FONT.render(f"Time used: {time_elapsed:.3f}", True, (0, 0, 0))
        self.time_display_rect = self.time_display_surface.get_rect(center = (cursor_x, cursor_y))
        
        cursor_y += 80
        self.level_display_surface = FONT.render(f"Current level: {current_level}", True, (0, 0, 0))
        self.level_display_rect = self.level_display_surface.get_rect(center = ((cursor_x, cursor_y)))
        
        cursor_y += 80
        current_difficulty = UIFactory.get_instance("difficulty").options[Game.instance.difficulty]["name"]
        self.difficulty_display_surface = FONT.render(f"Current difficulty: {current_difficulty}", True, (0, 0, 0))
        self.difficulty_display_rect = self.difficulty_display_surface.get_rect(center = (cursor_x, cursor_y))
        
        cursor_y += 80
        self.HP_display_surface = pg.transform.smoothscale(pg.image.load("assets\Heart.png"), (30, 30))
        self.HP_display_y = cursor_y
        
        self.level_display_rect.x = self.time_display_rect.x = self.difficulty_display_rect.x
        ## of course in the future i will improve this terrible code
        
        
    def update_stats_overlay(self):
        self.time_elapsed = time_elapsed
        pg.draw.rect(Game.instance.screen, (255, 255, 0), self.level_display_rect)
        Game.instance.screen.blit(self.level_display_surface, self.level_display_rect)
        
        pg.draw.rect(Game.instance.screen, (255, 255, 0), self.time_display_rect)
        self.time_display_surface = FONT.render(f"Time used: {self.time_elapsed}", True, (0, 0, 0))
        Game.instance.screen.blit(self.time_display_surface, self.time_display_rect)
        
        pg.draw.rect(Game.instance.screen, (255, 255, 0), self.difficulty_display_rect)
        Game.instance.screen.blit(self.difficulty_display_surface, self.difficulty_display_rect)
        
        cursor = [self.level_display_rect.x, self.HP_display_y]
        for i in range(player.HP):
            Game.instance.screen.blit(self.HP_display_surface, (cursor[0], cursor[1]))
            if i != 0 and (i + 1) % 5 == 0:
                cursor[0] = self.level_display_rect.x
                cursor[1] += 30 + 10
            else:
                cursor[0] += 30 + 10
                         
class RectObject:
    def __init__(self, x=None, y=None, width=None, height=None, color=(0, 0, 0), border_width=0, border_radius=0) -> None:
        self.activated = True
        if self.__class__ is RectObject:
            # self.x are actually not necessary for rect as we can access it through rect.x
            # but for consistency(we have self.x in SurfaceObject), it is still added
            self.x = x
            self.y = y
            self.width = width
            self.height = height
        
            self.rect_color = color
            self.rect_border_width = border_width
            self.rect_border_radius = border_radius
            self.rect = pg.rect.Rect(self.x, self.y, self.width, self.height)
        else:
            self.rect_object_list: list[RectObject] = []
        
    def append_rect_object(self, rect_object):
        self.rect_object_list.append(rect_object)
        
    def print(self):
        for rect_object in self.rect_object_list:
            pg.draw.rect(Game.instance.screen, rect_object.rect_color, rect_object.rect, rect_object.rect_border_width, rect_object.rect_border_radius)
               
class SurfaceObject:
    def __init__(self, x=None, y=None, width=None, height=None) -> None:
        self.activated = True
        if self.__class__ is SurfaceObject:
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            unscaled_surface = pg.image.load(PATH_TO_ITEM)
            self.scaled_surface = pg.transform.scale(unscaled_surface, (self.width, self.height))
        else:
            self.surface_object_list: list[SurfaceObject] = []
    
    def append_surface_object(self, surface_object):
        self.surface_object_list.append(surface_object)
        
    def print(self):
        for surface_object in self.surface_object_list:
            Game.instance.screen.blit(surface_object.scaled_surface, (surface_object.x, surface_object.y))
        
class Wall(RectObject):
    def __init__(self, width, height) -> None:
        super().__init__()
        self.default_width = width
        self.default_height = height
        
class Goal(RectObject):
    def __init__(self, width, height) -> None:
        super().__init__()
        self.default_width = width
        self.default_height = height
        
class Hint(RectObject):
    def __init__(self, width, height) -> None:
        super().__init__()
        self.default_width = width
        self.default_height = height
        self.activated = False
        self.append_rect_object = center_wrapper(self.append_rect_object)
        
    def get_hint(self, item_surface_object: SurfaceObject):
        self.rect_object_list = []
        # get the center of the player and get its current grid
        row_num = item_surface_object.y // Game.instance.grid_height
        column_num = item_surface_object.x // Game.instance.grid_width
        paths = Astar_search(Game.instance.maze_map, (column_num, row_num), None, 1)
        for path in paths:
            hint.append_rect_object(RectObject(path[1] * Game.instance.grid_width, path[0] * Game.instance.grid_height, hint.default_width, hint.default_height, (255, 0, 25), 0, 5))
      
class Items(SurfaceObject):
    __items = (
        # buff
        (Game.activate_hint, time_count, Game.deactivate_hint), # Shows path
        Game.heal_player, # Increase hp by 1
        # debuff
        
        
    )
    
    def __init__(self, width, height) -> None:
        super().__init__(None, None, width, height)
        self.default_width = width
        self.default_height = height
        self.list_tail = self.surface_object_list = ListNode()
        # this line converts the function from performing action of appending to list,
        # to action of appending to a linked list, while requiring 2 additional arguments,
        # which are now (self, surface_object, head, tail)
    
    def append_surface_object(self, surface_object):
        append_linkedlist = center_wrapper(ListNode.append_linkedlist)
        head = self.surface_object_list
        tail = self.list_tail
        self.list_tail = append_linkedlist(surface_object, head, tail)
        
    def generate_random_item(self):
        option = random.randrange(0, len(self.__items))
        return self.__items[option]
    
    def obtained(self, **kwargs):
        global thread
        
        item_function = self.generate_random_item()
        if type(item_function) == tuple:
            def run_functions(functions, **kwargs):
                for function in functions:
                    if not terminate_thread_event.is_set(): # if dont need to terminate
                        if len(inspect.signature(function).parameters) > 0:
                            function(**kwargs)
                        else:
                            function()
                    else:
                        terminate_thread_event.clear() # clear flag first
                        break
            thread = threading.Thread(target=run_functions, args=(item_function,), kwargs=kwargs)
            thread.start()
        else:
            item_function()
        
class Monster:
    def __init__(self, width, height, HP):
        self.width = width
        self.height = height
        self.HP = HP
        
def draw_screen() -> None:
    if UIFactory.activated_UI:
        if UIFactory.activated_UI[0].instance_name_raw == "main_menu":
            Game.instance.screen.fill(THEMES[Game.instance.chosen_theme_index])
        pg.draw.rect(Game.instance.screen, (0, 0, 255), (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 0, 40)
        UIFactory.activated_UI[-1].update_UI()
    else:
        Game.instance.screen.fill(THEMES[Game.instance.chosen_theme_index])

        draw_game_grid()
        
        camera.update()
        
        stats.update_stats_overlay()
    
    pg.display.update()
        
def draw_game_grid() -> None:
    for game_object in GAME_OBJECTS:
        if game_object.activated:
            game_object.print()
    
    Game.instance.screen.blit(player.surface_scaled, (player.x, player.y))

def init_UI():
    with open("UI_options.json", "r") as UI_options_file:
        UIs = json.load(UI_options_file)
    for instance_name_raw in UIs:
        UIFactory.UI_list[instance_name_raw] = UI(instance_name_raw, UIs[instance_name_raw]["options"])
    
def main():
    global time_elapsed, thread, terminate_thread_event
    thread = None
    terminate_thread_event = threading.Event()
    clock = pg.time.Clock()
    time_elapsed = 0.000000
    total_paused_time = 0
    pause_start_time = 0
    running = True
    while running:
        pg.key.stop_text_input() # Stop text input to allow WASD key to control the sprite
        clock.tick(FPS)
        if UIFactory.activated_UI:
            if pause_start_time == 0:
                pause_start_time = pg.time.get_ticks()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                Game.exit_game()
            if event.type == pg.USEREVENT:
                Game.load_bgm()
            if event.type == pg.KEYDOWN:
                if UIFactory.activated_UI: # if UI is turned on
                    UIFactory.activated_UI[-1].check_action(event)
                else:
                    if event.key == pg.K_ESCAPE:
                        UIFactory.UI_open(UIFactory.get_instance("menu")) # turn on menu UI when it's currently in the main game
            
        if not UIFactory.activated_UI:
            
            if pause_start_time != 0:
                total_paused_time += pg.time.get_ticks() - pause_start_time
                pause_start_time = 0
            player.check_movement()
            player.execute_movement()
        
        time_elapsed = (pg.time.get_ticks() - total_paused_time) / 1000.0
        draw_screen()

if __name__ == "__main__":
    pg.init()
    pgcam.init()
    Game()
    init_UI()
    UIFactory.activated_UI = [UIFactory.get_instance("main_menu")]
    Game.load_bgm()
    main()