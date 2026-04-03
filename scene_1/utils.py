import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math

# =====================
# Useful math functions
# =====================

# Transformation matrix generator
def translation_matrix(t_x, t_y, t_z):
    return np.array([
        1.0, 0.0, 0.0, t_x,
        0.0, 1.0, 0.0, t_y,
        0.0, 0.0, 1.0, t_z,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)

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
        s_x, 0.0, 0.0, 0.0,
        0.0, s_y, 0.0, 0.0,
        0.0, 0.0, s_z, 0.0,
        0.0, 0.0, 0.0, 1.0
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

# =======================================
# Init OpenGL context and compile shaders
# =======================================
def initOpenGL():
    
    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE);
    window = glfw.create_window(700, 700, "Programa", None, None)

    if (window == None):
        print("Failed to create GLFW window")
        glfwTerminate()
        
    glfw.make_context_current(window)


    vertex_code = """
            attribute vec3 position;
            uniform mat4 mat_transformation;
            void main(){
                gl_Position = mat_transformation * vec4(position,1.0);
            }
            """

    fragment_code = """
            uniform vec4 color;
            void main(){
                gl_FragColor = color;
            }
            """

    # Request a program and shader slots from GPU
    program  = glCreateProgram()
    vertex   = glCreateShader(GL_VERTEX_SHADER)
    fragment = glCreateShader(GL_FRAGMENT_SHADER)

    # Set shaders source
    glShaderSource(vertex, vertex_code)
    glShaderSource(fragment, fragment_code)

    # Compile shaders
    glCompileShader(vertex)
    if not glGetShaderiv(vertex, GL_COMPILE_STATUS):
        error = glGetShaderInfoLog(vertex).decode()
        print(error)
        raise RuntimeError("Erro de compilacao do Vertex Shader")

    glCompileShader(fragment)
    if not glGetShaderiv(fragment, GL_COMPILE_STATUS):
        error = glGetShaderInfoLog(fragment).decode()
        print(error)
        raise RuntimeError("Erro de compilacao do Fragment Shader")

    # Attach shader objects to the program
    glAttachShader(program, vertex)
    glAttachShader(program, fragment)

    # Build program
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        print(glGetProgramInfoLog(program))
        raise RuntimeError('Linking error')
        
    # Make program the default program
    glUseProgram(program)

    return window, program