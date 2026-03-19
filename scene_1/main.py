import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
import config
import ast 
from  objects import alga, pedra, baiacu, helice, peixe

#agrupa todos vertices de todas figuras
global vertices_list 
vertices_list = []

"""
Abre o arquivo com a lista de vértices 
e com a relação dos triângulos (faces)
e adiciona na lista total de vertices 
"""
def load_model_from_file(filename):

    objects = {}
    vertices = []
    faces = []

    for line in open(filename, "r"): #pra cada linha do arquivo
        if line.startswith('#'): continue #ignorar comentários 
        
        values = line.split()

        if not values: continue 
        
        if values[0] == 'v': 
            vertices.append(values[0:3])
        elif values[0] == 'f':
            face = []
            for v in values[1:]:
                face.append(v)
            faces.append(face)

    model = {}
    model['vertices'] = vertices 
    model['faces'] = faces 

    return model 

"""
função para criar a lista de vértices 
de forma a triangularizar a figura (CONFIRMAR)?
"""
def circular_sliding_window_of_three(arr):
    if len(arr) == 3:
        return arr
    circular_arr = arr + [arr[0]]
    result = []
    for i in range(len(circular_arr) - 2):
        result.extend(circular_arr[i:i+3])
    return result

"""
carrega os vertices, faces guardando começo e
fim na lista de vertices pra cada objeto
"""
def load_obj(objFile):
    
    modelo = load_model_from_file(objFile)

    vertice_inicial = len(vertices_list)
    print('Processando modelo {}. Vertice inicial: {}'.format(objFile, len(vertices_list)))

    faces_vis = []

    for face in modelo['faces']:
        if face[2] not in faces_vis:
            faces_vis.append(face[2])    
        for vertice_id in circular_sliding_window_of_three(face[0]):
            vertices_list.append(modelo['vertices'][vertice_id - 1])
    
    verticesFinal = len(vertices_list)

    print('Processando modelo {}. Vertice final: {}'.format(objFile, len(vertices_list)))
    
    return vertice_inicial, verticesFinal - vertice_inicial 

def key_event(window,key,scancode,action,mods):
    global x_inc, y_inc, r_inc, s_inc
    
    if key == 263: x_inc -= 0.0001 #esquerda
    if key == 262: x_inc += 0.0001 #direita

    if key == 265: y_inc += 0.0001 #cima
    if key == 264: y_inc -= 0.0001 #baixo
        
    if key == 65: r_inc += 0.1 #letra a
    if key == 83: r_inc -= 0.1 #letra s
        
    if key == 90: s_inc += 0.1 #letra z
    if key == 88: s_inc -= 0.1 #letra x
           
def multiplica_matriz(a,b):
    m_a = a.reshape(4,4)
    m_b = b.reshape(4,4)
    m_c = np.dot(m_a,m_b)
    c = m_c.reshape(1,16)
    return c

def buffer_object():

    vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
    vertices['position'] = vertices_list

    #request buffer slot from GPU 
    buffer_VBO = glGenBuffers(1)
    
    # Make this buffer the default one
    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO)

    # Upload data
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)

    return buffer_VBO, vertices

def Bind_object(buffer, vertices, loc):

    glBindBuffer(GL_ARRAY_BUFFER, buffer)
    
    glVertexAttribPointer(loc, 3, GL_FLOAT, False, stride, offset)

def operar_vertices(angle, t_x, t_y, t_z, s_x, s_y, s_z):

    angle = math.radians(angle)

    matrix_transform = glm.mat4(1.0) #instancia matriz identidade 

    #matriz translação
    mat_translate = np.array([      1.0,  0.0, 0.0, t_x, 
                                    0.0,  1.0, 0.0, t_y, 
                                    0.0,  0.0, 1.0, t_z, 
                                    0.0,  0.0, 0.0, 1.0], np.float32)
    
    #matriz rotação
    mat_rotation_z = np.array([     math.cos(angle), -math.sin(angle), 0.0, 0.0, 
                                    math.sin(angle),  math.cos(angle), 0.0, 0.0, 
                                    0.0,      0.0, 1.0, 0.0, 
                                    0.0,      0.0, 0.0, 1.0], np.float32)

    #matriz escala 
    mat_scale = np.array([          s_x,  0.0, 0.0, 0.0, 
                                    0.0,  s_y, 0.0, 0.0, 
                                    0.0,  0.0, s_z, 0.0, 
                                    0.0,  0.0, 0.0, 1.0], np.float32)

    matrix_transform = multiplica_matriz(mat_translate, mat_rotation_z)
    matrix_transform = multiplica_matriz(mat_scale, matrix_transform)

    return matrix_transform

def desenha_helice(angulo, t_x, t_y, t_z):
    
    global vertices #preciso acessar 

    mat_transf = operar_vertices(angulo, t_x, t_y, t_z, 1.0, 1.0, 1.0)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    glDrawArrays(GL_TRIANGLES, verticeInicial_helice, qtdVertices_helice) # renderizando


def __main__():

    window, program = config.init()

    verticeInicial_helice, qtdVertices_helice = load_obj('objetos/helice.txt', )
    
    buffer_VBO, vertices = buffer_object()

    loc_vertices = glGetAttribLocation(program, "position")
    
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)

    glEnableVertexAttribArray(loc_vertices, 3, GL_FLOAT, False, stride, offset)

    loc_color = glGetUniformLocation(program, "color")
    
    glfw.set_key_callback(window,key_event)
    glfw.show_window(window)

    glEnable(GL_DEPTH_TEST) #3D

    angulo_helice = 0.0 
    v_angulo = 0.01 

    while not glfw.window_should_close(window):
        
        #erasing for redraw 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    
        glClearColor(1.0, 1.0, 1.0, 1.0)

        """
        velocidade da helice aumenta 0.001 a cada vez, 
        se teclar d ela volta pro original (gira mais devagar)
        """
        angulo_helice += v_angulo
        #desenha helice, passar angulo e ponto do centro 
        desenha_helice(angulo_helice, 0.0, 0.0, 0.0)

        #drawing alga 
        Bind_object(buffer_VBO, vertices, loc_vertices)

        glfw.poll_events()
