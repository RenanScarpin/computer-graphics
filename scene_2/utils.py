import glfw
from OpenGL.GL import *
import numpy as np
import glm
import math
from numpy import random
from PIL import Image

from shader_s import Shader

global vertices_list
vertices_list = []    
global textures_coord_list
textures_coord_list = []


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


def initOpenGL(largura, altura):

    #inicilializando a janela 
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

def load_model_from_file(filename):
    """Loads a Wavefront OBJ file. """
    objects = {}
    vertices = []
    texture_coords = []
    faces = []

    material = None

    # abre o arquivo obj para leitura
    for line in open(filename, "r"): ## para cada linha do arquivo .obj
        if line.startswith('#'): continue ## ignora comentarios
        values = line.split() # quebra a linha por espaço
        if not values: continue

        ### recuperando vertices
        if values[0] == 'v':
            vertices.append(values[1:4])

        ### recuperando coordenadas de textura
        elif values[0] == 'vt':
            texture_coords.append(values[1:3])

        ### recuperando faces 
        elif values[0] in ('usemtl', 'usemat'):
            material = values[1]
        elif values[0] == 'f':
            face = []
            face_texture = []
            for v in values[1:]:
                w = v.split('/')
                face.append(int(w[0]))
                if len(w) >= 2 and len(w[1]) > 0:
                    face_texture.append(int(w[1]))
                else:
                    face_texture.append(0)

            faces.append((face, face_texture, material))

    model = {}
    model['vertices'] = vertices
    model['texture'] = texture_coords
    model['faces'] = faces

    return model


def load_texture_from_file(texture_id, img_textura):
    print(texture_id)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    img = Image.open(img_textura)
    img_width = img.size[0]
    img_height = img.size[1]
    image_data = img.tobytes("raw", "RGB", 0, -1)
    #image_data = np.array(list(img.getdata()), np.uint8)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_width, img_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)



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
    
global numberTextures
numberTextures = 0

def load_obj_and_texture(objFile, texturesList):
    modelo = load_model_from_file(objFile)
    
    ### inserindo vertices do modelo no vetor de vertices
    verticeInicial = len(vertices_list)
    print('Processando modelo {}. Vertice inicial: {}'.format(objFile, len(vertices_list)))
    faces_visited = []
    for face in modelo['faces']:
        if face[2] not in faces_visited:
            faces_visited.append(face[2])
        for vertice_id in circular_sliding_window_of_three(face[0]):
            vertices_list.append(modelo['vertices'][vertice_id - 1])
        for texture_id in circular_sliding_window_of_three(face[1]):
            textures_coord_list.append(modelo['texture'][texture_id - 1])
        
    verticeFinal = len(vertices_list)
    print('Processando modelo {}. Vertice final: {}'.format(objFile, len(vertices_list)))
    
    ### carregando textura equivalente e definindo um id (buffer): use um id por textura!
    global numberTextures
    for i in range(len(texturesList)):
        load_texture_from_file(numberTextures,texturesList[i])
        numberTextures += 1
    
    return verticeInicial, verticeFinal - verticeInicial