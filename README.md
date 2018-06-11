# python-playgound

Playground to learn python programming with graphical robotic battle

## Install

Install with PIP 
* pygame

## Create a program

Follow `skeleton.py` to:
* instanciate a map. The parameter is the number of targets in the map.
* instanciate as many robots as you wish with `map.create_robot`
* call `map.start()`

## API

### Robot

#### Properties

`Robot.name`
Robot's name (str)

`Robot.score`
Robot's current score (int)

`Robot.x`
Robot's x position (float)

`Robot.y`
Robot's y position (float)

`Robot.heading`
Robot's heading in rad (float)

`Robot.speed`
Robot's current speed (float)


#### Methods

`Robot.is_moving()`
Returns if robot is currently moving
* return : True/False (boolean)

`Robot.wait()`
Wait for the robot end of movement
* return : nothing

`Robot.translate(distance, speed = 2.0)`
Non-blocking ask the robot to translate (move forward/backward).
* distance : length of translation (float)
* speed (optional) : speed of translation
* return : nothing

`Robot.translate_and_wait(distance, speed = 2.0)`
Blocking ask the robot to translate (move forward/backward).
* distance : length of translation (float)
* speed (optional) : speed of translation
* return : nothing

`Robot.rotate(angle, speed = 8.0)`
Non-blocking ask the robot to rotate
* angle : rotation angle in radians (float)
* speed (optional) : speed of rotation in rad/s (float)
* return : nothing

`Robot.rotate_and_wait(angle, speed = 8.0)`
Blocking ask the robot to rotate
* angle : rotation angle in radians (float)
* speed (optional) : speed of rotation in rad/s (float)
* return : nothing

### Target

#### Properties

`Target.x`
target's x position (float)

`Target.y`
target's y position (float)

`Target.caugth`
does this target have benn caught by another robot (boolean)

### Map

#### Methods

`Map.Map(num_targets)`
Contructor
* num_targets : number of targets to generate in the map (in)
* return : map instance (Map)

`Map.create_robot(name, program, color)`
instanciate a robot and add to map
* name : robot's name (str)
* program : robot's logic callback - see below (function)
* color : robot's color : `Robot.COLOR_RED`, `Robot.COLOR_BLUE`, `Robot.COLOR_ORANGE`, `Robot.COLOR_GREEN`(tuple)
* return : robot instance (Robot)

`Map.start()`
Blocking launch of the GUI. Mandatory to lauch the game. The function exits when the GUI window is closed by user.

#### robot's logic callback

The robot's logic callback must be a function of the following prototype:

```def program_robot(robot, targets)```

This function must be blocking until robot's logic is finished (executed in a thread). The receuved parameters will be:
* robot : robot instance (Robot)
* targets : array of the map target (array of Target)

The function might compute the array of Target, to compute the orders, and call the robot API methods to tell the robot where to go.

## Run 

```python skeleton.py```
