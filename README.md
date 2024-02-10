# Maze-game
### To play the game, launch **MazeMiniGame.bat** 

This is a minigame where player needs to reach the goal (the blue rectangle) of the maze in the shortest time possible while avoiding monsters or traps, with assistance of items (monsters/traps/items WIP)

Use *WASD/arrow* keys to control the player or change options.<br>
Press *enter* if you want to apply an option.<br>
Press *escape* to return to the previous menu/pause the game.


# Documentation

The following elements are devised and will be added soon:
1. change maze generation algorithm so that multiple paths can lead to the same position
2. set up traps, items(which provides temporary debuff/buff like displaying the path to the goal) etc.

Graphics might be improved in the future (probably)
BGMs are from undertale 

manage.py: to automatically install virtualenv for the game <br>
main.py: main game script <br>
dfs.py: to generate maze with depth-first-search algorithm <br>
Astar_search.py: uses A* algorithm to find the path to goal (For more details, refer to my repository: https://github.com/ngngka1/Astar_path_finding)<br>
maze_map.json: to store generated maze_map <br> 
config.toml: store game configuration (screen property, settings etc.) <br>
level_properties.toml: specify the level difficulty etc. of each level <br>
UI_options.json: contains UIs' options and instance(which will be created in runtime)