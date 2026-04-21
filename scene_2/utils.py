import glfw
from OpenGL.GL import *
import numpy as np
import math
from numpy import random
from PIL import Image

from shader_s import Shader

# =====================
# Useful math functions
# =====================

# Transformation matrix generator
def translation_matrix(tx, ty, tz):
    return np.array([
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, tz],
        [0.0, 0.0, 0.0, 1.0]
    ])

# Rotation matrix generator for X axis
def rotation_x_matrix(angle_deg):
    angle = math.radians(angle_deg)
    return np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, math.cos(angle), -math.sin(angle), 0.0,
        0.0, math.sin(angle), math.cos(angle), 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

# Rotation matrix generator for Y axis
def rotation_y_matrix(angle_deg):
    angle = math.radians(angle_deg)
    return np.array([
        math.cos(angle), 0.0, math.sin(angle), 0.0,
        0.0, 1.0, 0.0, 0.0,
        -math.sin(angle), 0.0, math.cos(angle), 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

# Rotation matrix generator for Z axis
def rotation_z_matrix(angle_deg):
    angle = math.radians(angle_deg)
    return np.array([
        math.cos(angle), -math.sin(angle), 0.0, 0.0,
        math.sin(angle), math.cos(angle), 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

# Scale matrix generator
def scale_matrix(s_x, s_y, s_z):
    return np.array([
        [s_x, 0.0, 0.0, 0.0],
        [0.0, s_y, 0.0, 0.0],
        [0.0, 0.0, s_z, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ], np.float32)

# Helper function to multiply two 4x4 matrices represented as flat arrays
def matrix_mult(a, b):
    m_a = a.reshape(4, 4)
    m_b = b.reshape(4, 4)
    m_c = np.dot(m_a, m_b)
    return m_c.reshape(1, 16)

# Normalizes a vector
def normalize(v):
    x, y, z = v
    norma = math.sqrt(x*x + y*y + z*z)
    if norma == 0:
        return [0.0, 0.0, 0.0]
    return [x/norma, y/norma, z/norma]

def initOpenGL(largura, altura):

    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

    window = glfw.create_window(largura, altura, "Programa", None, None)

    if (window == None):
        print("Failed to create GLFW window")
        glfwTerminate()
        
    glfw.make_context_current(window)

    #shaders
    ourShader = Shader("vertex_shader.vs", "fragment_shader.fs")
    ourShader.use()

    program = ourShader.getProgram()

    #Para carregar os modelos (vértices e teturas a partir dos arquivos)
    glEnable(GL_TEXTURE_2D)
    glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
    glEnable( GL_BLEND )
    glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
    glEnable(GL_LINE_SMOOTH)

    return window, program

'''
É possível encontrar, na Internet, modelos .obj cujas faces não sejam triângulos. Nesses casos, precisamos gerar triângulos a partir dos vértices da face.
A função abaixo retorna a sequência de vértices que permite isso. Créditos: Hélio Nogueira Cardoso e Danielle Modesti (SCC0650 - 2024/2).
'''
def circular_sliding_window_of_three(arr):
    if len(arr) == 3:
        return arr
    circular_arr = arr + [arr[0]]
    result = []
    for i in range(len(circular_arr) - 2):
        result.extend(circular_arr[i:i+3])
    return result
