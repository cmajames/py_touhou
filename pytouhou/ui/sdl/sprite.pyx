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


from libc.math cimport M_PI as pi


cpdef tuple get_sprite_rendering_data(Sprite sprite):
    if not sprite.changed:
        return sprite._rendering_data

    x = 0
    y = 0

    tx, ty, tw, th = sprite._texcoords[0], sprite._texcoords[1], sprite._texcoords[2], sprite._texcoords[3]
    sx, sy = sprite._rescale[0], sprite._rescale[1]
    width = sprite.width_override or (tw * sx)
    height = sprite.height_override or (th * sy)

    rz = sprite._rotations_3d[2]
    if sprite.automatic_orientation:
        rz += pi/2. - sprite.angle
    elif sprite.force_rotation:
        rz += sprite.angle

    if sprite.allow_dest_offset:
        x += sprite._dest_offset[0]
        y += sprite._dest_offset[1]
    if not sprite.corner_relative_placement: # Reposition
        x -= width / 2
        y -= height / 2

    x_1 = sprite.anm.size_inv[0]
    y_1 = sprite.anm.size_inv[1]
    tox, toy = sprite._texoffsets[0], sprite._texoffsets[1]
    uvs = (tx * x_1 + tox,
           (tx + tw) * x_1 + tox,
           ty * y_1 + toy,
           (ty + th) * y_1 + toy)

    r, g, b, a = sprite._color[0], sprite._color[1], sprite._color[2], sprite._color[3]

    key = sprite.blendfunc
    values = (x, y, width, height), uvs, (r, g, b, a), -rz * 180 / pi, sprite.mirrored
    sprite._rendering_data = key, values
    sprite.changed = False

    return sprite._rendering_data