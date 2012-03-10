# -*- encoding: utf-8 -*-
##
## Copyright (C) 2011 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

from copy import copy

from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner


class Glyph(object):
    def __init__(self, sprite, pos):
        self._sprite = sprite
        self._removed = False

        self.x, self.y = pos


class Text(object):
    def __init__(self, pos, text, front_wrapper, ascii_wrapper):
        self._sprite = Sprite()
        self._anmrunner = ANMRunner(front_wrapper, 22, self._sprite)
        self._anmrunner.run_frame()
        self._removed = False
        self._changed = True

        self.text = ''
        self.glyphes = []

        self.front_wrapper = front_wrapper
        self.ascii_wrapper = ascii_wrapper

        self.x, self.y = pos
        self.set_text(text)


    def objects(self):
        return self.glyphes + [self]


    def set_text(self, text):
        if text == self.text:
            return

        if len(text) > len(self.glyphes):
            ref_sprite = Sprite()
            anm_runner = ANMRunner(self.ascii_wrapper, 0, ref_sprite)
            anm_runner.run_frame()
            ref_sprite.corner_relative_placement = True #TODO: perhaps not right, investigate.
            self.glyphes.extend(Glyph(copy(ref_sprite), (self.x + 14*i, self.y))
                for i in range(len(self.glyphes), len(text)))
        elif len(text) < len(self.glyphes):
            self.glyphes[:] = self.glyphes[:len(text)]

        for glyph, character in zip(self.glyphes, text):
            glyph._sprite.anm, glyph._sprite.texcoords = self.ascii_wrapper.get_sprite(ord(character) - 21)
            glyph._sprite._changed = True

        self.text = text
        self._changed = True


    def update(self):
        if self._changed:
            if self._anmrunner and not self._anmrunner.run_frame():
                self._anmrunner = None
            self._changed = False
