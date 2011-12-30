# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Thibaut Girka <thib@sitedethib.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##


from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner
from pytouhou.game.bullettype import BulletType

from math import pi


class PlayerState(object):
    def __init__(self, character=0, score=0, power=0, lives=0, bombs=0):
        self.character = character # ReimuA/ReimuB/MarisaA/MarisaB/...

        self.score = score
        self.lives = lives
        self.bombs = bombs
        self.power = power

        self.graze = 0
        self.points = 0

        self.x = 192.0
        self.y = 384.0

        self.invulnerable_time = 240
        self.touchable = True
        self.focused = False

        self.power_bonus = 0 # Never goes over 30.


class Player(object):
    def __init__(self, state, game, anm_wrapper, hitbox_size=2.5, graze_hitbox_size=42., speeds=None):
        self._sprite = None
        self._anmrunner = None
        self._game = game
        self.anm_wrapper = anm_wrapper

        self.speeds = speeds

        self.hitbox_size = hitbox_size
        self.hitbox_half_size = self.hitbox_size / 2.
        self.graze_hitbox_size = graze_hitbox_size
        self.graze_hitbox_half_size = self.graze_hitbox_size / 2.

        self.bullet_type = BulletType(anm_wrapper, 64, 96, 0, 0, 0, hitbox_size=4)
        self.bullet_launch_interval = 5
        self.bullet_speed = 12.
        self.bullet_launch_angle = -pi/2
        self.fire_time = 0

        self.state = state
        self.direction = None

        self.set_anim(0)

        self.death_time = 0


    @property
    def x(self):
        return self.state.x


    @property
    def y(self):
        return self.state.y


    def objects(self):
        return []


    def set_anim(self, index):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(self.anm_wrapper, index, self._sprite)
        self._anmrunner.run_frame()


    def collide(self):
        if not self.state.invulnerable_time and not self.death_time and self.state.touchable: # Border Between Life and Death
            self.death_time = self._game.frame
            self._game.new_death((self.state.x, self.state.y), 2)
            self._game.modify_difficulty(-1600)
            for i in range(16):
                self._game.new_particle((self.state.x, self.state.y), 2, 4., 256) #TODO: find the real size and range.


    def start_focusing(self):
        self.state.focused = True


    def stop_focusing(self):
        self.state.focused = False


    def update(self, keystate):
        if self.death_time == 0 or self._game.frame - self.death_time > 60:
            speed, diag_speed = self.speeds[2:] if self.state.focused else self.speeds[:2]
            try:
                dx, dy = {16: (0.0, -speed), 32: (0.0, speed), 64: (-speed, 0.0), 128: (speed, 0.0),
                          16|64: (-diag_speed, -diag_speed), 16|128: (diag_speed, -diag_speed),
                          32|64: (-diag_speed, diag_speed), 32|128:  (diag_speed, diag_speed)}[keystate & (16|32|64|128)]
            except KeyError:
                dx, dy = 0.0, 0.0

            if dx < 0 and self.direction != -1:
                self.set_anim(1)
                self.direction = -1
            elif dx > 0 and self.direction != +1:
                self.set_anim(3)
                self.direction = +1
            elif dx == 0 and self.direction is not None:
                self.set_anim({-1: 2, +1: 4}[self.direction])
                self.direction = None

            self.state.x += dx
            self.state.y += dy

            if not self.state.focused and keystate & 4:
                self.start_focusing()
            elif self.state.focused and not keystate & 4:
                self.stop_focusing()

            if self.state.invulnerable_time > 0:
                self.state.invulnerable_time -= 1

                m = self.state.invulnerable_time % 8
                if m == 0:
                    self._sprite.color = (255, 255, 255)
                    self._sprite._changed = True
                elif m == 2:
                    self._sprite.color = (64, 64, 64)
                    self._sprite._changed = True

            if keystate & 1 and self.fire_time == 0:
                self.fire_time = 30
            if self.fire_time > 0:
                self.fire()
                self.fire_time -= 1

        if self.death_time:
            time = self._game.frame - self.death_time
            if time == 6: # too late, you are dead :(
                self.state.touchable = False
                self.state.lives -= 1
                if self.state.power > 16:
                    self.state.power -= 16
                else:
                    self.state.power = 0

                self._game.drop_bonus(self.state.x, self.state.y, 2,
                                      end_pos=(self._game.prng.rand_double() * 288 + 48, # 102h.exe@0x41f3dc
                                               self._game.prng.rand_double() * 192 - 64))        # @0x41f3
                for i in range(5):
                    self._game.drop_bonus(self.state.x, self.state.y, 0,
                                          end_pos=(self._game.prng.rand_double() * 288 + 48,
                                                   self._game.prng.rand_double() * 192 - 64))

            elif time == 7:
                self._sprite.mirrored = False
                self._sprite.blendfunc = 0
                self._sprite.rescale = 0.75, 1.5
                self._sprite.fade(26, 96, lambda x: x)
                self._sprite.scale_in(26, 0.00, 2.5, lambda x: x)

            elif time == 32:
                self.state.x = float(self._game.width) / 2. #TODO
                self.state.y = float(self._game.width) #TODO
                self.direction = None

                self._sprite = Sprite()
                self._anmrunner = ANMRunner(self.anm_wrapper, 0, self._sprite)
                self._sprite.alpha = 128
                self._sprite.rescale = 0.0, 2.5
                self._sprite.fade(30, 255, lambda x: x)
                self._sprite.blendfunc = 1
                self._sprite.scale_in(30, 1., 1., lambda x: x)
                self._anmrunner.run_frame()

            elif time == 61: # respawned
                self.state.touchable = True
                self.state.invulnerable_time = 240
                self._sprite.blendfunc = 0
                self._sprite._changed = True

            if time > 30:
                for bullet in self._game.bullets:
                    bullet.cancel()

            if time > 90: # start the bullet hell again
                self.death_time = 0

        self._anmrunner.run_frame()

