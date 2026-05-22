import ctypes
import math
import os

import glfw
from OpenGL.GL import *
import numpy as np
import glm
from PIL import Image
from shader_s import Shader


# Window / scene state
WIDTH = 1080
HEIGHT = 1080

# OpenGL initialization (shaders, window)
def initOpenGL():
    """Creates a GLFW window, compiles the textured-MVP shader pair, and
    returns (window, program). Mirrors initOpenGL() from utils.py but with a
    shader pair that supports texture sampling and an MVP transform stack."""

    if not glfw.init():
        raise RuntimeError("Failed to initialize GLFW")
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(WIDTH, HEIGHT, "Bakery", None, None)

    if window is None:
        print("Failed to create GLFW window")
        glfw.terminate()
        raise RuntimeError("Failed to create GLFW window")

    glfw.make_context_current(window)

    # Load external shaders 
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vertex_path = os.path.join(base_dir, 'vertex_shader.vs')
    fragment_path = os.path.join(base_dir, 'fragment_shader.fs')
    shader = Shader(vertex_path, fragment_path)
    program = shader.getProgram()
    shader.use()

    loc_imagem = glGetUniformLocation(program, 'imagem')
    if loc_imagem != -1:
        glUniform1i(loc_imagem, 0)

    glEnable(GL_TEXTURE_2D)
    glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)

    return window, program

"""
Bounding box helper used to position objects relative to each other 
"""
def calcula_min_max_objeto(vertices_list, vertice_inicial, n_vertices,
                           escala=(1, 1, 1), translacao=(0, 0, 0)):
    pts = np.array(vertices_list[vertice_inicial:vertice_inicial + n_vertices],
                   dtype=float)

    sx, sy, sz = escala
    tx, ty, tz = translacao

    pts[:, 0] = pts[:, 0] * sx + tx
    pts[:, 1] = pts[:, 1] * sy + ty
    pts[:, 2] = pts[:, 2] * sz + tz

    return (pts[:, 0].min(), pts[:, 0].max(),
            pts[:, 1].min(), pts[:, 1].max(),
            pts[:, 2].min(), pts[:, 2].max())
