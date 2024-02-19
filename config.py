import toml
import pygame as pg

config = toml.load("config.toml")

# Main game
FPS = config["fps"]
SCREEN_WIDTH = config["screen_width"]
SCREEN_HEIGHT = config["screen_height"]
THEMES = config["themes"]

# Player
PATHS_TO_SPRITES = config["player"]["paths"]
PLAYER_DEFAULT_HP = config["player"]["HP"]

# Items
PATH_TO_ITEM = config["items"]["path"]

# Font
pg.font.init()
FONT_FILE_PATH = config["font"]["path"]
FONT = pg.font.Font(FONT_FILE_PATH, 50) 

# BGMs
BGM = config["bgm"]["paths"]

# Level properties
LEVEL_PROPERTIES = toml.load("LevelProperties.toml")