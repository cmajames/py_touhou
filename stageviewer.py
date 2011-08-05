#!/usr/bin/env python

import sys
import os

import struct
from math import degrees, radians
from io import BytesIO
from itertools import chain

import pygame

from pytouhou.formats.pbg3 import PBG3
from pytouhou.game.background import Background

import OpenGL
OpenGL.FORWARD_COMPATIBLE_ONLY = True
from OpenGL.GL import *
from OpenGL.GLU import *


def load_texture(image, alpha_image=None):
    #TODO: move elsewhere
    textureSurface = pygame.image.load(image).convert_alpha()

    if alpha_image:
        alphaSurface = pygame.image.load(alpha_image)
        assert textureSurface.get_size() == alphaSurface.get_size()
        for x in range(alphaSurface.get_width()):
            for y in range(alphaSurface.get_height()):
                r, g, b, a = textureSurface.get_at((x, y))
                color2 = alphaSurface.get_at((x, y))
                textureSurface.set_at((x, y), (r, g, b, color2[0]))

    textureData = pygame.image.tostring(textureSurface, 'RGBA', 1)

    width = textureSurface.get_width()
    height = textureSurface.get_height()

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA,
        GL_UNSIGNED_BYTE, textureData)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

    return texture, width, height


def main(path, stage_num):
    # Initialize pygame
    pygame.init()
    window = pygame.display.set_mode((384, 448), pygame.OPENGL | pygame.DOUBLEBUF)

    # Initialize OpenGL
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(30, float(window.get_width())/window.get_height(), 101010101./2010101., 101010101./10101.)

    glHint(GL_FOG_HINT, GL_NICEST)
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_FOG)
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    # Load data
    with open(path, 'rb') as file:
        archive = PBG3.read(file)
        background = Background(archive, stage_num)

    texture = load_texture(*background.texture_components)

    print(background.stage.name)

    frame = 0

    # Main loop
    clock = pygame.time.Clock()
    while True:
        # Check events
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and event.mod & pygame.KMOD_ALT:
                    pygame.display.toggle_fullscreen()

        # Update game
        background.update(frame)

        # Draw everything
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glVertexPointer(3, GL_FLOAT, 0, background._vertices)
        glTexCoordPointer(2, GL_FLOAT, 0, background._uvs)

        fog_b, fog_g, fog_r, _, fog_start, fog_end = background.fog_interpolator.values
        x, y, z = background.position_interpolator.values
        unknownx, dy, dz = background.position2_interpolator.values

        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, fog_start)
        glFogf(GL_FOG_END,  fog_end)
        glFogfv(GL_FOG_COLOR, (fog_r / 255., fog_g / 255., fog_b / 255., 1.))

        #TODO
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Some explanations on the magic constants:
        # 192. = 384. / 2. = width / 2.
        # 224. = 448. / 2. = height / 2.
        # 835.979370 = 224./math.tan(math.radians(15)) = (height/2.)/math.tan(math.radians(fov/2))
        # This is so that objects on the (O, x, y) plane use pixel coordinates
        gluLookAt(192., 224., - 835.979370 * dz,
                  192., 224. - dy, 750 - 835.979370 * dz, 0., -1., 0.) #TODO: 750 might not be accurate
        #print(glGetFloat(GL_MODELVIEW_MATRIX))
        glTranslatef(-x, -y, -z)

        glDrawArrays(GL_QUADS, 0, background.nb_vertices)

        #TODO: show the game itself
        # It is displayed on (0, 0, 0), (0, 448, 0), (388, 448, 0), (388, 0, 0)
        # using a camera at (192, 224, -835.979370) looking right behind itself
        # Depth test should be disabled when rendering the game

        pygame.display.flip()
        clock.tick(120)
        frame += 1



try:
    file_path, stage_num = sys.argv[1:]
    stage_num = int(stage_num)
except ValueError:
    print('Usage: %s std_dat_path stage_num' % sys.argv[0])
else:
    main(file_path, stage_num)

