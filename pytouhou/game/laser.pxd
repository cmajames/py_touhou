from pytouhou.game.element cimport Element
from pytouhou.game.sprite cimport Sprite
from pytouhou.game.game cimport Game

cdef enum State:
    STARTING, STARTED, STOPPING


cdef class LaserLaunchAnim(Element):
    cdef Laser _laser

    cpdef update(self)


cdef class Laser(Element):
    cdef public unsigned long frame
    cdef public double angle

    cdef unsigned long start_duration, duration, stop_duration, grazing_delay,
    cdef unsigned long grazing_extra_duration, sprite_idx_offset
    cdef double base_pos[2], speed, start_offset, end_offset, max_length, width
    cdef State state
    cdef Game _game
    cdef object _laser_type

    cdef void set_anim(self, long sprite_idx_offset=*) except *
    cpdef set_base_pos(self, double x, double y)
    cdef bint _check_collision(self, double point[2], double border_size)
    cdef bint check_collision(self, double point[2])
    cdef bint check_grazing(self, double point[2])
    #def get_bullets_pos(self)
    cpdef cancel(self)
    cpdef update(self)


cdef class PlayerLaser(Element):
    cdef double hitbox[2], angle, offset
    cdef unsigned long frame, duration, sprite_idx_offset, damage
    cdef Element origin
    cdef object _laser_type

    cdef void set_anim(self, long sprite_idx_offset=*) except *
    cdef void cancel(self) except *
    cdef void update(self) except *
