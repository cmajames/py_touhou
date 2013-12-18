from pytouhou.utils.interpolator cimport Interpolator
from pytouhou.formats.anm0 cimport ANM

cdef class Sprite:
    cdef public long blendfunc, frame
    cdef public double width_override, height_override, angle
    cdef public bint removed, changed, visible, force_rotation
    cdef public bint automatic_orientation, allow_dest_offset, mirrored
    cdef public bint corner_relative_placement
    cdef public Interpolator scale_interpolator, fade_interpolator
    cdef public Interpolator offset_interpolator, rotation_interpolator
    cdef public Interpolator color_interpolator
    cdef public ANM anm
    cdef public object _rendering_data

    cdef float _dest_offset[3]
    cdef double _texcoords[4]
    cdef double _texoffsets[2]
    cdef double _rescale[2]
    cdef double _scale_speed[2]
    cdef double _rotations_3d[3]
    cdef double _rotations_speed_3d[3]
    cdef unsigned char _color[4]

    cpdef fade(self, unsigned long duration, alpha, formula=*)
    cpdef scale_in(self, unsigned long duration, sx, sy, formula=*)
    cpdef move_in(self, unsigned long duration, x, y, z, formula=*)
    cpdef rotate_in(self, unsigned long duration, rx, ry, rz, formula=*)
    cpdef change_color_in(self, unsigned long duration, r, g, b, formula=*)
    cpdef update_orientation(self, double angle_base=*, bint force_rotation=*)
    cpdef Sprite copy(self)
    cpdef update(self)
