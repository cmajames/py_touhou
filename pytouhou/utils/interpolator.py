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


class Interpolator(object):
    def __init__(self, values=(), formula=None):
        self.values = tuple(values)
        self.start_values = tuple(values)
        self.end_values = tuple(values)
        self.start_frame = 0
        self.end_frame = 0
        self._frame = 0
        self._formula = formula or (lambda x: x)


    def __nonzero__(self):
        return self._frame < self.end_frame


    def set_interpolation_start(self, frame, values):
        self.start_values = tuple(values)
        self.start_frame = frame


    def set_interpolation_end(self, frame, values):
        self.end_values = tuple(values)
        self.end_frame = frame


    def set_interpolation_end_frame(self, end_frame):
        self.end_frame = end_frame


    def set_interpolation_end_values(self, values):
        self.end_values = tuple(values)


    def update(self, frame):
        self._frame = frame
        if frame >= self.end_frame - 1:
            self.values = tuple(self.end_values)
            self.start_values = tuple(self.end_values)
            self.start_frame = frame
        else:
            coeff = self._formula(float(frame - self.start_frame) / float(self.end_frame - self.start_frame))
            self.values = tuple(start_value + coeff * (end_value - start_value)
                                for (start_value, end_value) in zip(self.start_values, self.end_values))

