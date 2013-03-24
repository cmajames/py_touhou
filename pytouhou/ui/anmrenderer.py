#!/usr/bin/env python
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

import pyglet
import traceback

from pyglet.gl import (glMatrixMode, glEnable,
                       glHint, glEnableClientState, glViewport,
                       glLoadMatrixf, GL_PROJECTION, GL_MODELVIEW,
                       GL_TEXTURE_2D, GL_BLEND,
                       GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST,
                       GL_COLOR_ARRAY, GL_VERTEX_ARRAY, GL_TEXTURE_COORD_ARRAY,
                       glClearColor, glClear, GL_COLOR_BUFFER_BIT,
                       glGenBuffers)

from pytouhou.game.sprite import Sprite
from pytouhou.vm.anmrunner import ANMRunner

from pytouhou.utils.helpers import get_logger

from .renderer import Renderer
from .shaders.eosd import GameShader

from ctypes import c_uint


logger = get_logger(__name__)


class ANMRenderer(pyglet.window.Window, Renderer):
    def __init__(self, resource_loader, anm_wrapper, index=0, sprites=False,
                 fixed_pipeline=False):
        Renderer.__init__(self, resource_loader)
        self.texture_manager.preload(resource_loader.instanced_anms.values())

        width, height = 384, 448
        pyglet.window.Window.__init__(self, width=width, height=height,
                                      caption='PyTouhou', resizable=False)

        self.use_fixed_pipeline = fixed_pipeline

        self._anm_wrapper = anm_wrapper
        self.sprites = sprites
        self.clear_color = (0., 0., 0., 1.)
        self.force_allow_dest_offset = False
        self.index_items()
        self.load(index)
        self.objects = [self]

        self.x = width / 2
        self.y = height / 2


    def start(self, width=384, height=448):
        if (width, height) != (self.width, self.height):
            self.set_size(width, height)

        # Initialize OpenGL
        glEnable(GL_BLEND)
        if self.use_fixed_pipeline:
            glEnable(GL_TEXTURE_2D)
            glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
            glEnableClientState(GL_COLOR_ARRAY)
            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        # Switch to game projection
        proj = self.perspective(30, float(self.width) / float(self.height),
                                101010101./2010101., 101010101./10101.)
        view = self.setup_camera(0, 0, 1)

        if not self.use_fixed_pipeline:
            shader = GameShader()

            vbo_array = (c_uint * 1)()
            glGenBuffers(1, vbo_array)
            self.vbo, = vbo_array

            mvp = view * proj
            shader.bind()
            shader.uniform_matrixf('mvp', mvp.get_c_data())
        else:
            glMatrixMode(GL_PROJECTION)
            glLoadMatrixf(proj.get_c_data())

            glMatrixMode(GL_MODELVIEW)
            glLoadMatrixf(view.get_c_data())

        # Use our own loop to ensure 60 fps
        pyglet.clock.set_fps_limit(60)
        while not self.has_exit:
            pyglet.clock.tick()
            self.dispatch_events()
            self.update()
            self.flip()


    def on_resize(self, width, height):
        glViewport(0, 0, width, height)


    def _event_text_symbol(self, ev):
        # XXX: Ugly workaround to a pyglet bug on X11
        #TODO: fix that bug in pyglet
        try:
            return pyglet.window.Window._event_text_symbol(self, ev)
        except Exception as exc:
            logger.warn('Pyglet error: %s', traceback.format_exc(exc))
            return None, None


    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.has_exit = True
        elif symbol == pyglet.window.key.W:
            self.load()
        elif symbol == pyglet.window.key.X:
            self.x, self.y = {(192, 224): (0, 0),
                              (0, 0): (-224, 0),
                              (-224, 0): (192, 224)}[(self.x, self.y)]
        elif symbol == pyglet.window.key.C:
            self.force_allow_dest_offset = not self.force_allow_dest_offset
            self.load()
        elif symbol == pyglet.window.key.LEFT:
            self.change(-1)
        elif symbol == pyglet.window.key.RIGHT:
            self.change(+1)
        elif symbol == pyglet.window.key.TAB:
            self.toggle_sprites()
        elif symbol == pyglet.window.key.SPACE:
            self.toggle_clear_color()
        elif symbol >= pyglet.window.key.F1 and symbol <= pyglet.window.key.F12:
            interrupt = symbol - pyglet.window.key.F1 + 1
            if modifiers & pyglet.window.key.MOD_SHIFT:
                interrupt += 12
            if not self.sprites:
                self.anmrunner.interrupt(interrupt)


    def load(self, index=None):
        if index is None:
            index = self.num
        self.sprite = Sprite()
        if self.sprites:
            self.sprite.anm, self.sprite.texcoords = self._anm_wrapper.get_sprite(index)
            print('Loaded sprite %d' % index)
        else:
            self.anmrunner = ANMRunner(self._anm_wrapper, index, self.sprite)
            print('Loading anim %d, handled events: %r' % (index, self.anmrunner.script.interrupts.keys()))
        self.num = index


    def change(self, diff):
        keys = self.items.keys()
        keys.sort()
        index = (keys.index(self.num) + diff) % len(keys)
        item = keys[index]
        self.load(item)


    def index_items(self):
        self.items = {}
        if self.sprites:
            self.items = self._anm_wrapper.sprites
        else:
            self.items = self._anm_wrapper.scripts


    def toggle_sprites(self):
        self.sprites = not(self.sprites)
        self.index_items()
        self.load(0)


    def toggle_clear_color(self):
        if self.clear_color[0] == 0.:
            self.clear_color = (1., 1., 1., 1.)
        else:
            self.clear_color = (0., 0., 0., 1.)


    def update(self):
        if not self.sprites:
             self.anmrunner.run_frame()

        if self.force_allow_dest_offset:
            self.sprite.allow_dest_offset = True

        glClearColor(*self.clear_color)
        glClear(GL_COLOR_BUFFER_BIT)
        if not self.sprite.removed:
            self.render_elements([self])

