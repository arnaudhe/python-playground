from simulator import Map, Robot
import math
from datetime import datetime

def distance(robot, target):
    return math.sqrt((robot.x - target.x) ** 2 + (robot.y - target.y) ** 2)

def distance_point(target, x, y):
    return math.sqrt((x - target.x) ** 2 + (y - target.y) ** 2)

def mod2pi(angle):
    while angle > math.pi:
        angle = angle - (2.0 * math.pi)
    while angle < -math.pi:
        angle = angle + (2.0 * math.pi)
    return angle

def delta_heading(robot, target):
    return mod2pi(math.atan2(target.y - robot.y, target.x - robot.x) - robot.heading)

def delta_heading_point(target, x, y, heading):
    return mod2pi(math.atan2(target.y - y, target.x - x) - heading)

def get_next_target(robot, targets):
    min_target = None
    min_cost = 100000.0
    for target in targets:
        if not target.caugth:
            cost_distance = 1.0 * distance_point(target, robot.x, robot.y)
            cost_angle = 1.1 * math.fabs(delta_heading_point(target, robot.x, robot.y, robot.heading))
            cost = cost_distance + cost_angle
            target.set_costs(cost_distance, cost_angle)
            if cost < min_cost:
                min_cost = cost
                min_target = target
    return min_target

def program_robot(robot, targets):
    # Start of robot logic
    target = get_next_target(robot, targets)
    while target != None:
        if distance(robot, target) <= 0.2:
            print 'Cible proche : rotation'
            robot.rotate_and_wait(delta_heading(robot, target))
        while math.fabs(delta_heading(robot, target)) > (math.pi / 4.0):
            robot.rotate(delta_heading(robot, target))
            robot.wait_sec(0.1)
            print 'Cible non-alignee : rotation'
        while distance(robot, target) > 0.2:
            print 'En cours'
            angular = 2.0 * delta_heading(robot, target)
            longitudinal = 1.5 * distance(robot, target)
            robot.set_speeds(longitudinal, angular)
            robot.wait_sec(0.1)
        while distance(robot, target) > 0.05:
            print 'Approche'
            next_target = get_next_target(robot, targets)
            angular = 2.0 * delta_heading(robot, target)
            if math.fabs(delta_heading(robot, next_target)) > (math.pi / 4.0):
                longitudinal = 1.5 * distance(robot, target)
            robot.set_speeds(longitudinal, angular)
            robot.wait_sec(0.1)
        target = get_next_target(robot, targets)
    # End of robot logic

def program_labourde(robot, targets):
    # Start of robot logic
    for target in reversed(targets):
        robot.rotate_and_wait(delta_heading(robot, target))
        robot.translate_and_wait(distance(robot, target))
    # End of robot logic

map = Map(50)
chacha = map.create_robot('Chacha', program_robot, Robot.COLOR_BLUE)
la_bourde = map.create_robot('La bourde', program_labourde, Robot.COLOR_RED)
map.start()