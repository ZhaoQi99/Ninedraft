"""
Classes to represent mobs in the game world, and some useful constants
"""

__author__ = "Benjamin Martin and Paul Haley"
__version__ = "1.1.0"
__date__ = "26/04/2019"
__copyright__ = "The University of Queensland, 2019"

import random
import cmath

from physical_thing import DynamicThing
from random import randint
MOB_DEFAULT_TEMPO = 40

BIRD_GRAVITY_FACTOR = 150
BIRD_X_SCALE = 1.61803

SHEEP_GRAVITY_FACTOR = 30
SHEEP_X_SCALE = 1.4

BEE_X_SCALE = 2.5
BEE_GRAVITY_FACTOR = 180
BEE_ATACK_RATE = 0.2
BEE_SWARM_DISTANCE = 5
BEE_HONEY_DISTANCE = 40


class Mob(DynamicThing):
    """An abstract representation of a creature in the sandbox game

    Can be friend, foe, or neither

    Should not be instantiated directly"""

    def __init__(self, mob_id, size, tempo=MOB_DEFAULT_TEMPO, max_health=20):
        """Constructor

        Parameters:
            mob_id (str): A unique id for this type of mob
            size (tuple<float, float>):
                    The physical (x, y) size of this mob
            tempo (float):
                    The movement tempo of this mob:
                      - zero indicates no movement
                      - further from zero means faster movement
                      - negative is reversed
            max_health (float): The maximum & starting health for this mob
        """
        super().__init__(max_health=max_health)

        self._id = mob_id
        self._size = size
        self._tempo = tempo

        self._steps = 0

    def get_id(self):
        """(str) Returns the unique id for this type of mob"""
        return self._id

    def get_size(self):
        """(str) Returns the physical (x, y) size of this mob"""
        return self._size

    def step(self, time_delta, game_data):
        """Advance this mob by one time step

        See PhysicalThing.step for parameters & return"""
        # Track time via time_delta would be more precise, but a step counter is simpler
        # and works reasonably well, assuming time steps occur at roughly constant time deltas
        self._steps += 1

    def __repr__(self):
        return f"{self.__class__.__name__}({self._id!r})"


class Bird(Mob):
    """A friendly bird, nonchalant with a dash of cheerfulness"""

    def step(self, time_delta, game_data):
        """Advance this bird by one time step

        See PhysicalThing.step for parameters & return"""
        # Every 20 steps; could track time_delta instead to be more precise
        if self._steps % 20 == 0:
            # a random point on a movement circle (radius=tempo), scaled by the percentage
            # of health remaining
            health_percentage = self._health / self._max_health
            z = cmath.rect(self._tempo * health_percentage,
                           random.uniform(0, 2 * cmath.pi))

            # stretch that random point onto an ellipse that is wider on the x-axis
            dx, dy = z.real * BIRD_X_SCALE, z.imag

            x, y = self.get_velocity()
            velocity = x + dx, y + dy - BIRD_GRAVITY_FACTOR

            self.set_velocity(velocity)

        super().step(time_delta, game_data)

    def use(self):
        pass


class Sheep(Mob):
    def step(self, time_delta, game_data):
        """Advance this bird by one time step

        See PhysicalThing.step for parameters & return"""
        # Every 20 steps; could track time_delta instead to be more precise
        if self._steps % 20 == 0:
            # a random point on a movement circle (radius=tempo), scaled by the percentage
            # of health remaining
            health_percentage = self._health / self._max_health
            z = cmath.rect(self._tempo * health_percentage,
                           random.uniform(0, 2 * cmath.pi))

            # stretch that random point onto an ellipse that is wider on the x-axis
            dx, dy = z.real * SHEEP_X_SCALE, z.imag

            x, y = self.get_velocity()
            velocity = x + dx, y + dy - SHEEP_GRAVITY_FACTOR

            self.set_velocity(velocity)

        super().step(time_delta, game_data)

    def use(self):
        pass


class Bee(Mob):
    _max_health = 5

    def __init__(self, mob_id, size, tempo=MOB_DEFAULT_TEMPO, max_health=20):
        super().__init__(mob_id, size, tempo=tempo, max_health=5)

    def step(self, time_delta, game_data, players, honey_blocks):
        if self._steps % 25 == 0:
            if random.random() < BEE_ATACK_RATE:
                player = players[random.randint(0, len(players) - 1)]
                player_x, player_y = player.get_position()
                bee_x, bee_y = self.get_position()
                vx, vy = self.get_velocity()
                if player_x > bee_x:
                    vx = abs(vx) * 1.0
                else:
                    vx = abs(vx) * -1.0
                if player_y > bee_y:
                    vy = abs(vy) * 1.0
                else:
                    vy = abs(vy)*-1.0
                self.set_velocity((vx, vy))
            elif honey_blocks:
                velocity = randint(-BEE_HONEY_DISTANCE,
                                   BEE_HONEY_DISTANCE), randint(-BEE_HONEY_DISTANCE, BEE_HONEY_DISTANCE)
                self.set_velocity(velocity)
            else:
                health_percentage = self._health / self._max_health
                z = cmath.rect(self._tempo * health_percentage,
                               random.uniform(0, 2 * cmath.pi))
                dx, dy = z.real * BEE_X_SCALE, z.imag
                x, y = self.get_velocity()
                velocity = x + dx, y + dy - BEE_GRAVITY_FACTOR
                self.set_velocity(velocity)
        super().step(time_delta, game_data)

    def use(self):
        pass

    def attack(self, successful):
        if successful:
            self._health -= 1
