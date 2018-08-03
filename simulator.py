import pygame
import sys
import os
import math
import threading
import traceback
import subprocess
import re
import time
import random
from threading import Thread, Event

global lock
lock = threading.Lock()


#Initilaizing all pygame imported module
pygame.init()

class Display():
    
    SCALE_FACTOR    = 300.0
    BORDER_M        = 0.2
    BORDER_PX       = (int)(BORDER_M * SCALE_FACTOR)
    ROBOT_WIDTH_M   = 0.25
    ROBOT_WIDTH_PX  = (int)(ROBOT_WIDTH_M * SCALE_FACTOR)
    ROBOT_HEIGHT_M  = 0.2
    ROBOT_HEIGHT_PX = (int)(ROBOT_HEIGHT_M * SCALE_FACTOR)
    
    def __init__(self, width, height):
        self._width = width
        self._height = height
        WIDTH_PX = (int)(width * self.SCALE_FACTOR) + (2 * self.BORDER_PX)
        HEIGHT_PX = (int)(height * self.SCALE_FACTOR) + (2 * self.BORDER_PX)
        self.screen = pygame.display.set_mode((WIDTH_PX, HEIGHT_PX))

    def display_grid(self):

        w, h = self.screen.get_size()

        # Draw grid
        for i in range(12):
            if (i == 11):
                width = 3
            else:
                width = 1
                
            pygame.draw.line(self.screen, (150, 150, 150), (0, int(h*0.083333*i)), (w-1, int(h*0.083333*i)), width)

        for i in range(18):
            if (i == 9):
                width = 3
            else:
                width = 1

            pygame.draw.line(self.screen, (150, 150, 150), (int(w*0.0555*i), 0), (int(w*0.0555*i), h-1), width)

    def draw_robot(self, x, y, heading, color, score_text):
    
        diagonal = math.sqrt((float)(self.ROBOT_WIDTH_PX * self.ROBOT_WIDTH_PX + self.ROBOT_HEIGHT_PX * self.ROBOT_HEIGHT_PX))
        diagonal_2 = diagonal / 2.0
        alpha = math.atan(float(self.ROBOT_WIDTH_PX) / float(self.ROBOT_HEIGHT_PX))

        x1 = x + int(diagonal_2 * math.cos(heading + alpha))
        y1 = y + int(diagonal_2 * math.sin(heading + alpha))
        x2 = x + int(diagonal_2 * math.cos(heading - alpha))
        y2 = y + int(diagonal_2 * math.sin(heading - alpha))
        x3 = x + x - x1
        y3 = y + y - y1
        x4 = x + x - x2
        y4 = y + y - y2

        pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 3)
        pygame.draw.line(self.screen, color, (x2, y2), (x3, y3), 3)
        pygame.draw.line(self.screen, color, (x3, y3), (x4, y4), 3)
        pygame.draw.line(self.screen, color, (x4, y4), (x1, y1), 3)
        pygame.draw.line(self.screen, color, (x3, y3), (x,  y),  3)
        pygame.draw.line(self.screen, color, (x4, y4), (x,  y),  3)

        font = pygame.font.SysFont("Arial", 15)

        # render text
        self.screen.blit(font.render(score_text, 1, color), (x, y))

    def update(self, robots, targets):

        self.screen.fill((0, 0, 0))
        self.display_grid()

        for robot in robots:
            y_pix = int((self._height - robot.y) * self.SCALE_FACTOR) + self.BORDER_PX
            x_pix = int(((self._width / 2.0) + robot.x) * self.SCALE_FACTOR) + self.BORDER_PX
            self.draw_robot(x_pix, y_pix, -robot.heading, robot.color, '{} : {}'.format(robot.name, robot.score))

        for target in targets:
            y_pix = int((self._height - target.y) * self.SCALE_FACTOR) + self.BORDER_PX
            x_pix = int(((self._width / 2.0) + target.x) * self.SCALE_FACTOR) + self.BORDER_PX
            pygame.draw.circle(self.screen, target.color, (x_pix, y_pix), 12, 3)
            font = pygame.font.SysFont("Arial", 16)

        pygame.display.update()
        pygame.display.flip()

    def display_winners(self, winners, robots):

        message = winners[0].name
        if len(winners) > 1:
            for winner in winners[1:]:
                message = message + ' and ' + winner.name
            message = message + ' win !'
        else:
            message = message + ' wins !'

        self.screen.fill((0, 0, 0))
        self.display_grid()
        
        font = pygame.font.SysFont("Arial", 60)
        font_score = pygame.font.SysFont("Arial", 30)

        # render text
        y = int((self._height / 2) * self.SCALE_FACTOR) + self.BORDER_PX
        x = 200
        self.screen.blit(font.render(message, 1, (255, 255, 255)), (x, y))

        count = 0
        for robot in robots:
            y = int((self._height / 2) * self.SCALE_FACTOR) + self.BORDER_PX + 80 + count * 50
            x = 200
            self.screen.blit(font_score.render('{} : {} pts'.format(robot.name, robot.score), 1, robot.color), (x, y))
            count += 1

        pygame.display.update()
        pygame.display.flip()


class Robot(Thread):


    COLOR_WHITE  = (255, 255, 255)
    COLOR_RED    = (229, 32,  57)
    COLOR_ORANGE = (255, 154, 4)
    COLOR_BLUE   = (0,   162, 232)
    COLOR_GREEN  = (102, 177, 33)

    ANGULAR_TIME_CONSTANT = 0.2
    ANGULAR_STATIC_GAIN = 1.0
    ANGULAR_POSITION_CONTROL_GAIN = 1.5
    ANGULAR_MAX_SPEED = 8.0
    ANGULAR_THRESHOLD = 0.01

    LONGITUDINAL_TIME_CONSTANT = 0.3
    LONGITUDINAL_STATIC_GAIN = 1.0
    LONGITUDINAL_POSITION_CONTROL_GAIN = 1.1
    LONGITUDINAL_MAX_SPEED = 2.0
    LONGITUDINAL_THRESHOLD = 0.01

    def __init__(self, name, program, color, period = 0.05):

        Thread.__init__(self)

        self._name = name
        self._color = color
        self._program = program

        self._longitudinal_command = 0.0
        self._longitudinal_speed = 0.0
        self._longitudinal_position = 0.0
        self._longitudinal_position_setpoint = 0.0
        self._longitudinal_max_speed = self.LONGITUDINAL_MAX_SPEED
        self._longitudinal_position_control = False

        self._angular_command = 0.0
        self._angular_speed = 0.0
        self._angular_position = 0.0
        self._angular_position_setpoint = 0.0
        self._angular_max_speed = self.ANGULAR_MAX_SPEED
        self._angular_position_control = False

        self._x = 0.0
        self._y = 0.0
        self._heading = 0.0

        self._period = period

        self._score = 0

        self._running = False

    def _mod2pi(self, angle):
        while angle > (2.0 * math.pi):
            angle = angle - (2.0 * math.pi)
        while angle < 0.0:
            angle = angle + (2.0 * math.pi)
        return angle

    def _run_angular(self):
        coeff = self.ANGULAR_TIME_CONSTANT / (self.ANGULAR_TIME_CONSTANT + self._period)
        old_position = self._angular_position
        self._angular_speed = ((1.0 - coeff) * self._angular_command * self.ANGULAR_STATIC_GAIN) + (coeff * self._angular_speed)
        self._angular_position = self._angular_position + (self._angular_speed * self._period)
        return self._angular_position - old_position

    def _run_longitudinal(self):
        coeff = self.LONGITUDINAL_TIME_CONSTANT / (self.LONGITUDINAL_TIME_CONSTANT + self._period)
        old_position = self._longitudinal_position
        self._longitudinal_speed = (1.0 - coeff) * self._longitudinal_command * self.LONGITUDINAL_STATIC_GAIN + coeff * self._longitudinal_speed
        self._longitudinal_position = self._longitudinal_position + (self._longitudinal_speed * self._period)
        return self._longitudinal_position - old_position

    def _run_cartesian(self, delta_longitudinal):
        self._heading = self._mod2pi(self._angular_position)
        self._x = self._x + (delta_longitudinal * math.cos(self._heading))
        self._y = self._y + (delta_longitudinal * math.sin(self._heading))

    def run(self):
        try:
            self._program(self, self._targets)
        except Exception as e:
            print "{} program exited ({})".format(self._name, e.message)

    def step(self):

        if self._angular_position_control:
            self._angular_command = self.ANGULAR_POSITION_CONTROL_GAIN * (self._angular_position_setpoint - self._angular_position)
            if (self._angular_command > self._angular_max_speed):
                self._angular_command = self._angular_max_speed
            if (self._angular_command < -self._angular_max_speed):
                self._angular_command = -self._angular_max_speed

        if self._longitudinal_position_control:
            self._longitudinal_command = self.LONGITUDINAL_POSITION_CONTROL_GAIN * (self._longitudinal_position_setpoint - self._longitudinal_position)
            if (self._longitudinal_command > self._longitudinal_max_speed):
                self._longitudinal_command = self._longitudinal_max_speed
            if (self._longitudinal_command < - self._longitudinal_max_speed):
                self._longitudinal_command = -self._longitudinal_max_speed

        self._run_angular()
        delta_longitudinal = self._run_longitudinal()
        self._run_cartesian(delta_longitudinal)

    def add_score(self):
        self._score = self._score + 1

    @property
    def name(self):
        return self._name

    @property
    def color(self):
        return self._color

    @property
    def score(self):
        return self._score

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def heading(self):
        return self._heading

    @property
    def speed(self):
        return self._longitudinal_speed

    def is_moving(self):
        lock.acquire()
        if (math.fabs(self._angular_command) > Robot.ANGULAR_THRESHOLD) or (math.fabs(self._longitudinal_command) > Robot.LONGITUDINAL_THRESHOLD):
            lock.release()
            return True
        else:
            lock.release()
            return False

    def wait(self):
        time.sleep(2.0 * self._period)
        while self.is_moving():
            self.wait_sec(self._period)

    def set_speeds(self, longitudinal, angular):
        lock.acquire()
        self._longitudinal_command = longitudinal if longitudinal < Robot.LONGITUDINAL_MAX_SPEED else Robot.LONGITUDINAL_MAX_SPEED
        self._longitudinal_position_setpoint = 0.0
        self._longitudinal_max_speed = self._longitudinal_command
        self._longitudinal_position_control = False
        self._angular_command = angular if angular < Robot.ANGULAR_MAX_SPEED else Robot.ANGULAR_MAX_SPEED
        self._angular_max_speed = self._angular_command
        self._angular_position_setpoint = 0.0
        self._angular_position_control = False
        lock.release()

    def translate(self, distance, speed = 2.0):
        lock.acquire()
        self._longitudinal_command = 0.0
        self._longitudinal_position_setpoint = self._longitudinal_position + distance
        self._longitudinal_max_speed = speed if speed < Robot.LONGITUDINAL_MAX_SPEED else Robot.LONGITUDINAL_MAX_SPEED
        self._longitudinal_position_control = True
        self._angular_command = 0.0
        self._angular_max_speed = self.ANGULAR_MAX_SPEED
        self._angular_position_setpoint = 0.0
        self._angular_position_control = False
        lock.release()

    def rotate(self, angle, speed = 8.0):
        lock.acquire()
        self._longitudinal_command = 0.0
        self._longitudinal_position_setpoint = 0.0
        self._longitudinal_max_speed = Robot.LONGITUDINAL_MAX_SPEED
        self._longitudinal_position_control = False
        self._angular_command = 0.0
        self._angular_max_speed = speed if speed < Robot.ANGULAR_MAX_SPEED else Robot.ANGULAR_MAX_SPEED
        self._angular_position_setpoint = self._angular_position + angle
        self._angular_position_control = True
        lock.release()

    def translate_and_wait(self, distance, speed = 2.0):
        self.translate(distance, speed)
        self.wait()

    def rotate_and_wait(self, angle, speed = 8.0):
        self.rotate(angle, speed)
        self.wait()

    def wait_sec(self, duration):
        while duration > 0.0:
            lock.acquire()
            running = self._running
            lock.release()
            if running == False:
                raise Exception("Execution stopped by user")
            time.sleep(0.1)
            duration = duration - 0.1

    def start(self, targets):
        self._running = True
        self._targets = targets
        Thread.start(self)

    def stop(self):
        self._running = False

class Target():

    def __init__(self, width, height):
        random.seed()
        self._x = (random.random() - 0.5) * width
        self._y = random.random() * height
        self._color = Robot.COLOR_WHITE
        self._caught = False

    def catch(self, color):
        if self._caught == False:
            self._caught = True
            self._color = color

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def caugth(self):
        return self._caught

    @property
    def color(self):
        return self._color

class Map:

    MAP_PERIOD = 0.05
    MAP_WIDTH  = 3.2
    MAP_HEIGHT = 2.0
    MAP_CATCH_THRESHOLD = 0.05

    def __init__(self, num_targets):
        self._robots = []
        self._display = Display(self.MAP_WIDTH, self.MAP_HEIGHT)
        self._targets = []
        for _ in range(num_targets):
            self._targets.append(Target(self.MAP_WIDTH, self.MAP_HEIGHT))

    def create_robot(self, name, program, color):
        robot = Robot(name, program, color, self.MAP_PERIOD)
        lock.acquire()
        self._robots.append(robot)
        lock.release()
        return robot

    def distance(self, robot, target):
        return math.sqrt((robot.x - target.x) * (robot.x - target.x) + 
                         (robot.y - target.y) * (robot.y - target.y))
    
    def check_catch(self, robot, target):
        if target.caugth == False:
            if self.distance(robot, target) < self.MAP_CATCH_THRESHOLD:
                target.catch(robot._color)
                robot.add_score()

    def remaining_targets(self):
        remaining = 0
        for target in self._targets:
            if target.caugth == False:
                remaining = remaining + 1
        return remaining 

    def find_winners(self):
        winners = []
        best_score = 1
        for robot in self._robots:
            if robot.score > best_score:
                winners = [robot]
                best_score = robot.score
            elif robot.score == best_score:
                winners.append(robot)
        return winners

    def run(self):
        try:
            while self._running:

                lock.acquire()

                for robot in self._robots:
                    robot.step()
                    for target in self._targets:
                        self.check_catch(robot, target)

                if self.remaining_targets() == 0 and len(self._targets) > 0:
                    winners = self.find_winners()
                    self._display.display_winners(winners, self._robots)
                else:
                    self._display.update(self._robots, self._targets)

                lock.release()
                event = pygame.event.poll()
                if event.type == pygame.QUIT:
                    pygame.quit()
                    self.stop()
                time.sleep(self.MAP_PERIOD)
        except Exception as e: 
            print(e)
            traceback.print_exc()
            pygame.quit()
            self.stop()

    def start(self):
        self._running = True
        for robot in self._robots:
            robot.start(self._targets)
        self.run()

    def stop(self):
        self._running = False
        for robot in self._robots:
            robot.stop()
