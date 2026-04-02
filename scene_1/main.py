import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
import config
import ast 
import ctypes

#agrupa todos vertices de todas figuras

v_angulo = 0.2 
angulo_helice = 0.0
mesh_mode = False
vertices_list = []

# Fish movement state
fish_x = -0.5
fish_y = -0.3
fish_vx = 0.0
fish_facing = 1.0  # 1.0 to right, -1.0 to left
fish_speed = 0.015

# Eye placement (one side defines the other by mirror)
fish_eye_offset_x = 0.08  # horizontal distance from fish center
fish_eye_offset_y = 0.02  # vertical offset above fish center
fish_eye_scale_x = 0.03
fish_eye_scale_y = 0.05

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
            vertices.append([float(values[1]), float(values[2]), float(values[3])])
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
        for vertice_id in circular_sliding_window_of_three(face):
            vertices_list.append(modelo['vertices'][int(vertice_id) - 1])
    
    verticesFinal = len(vertices_list)

    print('Processando modelo {}. Vertice final: {}'.format(objFile, len(vertices_list)))
    
    return vertice_inicial, verticesFinal - vertice_inicial 

def key_event(window,key,scancode,action,mods):
    
    global v_angulo, angulo_helice, s_baiacu, mesh_mode
    global fish_vx, fish_facing, fish_speed
    
    if key == glfw.KEY_D and action == glfw.PRESS:
        if v_angulo == 0: #tava parado e volta a rodar
            v_angulo = 0.2
            print("voltei")
        else: 
            print("parei")
            v_angulo = 0.0
    elif key == glfw.KEY_A: #baiacu aumenta ate um limite
        s_baiacu += 0.05
        s_baiacu = min(s_baiacu, 1.0)

    elif key == glfw.KEY_S: #baiacu aumenta ate a escala inicial 
        s_baiacu -= 0.05
        s_baiacu = max(s_baiacu, 0.5)
    
    elif key == glfw.KEY_P and action == glfw.PRESS:
        mesh_mode = not mesh_mode
        print("Mesh mode:", mesh_mode)

    elif key == glfw.KEY_Z:
        if action == glfw.PRESS or action == glfw.REPEAT:
            fish_vx = -fish_speed
            fish_facing = 1.0
        elif action == glfw.RELEASE and fish_vx < 0:
            fish_vx = 0.0

    elif key == glfw.KEY_X:
        if action == glfw.PRESS or action == glfw.REPEAT:
            fish_vx = fish_speed
            fish_facing = -1.0
        elif action == glfw.RELEASE and fish_vx > 0:
            fish_vx = 0.0
        
    elif key == glfw.KEY_S: #baiacu aumenta ate a escala inicial 
        s_baiacu -= 0.05
        s_baiacu = max(s_baiacu, 0.5)
    
    elif key == glfw.KEY_P and action == glfw.PRESS:
        mesh_mode = not mesh_mode
        print("Mesh mode:", mesh_mode)

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

def operar_vertices(angle, t_x, t_y, t_z, s_x, s_y, s_z, rot_y = 0.0):

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
    
    mat_rotation_y = np.array([     math.cos(rot_y), 0.0, math.sin(rot_y), 0.0, 
                                    0.0,  1.0, 0.0, 0.0, 
                                    -math.sin(rot_y),      0.0, math.cos(rot_y), 0.0, 
                                    0.0,      0.0, 0.0, 1.0], np.float32)
    

    #matriz escala 
    mat_scale = np.array([          s_x,  0.0, 0.0, 0.0, 
                                    0.0,  s_y, 0.0, 0.0, 
                                    0.0,  0.0, s_z, 0.0, 
                                    0.0,  0.0, 0.0, 1.0], np.float32)
    
    mat_rotation_z = multiplica_matriz(mat_rotation_z, mat_rotation_y)
    matrix_transform = multiplica_matriz(mat_rotation_z, mat_scale)
    matrix_transform = multiplica_matriz(mat_translate, matrix_transform)

    return matrix_transform

def desenha_helice(angulo, t_x, t_y, t_z, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(angulo, t_x, t_y, t_z, 1.0, 1.0, 1.0)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    # draw lines
    glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, verticeInicial_helice, qtdVertices_helice)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


def desenha_cano(t_x, t_y, t_z, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.5, 0.5, 0.5)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_cano, qtdVertices_cano)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_cano, qtdVertices_cano)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_cano, qtdVertices_cano)


def desenha_alga(t_x, t_y, t_z, s_x, s_y, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, s_x,  s_y, 1.0)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 0.0, 1.0, 0.0, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_alga, qtdVertices_alga)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_alga, qtdVertices_alga)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.0, 1.0, 0.0, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_alga, qtdVertices_alga)

def desenha_baiacu(t_x, t_y, t_z, s_x, s_y, s_z, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(90.0, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 0.95, 0.80, 0.35, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_baiacu, qtdVertices_baiacu)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_baiacu, qtdVertices_baiacu)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.95, 0.80, 0.35, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_baiacu, qtdVertices_baiacu)

    # Draw eyes and mouth at scaled positions on the surface
    scale = s_x  # assuming uniform scaling
    eye_right_x = t_x + 0.07 * scale
    eye_right_y = t_y + 0.0
    eye_right_z = t_z - 0.8 * scale
    eye_left_x = t_x - 0.07 * scale
    eye_left_y = t_y + 0.0
    eye_left_z = t_z - 0.8 * scale
    mouth_x = t_x + 0.0
    mouth_y = t_y - 0.1 * scale
    mouth_z = t_z - 0.8 * scale

    desenha_olho_baiacu(eye_right_x, eye_right_y, eye_right_z, loc_color)
    desenha_olho_baiacu(eye_left_x, eye_left_y, eye_left_z, loc_color)
    desenha_boca_baiacu(mouth_x, mouth_y, mouth_z, loc_color)

def desenha_pedra(t_x, t_y, t_z, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.3, 0.3, 0.3)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 0.5, 0.5, 0.5, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.5, 0.5, 0.5, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)

def desenha_peixe(t_x, t_y, t_z, loc_color, facing=1.0):
    
    global vertices, mesh_mode #preciso acessar 

    # Flip horizontally by negative x-scale when facing left
    s_x = 0.3 * facing
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, s_x, 0.3, 0.3, rot_y=120.0)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 1.0, 0.45, 0.1, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_peixe, qtdVertices_peixe)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_peixe, qtdVertices_peixe)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 1.0, 0.45, 0.1, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_peixe, qtdVertices_peixe)

def desenha_boca_baiacu(t_x, t_y, t_z, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.07, 0.07, 0.07)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 1.0, 0.0, 0.7, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 1.0, 0.0, 0.7, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)

def desenha_olho_baiacu(t_x, t_y, t_z, loc_color):
    
    global vertices, mesh_mode #preciso acessar 

    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.04, 0.04, 0.04)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)


def desenha_olho_peixe(t_x, t_y, t_z, loc_color):
    global vertices, mesh_mode

    # vertical ellipse style from rock model
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, fish_eye_scale_x, fish_eye_scale_y, 0.03)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

    if mesh_mode:
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_pedra, qtdVertices_pedra)

def desenha_areia(loc_color):
    
    global vertices, mesh_mode
    
    mat_transf = operar_vertices(0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0)
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)
    
    if mesh_mode:
        # draw fill with transparency
        glUniform4f(loc_color, 0.8, 0.7, 0.5, 0.3)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDrawArrays(GL_TRIANGLES, verticeInicial_areia, qtdVertices_areia)
        # draw lines
        glUniform4f(loc_color, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, verticeInicial_areia, qtdVertices_areia)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    else:
        glUniform4f(loc_color, 0.8, 0.7, 0.5, 1.0)
        glDrawArrays(GL_TRIANGLES, verticeInicial_areia, qtdVertices_areia)

def __main__():

    global angulo_helice, v_angulo
    global verticeInicial_peixe, qtdVertices_peixe
    global verticeInicial_cano, qtdVertices_cano 
    global verticeInicial_alga, qtdVertices_alga
    global verticeInicial_pedra, qtdVertices_pedra
    global verticeInicial_baiacu, qtdVertices_baiacu, s_baiacu
    global verticeInicial_areia, qtdVertices_areia
    global vertices_list, program, verticeInicial_helice, qtdVertices_helice
    global verticeInicial_fundo_helice, qtdVertices_fundo_helice
    global fish_x, fish_y, fish_vx, fish_facing

    window, program = config.init()

    verticeInicial_peixe, qtdVertices_peixe = load_obj('peixe.txt')
    verticeInicial_helice, qtdVertices_helice = load_obj('helice.txt')
    verticeInicial_alga, qtdVertices_alga = load_obj('alga.txt')
    verticeInicial_baiacu, qtdVertices_baiacu = load_obj('baiacu.txt')
    verticeInicial_pedra, qtdVertices_pedra = load_obj('pedra.txt')
    verticeInicial_cano, qtdVertices_cano = load_obj('cano.txt')
    verticeInicial_areia, qtdVertices_areia = load_obj('areia.txt')

    buffer_VBO, vertices = buffer_object()

    loc_vertices = glGetAttribLocation(program, "position")
    
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)

    loc_color = glGetUniformLocation(program, "color")
    
    glEnableVertexAttribArray(loc_vertices)
    glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

    glfw.set_key_callback(window,key_event)
    glfw.show_window(window)

    glEnable(GL_DEPTH_TEST) #3D

    angulo_helice = 0.0 
    v_angulo = 0.2
    s_baiacu = 0.7

    while not glfw.window_should_close(window):
        
        glfw.poll_events()

        if mesh_mode:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_BLEND)

        #erasing for redraw 
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)    
        glClearColor(0.0, 0.3, 0.8, 0.3)

        """
        velocidade da helice aumenta 0.001 a cada vez, 
        se teclar d ela volta pro original (gira mais devagar)
        """
        angulo_helice += v_angulo

        #desenha helice, passar angulo e ponto do centro 
        desenha_helice(angulo_helice, -0.7, 0.5, 0.0, loc_color)
        #desenha_cano(-0.7, 0.5, 0.0, loc_color)

        #desenha areia no fundo
        desenha_areia(loc_color)

        #desenhar várias algas no fundo do aquário
        pos_alga = -1.9

        for i in range(0, 300):
            desenha_alga(pos_alga, -1.0, 0.0, 0.5, 0.5, loc_color)
            pos_alga += 0.06
        
        desenha_baiacu(0.0, -0.2, 0.9, s_baiacu, s_baiacu, s_baiacu, loc_color)

        desenha_pedra(-0.6, -0.9, 0.0, loc_color)
        desenha_pedra(0.6, -0.9, 0.0, loc_color)

        # update fish position and keep it inside view
        fish_x += fish_vx
        fish_x = max(min(fish_x, 1.8), -1.8)
        desenha_peixe(fish_x, fish_y, 0.0, loc_color, facing=fish_facing)

        # single fish eye that mirrors position with facing direction
        eye_x = fish_x + fish_facing * -fish_eye_offset_x
        eye_y = fish_y + fish_eye_offset_y
        desenha_olho_peixe(eye_x, eye_y, -0.1, loc_color)

        glfw.swap_buffers(window)
    
    glfw.terminate()

__main__()