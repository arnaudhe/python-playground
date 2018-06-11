from simulator import Map, Robot
import math

def program_robot(robot, targets):
    # Start of robot logic
    robot.rotate_and_wait(1.0)
    robot.translate_and_wait(1.0)
    # End of robot logic

map = Map(1)
chacha = map.create_robot('R2D2', program_robot, Robot.COLOR_BLUE)
map.start()