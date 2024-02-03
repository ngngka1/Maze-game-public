# Maze-game
### To play the game, launch **MazeMiniGame.bat** 

This is a minigame where player needs to reach the goal (the blue rectangle) of the maze in the shortest time possible while avoiding monsters or traps (monsters/traps WIP)


# Documentation

To increase the difficulty of the game, the following elements are devised and will be added soon:
1. change maze generation algorithm so that multiple paths can lead to the same position
2. set up traps, items etc.

Graphics might be improved in the future too (probably)

manage.py: to automatically install virtualenv for the game <br>
main.py: main game script <br>
dfs.py: to generate maze with depth-first-search algorithm <br>
maze_map.json: to store generated maze_map <br> 
config.toml: store game configuration (screen property, settings etc.) <br>
level_properties.toml: specify the level difficulty etc. of each level <br>
UI_options.json: contains UIs' names and related function names