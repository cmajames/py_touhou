# -*- encoding: utf-8 -*-
##
## Copyright (C) 2013 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
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

GL_CONTEXT_MAJOR_VERSION = SDL_GL_CONTEXT_MAJOR_VERSION
GL_CONTEXT_MINOR_VERSION = SDL_GL_CONTEXT_MINOR_VERSION
GL_DOUBLEBUFFER = SDL_GL_DOUBLEBUFFER
GL_DEPTH_SIZE = SDL_GL_DEPTH_SIZE

WINDOWPOS_CENTERED = SDL_WINDOWPOS_CENTERED
WINDOW_OPENGL = SDL_WINDOW_OPENGL
WINDOW_SHOWN = SDL_WINDOW_SHOWN

SCANCODE_Z = SDL_SCANCODE_Z
SCANCODE_X = SDL_SCANCODE_X
SCANCODE_LSHIFT = SDL_SCANCODE_LSHIFT
SCANCODE_UP = SDL_SCANCODE_UP
SCANCODE_DOWN = SDL_SCANCODE_DOWN
SCANCODE_LEFT = SDL_SCANCODE_LEFT
SCANCODE_RIGHT = SDL_SCANCODE_RIGHT
SCANCODE_LCTRL = SDL_SCANCODE_LCTRL
SCANCODE_ESCAPE = SDL_SCANCODE_ESCAPE

KEYDOWN = SDL_KEYDOWN
QUIT = SDL_QUIT


class SDLError(Exception):
    pass


class SDL(object):
    def __init__(self, sound=True):
        self.sound = sound

    def __enter__(self):
        IF UNAME_SYSNAME == "Windows":
            SDL_SetMainReady()
        init(SDL_INIT_VIDEO)
        img_init(IMG_INIT_PNG)
        ttf_init()

        if self.sound:
            mix_init(0)
            mix_open_audio(44100, MIX_DEFAULT_FORMAT, 2, 4096)
            mix_allocate_channels(MAX_CHANNELS) #TODO: make it dependent on the SFX number.

    def __exit__(self, *args):
        if self.sound:
            Mix_CloseAudio()
            Mix_Quit()

        TTF_Quit()
        IMG_Quit()
        SDL_Quit()


cdef class Window:
    def __init__(self, const char *title, int x, int y, int w, int h, Uint32 flags):
        self.window = SDL_CreateWindow(title, x, y, w, h, flags)
        if self.window == NULL:
            raise SDLError(SDL_GetError())

    def __dealloc__(self):
        if self.context != NULL:
            SDL_GL_DeleteContext(self.context)
        if self.window != NULL:
            SDL_DestroyWindow(self.window)

    cdef void gl_create_context(self) except *:
        self.context = SDL_GL_CreateContext(self.window)
        if self.context == NULL:
            raise SDLError(SDL_GetError())

    cdef void gl_swap_window(self) nogil:
        SDL_GL_SwapWindow(self.window)

    cdef void set_window_size(self, int width, int height) nogil:
        SDL_SetWindowSize(self.window, width, height)


cdef class Surface:
    def __dealloc__(self):
        if self.surface != NULL:
            SDL_FreeSurface(self.surface)

    property pixels:
        def __get__(self):
            return bytes(self.surface.pixels[:self.surface.w * self.surface.h * 4])

    cdef void blit(self, Surface other):
        if SDL_BlitSurface(other.surface, NULL, self.surface, NULL) < 0:
            raise SDLError(SDL_GetError())

    cdef void set_alpha(self, Surface alpha_surface) nogil:
        nb_pixels = self.surface.w * self.surface.h
        image = self.surface.pixels
        alpha = alpha_surface.surface.pixels

        for i in xrange(nb_pixels):
            # Only use the red value, assume the others are equal.
            image[3+4*i] = alpha[3*i]


cdef class Music:
    def __dealloc__(self):
        if self.music != NULL:
            Mix_FreeMusic(self.music)

    cdef void play(self, int loops) nogil:
        Mix_PlayMusic(self.music, loops)

    cdef void set_loop_points(self, double start, double end) nogil:
        #Mix_SetLoopPoints(self.music, start, end)
        pass


cdef class Chunk:
    def __dealloc__(self):
        if self.chunk != NULL:
            Mix_FreeChunk(self.chunk)

    cdef void play(self, int channel, int loops) nogil:
        Mix_PlayChannel(channel, self.chunk, loops)

    cdef void set_volume(self, float volume) nogil:
        Mix_VolumeChunk(self.chunk, int(volume * 128))


cdef class Font:
    def __init__(self, const char *filename, int ptsize):
        self.font = TTF_OpenFont(filename, ptsize)
        if self.font == NULL:
            raise SDLError(SDL_GetError())

    def __dealloc__(self):
        if self.font != NULL:
            TTF_CloseFont(self.font)

    cdef Surface render(self, unicode text):
        cdef SDL_Color white
        white = SDL_Color(255, 255, 255, 255)
        surface = Surface()
        string = text.encode('utf-8')
        surface.surface = TTF_RenderUTF8_Blended(self.font, string, white)
        if surface.surface == NULL:
            raise SDLError(SDL_GetError())
        return surface


cdef void init(Uint32 flags) except *:
    if SDL_Init(flags) < 0:
        raise SDLError(SDL_GetError())


cdef void img_init(Uint32 flags) except *:
    if IMG_Init(flags) != flags:
        raise SDLError(SDL_GetError())


cdef void mix_init(int flags) except *:
    if Mix_Init(flags) != flags:
        raise SDLError(SDL_GetError())


cdef void ttf_init() except *:
    if TTF_Init() < 0:
        raise SDLError(SDL_GetError())


cdef void quit() nogil:
    SDL_Quit()


cdef void img_quit() nogil:
    IMG_Quit()


cdef void mix_quit() nogil:
    Mix_Quit()


cdef void ttf_quit() nogil:
    TTF_Quit()


cdef void gl_set_attribute(SDL_GLattr attr, int value) except *:
    if SDL_GL_SetAttribute(attr, value) < 0:
        raise SDLError(SDL_GetError())


cdef list poll_events():
    cdef SDL_Event event
    ret = []
    while SDL_PollEvent(&event):
        if event.type == SDL_KEYDOWN:
            ret.append((event.type, event.key.keysym.scancode))
        elif event.type == SDL_QUIT:
            ret.append((event.type,))
    return ret


cdef const Uint8* get_keyboard_state() nogil:
    return SDL_GetKeyboardState(NULL)


cdef Surface load_png(file_):
    data = file_.read()
    rwops = SDL_RWFromConstMem(<char*>data, len(data))
    surface = Surface()
    surface.surface = IMG_LoadPNG_RW(rwops)
    SDL_RWclose(rwops)
    if surface.surface == NULL:
        raise SDLError(SDL_GetError())
    return surface


cdef Surface create_rgb_surface(int width, int height, int depth, Uint32 rmask=0, Uint32 gmask=0, Uint32 bmask=0, Uint32 amask=0):
    surface = Surface()
    surface.surface = SDL_CreateRGBSurface(0, width, height, depth, rmask, gmask, bmask, amask)
    if surface.surface == NULL:
        raise SDLError(SDL_GetError())
    return surface


cdef void mix_open_audio(int frequency, Uint16 format_, int channels, int chunksize) except *:
    if Mix_OpenAudio(frequency, format_, channels, chunksize) < 0:
        raise SDLError(SDL_GetError())


cdef void mix_allocate_channels(int numchans) except *:
    if Mix_AllocateChannels(numchans) != numchans:
        raise SDLError(SDL_GetError())


cdef int mix_volume(int channel, float volume) nogil:
    return Mix_Volume(channel, int(volume * 128))


cdef int mix_volume_music(float volume) nogil:
    return Mix_VolumeMusic(int(volume * 128))


cdef Music load_music(const char *filename):
    music = Music()
    music.music = Mix_LoadMUS(filename)
    if music.music == NULL:
        raise SDLError(SDL_GetError())
    return music


cdef Chunk load_chunk(file_):
    cdef SDL_RWops *rwops
    chunk = Chunk()
    data = file_.read()
    rwops = SDL_RWFromConstMem(<char*>data, len(data))
    chunk.chunk = Mix_LoadWAV_RW(rwops, 1)
    if chunk.chunk == NULL:
        raise SDLError(SDL_GetError())
    return chunk


cdef Uint32 get_ticks() nogil:
    return SDL_GetTicks()


cdef void delay(Uint32 ms) nogil:
    SDL_Delay(ms)
