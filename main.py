import pygame as pg
import pygame.camera as pgcam
import dfs
import toml
import sys
import json
import math

class Game:
    def __init__(self, level=1) -> None:
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pg.display.set_caption("Maze minigame")
        self.level = level
        self.camera_size = 0
        self.get_level_properties()
        
        
    def get_level_properties(self) -> None:
        global wall, goal, sprite, camera, overlay
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

        wall = Wall(self.grid_width, self.grid_height)
        goal = Goal(self.grid_width, self.grid_height)
        sprite = Sprite(self.grid_width / 2, self.grid_height / 2)
        camera = Camera(self.camera_size)
        overlay = UI()
        
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
        
class UI:
    def __init__(self) -> None:
        self.activated = True
        self.text_box_color_unchosen = (100, 100, 100)
        self.text_box_color_chosen = (0, 0, 0)
        self.text_color = (255, 255, 255)
        self.FONT = pg.font.Font(FONT_FILE_PATH, 50) ## 
        self.text_box_rects = [] ## 
        self.text_surfaces = [] ##
        self.chosen_index = 0
        self.overlay_actions = []
        self.get_overlay_options()
        
    def get_overlay_options(self):
        txt_surface_continue = self.FONT.render("Continue", True, self.text_color)
        txt_surface_settings = self.FONT.render("Settings", True, self.text_color)
        txt_surface_exit = self.FONT.render("Exit", True, self.text_color)
        self.overlay_actions.append(self.switch_UI)
        self.overlay_actions.append(self.switch_UI) ## Setting menu is not done yet, so it quits menu for now
        self.overlay_actions.append(exit_game)
        self.text_surfaces.append(txt_surface_continue)
        self.text_surfaces.append(txt_surface_settings)
        self.text_surfaces.append(txt_surface_exit)
        self.text_box_rects.append(txt_surface_continue.get_rect(center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))) ##
        self.text_box_rects.append(txt_surface_settings.get_rect(center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))) ## 
        self.text_box_rects.append(txt_surface_exit.get_rect(center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))) ##
        
    def change_option(self, value):
        self.chosen_index = ((self.chosen_index + value) % 3) & 3
        #1111 (-1)
        #0000 (0)
        #0001 (1)
        #0010 (2)
        
        #0011 (3)
        
    def check_action(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_RETURN:
                self.execute_action(self.chosen_index)
            elif event.key == pg.K_UP:
                overlay.change_option(-1)
            elif event.key == pg.K_DOWN:
                overlay.change_option(1)
                
    def execute_action(self, i):
        self.overlay_actions[i]()
        
    def switch_UI(self) -> None:
        self.activated = not self.activated
        
    def update_UI(self) -> None:
        for i in range(len(self.text_box_rects)):
            if i == self.chosen_index:
                rect_color = self.text_box_color_chosen
            else:
                rect_color = self.text_box_color_unchosen
            pg.draw.rect(game_obj.screen, rect_color, self.text_box_rects[i], 0, 3)
            game_obj.screen.blit(self.text_surfaces[i], self.text_box_rects[i])
        
        
        
        

def draw_screen() -> None:

    if overlay.activated:
        overlay.update_UI()
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
                    overlay.switch_UI()
            if overlay.activated:
                sprite.freeze() # freeze is needed as sprite.check_movement stops the sprite only when it detects KEYUP
                overlay.check_action(event)
            else:
                sprite.check_movement(event)
        sprite.execute_movement()
            
        draw_screen()
                
def init_game() -> None:
    global game_obj
    game_obj = Game()
    overlay.activated = False
        
def init_config() -> None:
    global FPS, SCREEN_WIDTH, SCREEN_HEIGHT, PATH_TO_SPRITE, bg_color, FONT_FILE_PATH, FONT
    config = toml.load("config.toml")
    FPS = config["fps"]
    SCREEN_WIDTH = config["screen_width"]
    SCREEN_HEIGHT = config["screen_height"]
    bg_color = config["default_background_color"]
    PATH_TO_SPRITE = config["sprite"]["path"]
    # Font
    pg.font.init()
    FONT_FILE_PATH = config["font"]["path"]
    
    
    
if __name__ == "__main__":
    global camera
    pg.init()
    pgcam.init()
    init_config()
    init_game()
    main()