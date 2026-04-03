
import os
import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
import config
import ctypes

# -----------------------------
# Scene state
# -----------------------------
v_angulo = 0.2
angulo_helice = 0.0
mesh_mode = False
vertices_list = []

# Fish movement state
fish_x = -0.35
fish_y = -0.20
fish_vx = 0.0
fish_facing = 1.0  # 1.0 to right, -1.0 to left
fish_speed = 0.012

# Eye placement
fish_eye_offset_x = 0.08
fish_eye_offset_y = 0.02
fish_eye_scale_x = 0.03
fish_eye_scale_y = 0.05

# Global "camera-like" scene transform to create an isometric feel
SCENE_SCALE = 0.72
SCENE_ROT_X = -28.0
SCENE_ROT_Y = 38.0
SCENE_SHIFT_Y = -0.02

# Aquarium dimensions (centered near the origin before scene rotation)
AQUARIUM_WIDTH = 2.15
AQUARIUM_HEIGHT = 1.75
AQUARIUM_DEPTH = 1.35
AQUARIUM_CENTER_Y = -0.10


def create_box_geometry(width, height, depth, center=(0.0, 0.0, 0.0)):
    cx, cy, cz = center
    hw = width / 2.0
    hh = height / 2.0
    hd = depth / 2.0

    vertices = [
        [cx - hw, cy - hh, cz - hd],  # 0
        [cx + hw, cy - hh, cz - hd],  # 1
        [cx + hw, cy + hh, cz - hd],  # 2
        [cx - hw, cy + hh, cz - hd],  # 3
        [cx - hw, cy - hh, cz + hd],  # 4
        [cx + hw, cy - hh, cz + hd],  # 5
        [cx + hw, cy + hh, cz + hd],  # 6
        [cx - hw, cy + hh, cz + hd],  # 7
    ]

    faces = [
        [0, 1, 2], [0, 2, 3],  # back
        [4, 6, 5], [4, 7, 6],  # front
        [0, 4, 5], [0, 5, 1],  # bottom
        [3, 2, 6], [3, 6, 7],  # top
        [0, 3, 7], [0, 7, 4],  # left
        [1, 5, 6], [1, 6, 2],  # right
    ]

    return vertices, faces


def load_model_from_file(filename):
    vertices = []
    faces = []

    for line in open(filename, "r", encoding="utf-8"):
        if line.startswith('#'):
            continue

        values = line.split()
        if not values:
            continue

        if values[0] == 'v':
            vertices.append([float(values[1]), float(values[2]), float(values[3])])
        elif values[0] == 'f':
            face = []
            for value in values[1:]:
                face.append(value)
            faces.append(face)

    return {"vertices": vertices, "faces": faces}


def circular_sliding_window_of_three(arr):
    if len(arr) == 3:
        return arr
    circular_arr = arr + [arr[0]]
    result = []
    for i in range(len(circular_arr) - 2):
        result.extend(circular_arr[i:i+3])
    return result


def append_model(vertices, faces):
    vertice_inicial = len(vertices_list)

    for face in faces:
        for vertice_id in face:
            vertices_list.append(vertices[int(vertice_id)])

    vertices_final = len(vertices_list)
    return vertice_inicial, vertices_final - vertice_inicial


def load_obj(obj_file):
    modelo = load_model_from_file(obj_file)

    vertice_inicial = len(vertices_list)
    print(f'Processando modelo {obj_file}. Vertice inicial: {vertice_inicial}')

    for face in modelo['faces']:
        for vertice_id in circular_sliding_window_of_three(face):
            vertices_list.append(modelo['vertices'][int(vertice_id) - 1])

    vertices_final = len(vertices_list)
    print(f'Processando modelo {obj_file}. Vertice final: {vertices_final}')

    return vertice_inicial, vertices_final - vertice_inicial


def key_event(window, key, scancode, action, mods):
    global v_angulo, s_baiacu, mesh_mode
    global fish_vx, fish_facing, fish_speed

    if key == glfw.KEY_D and action == glfw.PRESS:
        v_angulo = 0.0 if v_angulo != 0.0 else 0.2
    elif key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        s_baiacu = min(s_baiacu + 0.05, 1.0)
    elif key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        s_baiacu = max(s_baiacu - 0.05, 0.5)
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


def multiplica_matriz(a, b):
    m_a = a.reshape(4, 4)
    m_b = b.reshape(4, 4)
    m_c = np.dot(m_a, m_b)
    return m_c.reshape(1, 16)


def buffer_object():
    vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
    vertices['position'] = vertices_list

    buffer_vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, buffer_vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)

    return buffer_vbo, vertices


def translation_matrix(t_x, t_y, t_z):
    return np.array([
        1.0, 0.0, 0.0, t_x,
        0.0, 1.0, 0.0, t_y,
        0.0, 0.0, 1.0, t_z,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)


def rotation_x_matrix(angle_deg):
    angle = math.radians(angle_deg)
    return np.array([
        1.0, 0.0, 0.0, 0.0,
        0.0, math.cos(angle), -math.sin(angle), 0.0,
        0.0, math.sin(angle), math.cos(angle), 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)


def rotation_y_matrix(angle_deg):
    angle = math.radians(angle_deg)
    return np.array([
        math.cos(angle), 0.0, math.sin(angle), 0.0,
        0.0, 1.0, 0.0, 0.0,
        -math.sin(angle), 0.0, math.cos(angle), 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)


def rotation_z_matrix(angle_deg):
    angle = math.radians(angle_deg)
    return np.array([
        math.cos(angle), -math.sin(angle), 0.0, 0.0,
        math.sin(angle), math.cos(angle), 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)


def scale_matrix(s_x, s_y, s_z):
    return np.array([
        s_x, 0.0, 0.0, 0.0,
        0.0, s_y, 0.0, 0.0,
        0.0, 0.0, s_z, 0.0,
        0.0, 0.0, 0.0, 1.0
    ], np.float32)


def matrix_scene():
    mat_translate = translation_matrix(0.0, SCENE_SHIFT_Y, 0.0)
    mat_rot_y = rotation_y_matrix(SCENE_ROT_Y)
    mat_rot_x = rotation_x_matrix(SCENE_ROT_X)
    mat_scale = scale_matrix(SCENE_SCALE, SCENE_SCALE, SCENE_SCALE)

    scene = multiplica_matriz(mat_rot_y, mat_rot_x)
    scene = multiplica_matriz(scene, mat_scale)
    scene = multiplica_matriz(mat_translate, scene)
    return scene


def operar_vertices(angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=0.0, rot_x=0.0, apply_scene=True):
    mat_translate = translation_matrix(t_x, t_y, t_z)
    mat_rotation_z = rotation_z_matrix(angle_z)
    mat_rotation_y = rotation_y_matrix(rot_y)
    mat_rotation_x = rotation_x_matrix(rot_x)
    mat_scale = scale_matrix(s_x, s_y, s_z)

    local_rotation = multiplica_matriz(mat_rotation_z, mat_rotation_y)
    local_rotation = multiplica_matriz(local_rotation, mat_rotation_x)
    matrix_transform = multiplica_matriz(local_rotation, mat_scale)
    matrix_transform = multiplica_matriz(mat_translate, matrix_transform)

    if apply_scene:
        matrix_transform = multiplica_matriz(matrix_scene(), matrix_transform)

    return matrix_transform


def define_transform(mat_transf):
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)


def desenha_modelo(inicio, quantidade, color, alpha=1.0, wire_overlay=False):
    glUniform4f(loc_color_global, color[0], color[1], color[2], alpha)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glDrawArrays(GL_TRIANGLES, inicio, quantidade)

    if wire_overlay:
        glUniform4f(loc_color_global, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, inicio, quantidade)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


def desenha_helice(angulo, t_x, t_y, t_z):
    mat_transf = operar_vertices(angulo, t_x, t_y, t_z, 0.22, 0.22, 0.22, rot_y=90.0)
    define_transform(mat_transf)

    glUniform4f(loc_color_global, 0.15, 0.20, 0.25, 1.0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, verticeInicial_helice, qtdVertices_helice)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


def desenha_corpo_filtro():
    mat_transf = operar_vertices(0.0, -0.68, 0.36, -0.26, 1.0, 1.0, 1.0)
    define_transform(mat_transf)
    desenha_modelo(verticeInicial_filtro, qtdVertices_filtro, (0.18, 0.22, 0.25), alpha=1.0, wire_overlay=mesh_mode)


def desenha_alga(t_x, t_y, t_z, s_x, s_y):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, s_x, s_y, 0.65)
    define_transform(mat_transf)

    if mesh_mode:
        desenha_modelo(verticeInicial_alga, qtdVertices_alga, (0.22, 0.72, 0.34), alpha=0.35, wire_overlay=True)
    else:
        desenha_modelo(verticeInicial_alga, qtdVertices_alga, (0.22, 0.72, 0.34), alpha=1.0, wire_overlay=False)


def desenha_baiacu(t_x, t_y, t_z, s_x, s_y, s_z):
    mat_transf = operar_vertices(90.0, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=20.0)
    define_transform(mat_transf)

    if mesh_mode:
        desenha_modelo(verticeInicial_baiacu, qtdVertices_baiacu, (0.95, 0.80, 0.35), alpha=0.35, wire_overlay=True)
    else:
        desenha_modelo(verticeInicial_baiacu, qtdVertices_baiacu, (0.95, 0.80, 0.35), alpha=1.0, wire_overlay=False)

    scale = s_x
    eye_right_x = t_x + 0.07 * scale
    eye_right_y = t_y + 0.02 * scale
    eye_right_z = t_z + 0.12 * scale
    eye_left_x = t_x - 0.07 * scale
    eye_left_y = t_y + 0.02 * scale
    eye_left_z = t_z + 0.12 * scale
    mouth_x = t_x
    mouth_y = t_y - 0.08 * scale
    mouth_z = t_z + 0.16 * scale

    desenha_olho_baiacu(eye_right_x, eye_right_y, eye_right_z)
    desenha_olho_baiacu(eye_left_x, eye_left_y, eye_left_z)
    desenha_boca_baiacu(mouth_x, mouth_y, mouth_z)


def desenha_pedra(t_x, t_y, t_z, scale=0.22):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, scale, scale, scale)
    define_transform(mat_transf)

    if mesh_mode:
        desenha_modelo(verticeInicial_pedra, qtdVertices_pedra, (0.55, 0.56, 0.58), alpha=0.35, wire_overlay=True)
    else:
        desenha_modelo(verticeInicial_pedra, qtdVertices_pedra, (0.55, 0.56, 0.58), alpha=1.0, wire_overlay=False)


def desenha_peixe(t_x, t_y, t_z, facing=1.0):
    s_x = 0.24 * facing
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, s_x, 0.24, 0.24, rot_y=120.0)
    define_transform(mat_transf)

    if mesh_mode:
        desenha_modelo(verticeInicial_peixe, qtdVertices_peixe, (1.0, 0.45, 0.12), alpha=0.35, wire_overlay=True)
    else:
        desenha_modelo(verticeInicial_peixe, qtdVertices_peixe, (1.0, 0.45, 0.12), alpha=1.0, wire_overlay=False)


def desenha_boca_baiacu(t_x, t_y, t_z):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.05, 0.05, 0.05)
    define_transform(mat_transf)
    desenha_modelo(verticeInicial_pedra, qtdVertices_pedra, (0.93, 0.20, 0.62), alpha=1.0, wire_overlay=False)


def desenha_olho_baiacu(t_x, t_y, t_z):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.035, 0.035, 0.035)
    define_transform(mat_transf)
    desenha_modelo(verticeInicial_pedra, qtdVertices_pedra, (0.05, 0.05, 0.05), alpha=1.0, wire_overlay=False)


def desenha_olho_peixe(t_x, t_y, t_z):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, fish_eye_scale_x, fish_eye_scale_y, 0.03)
    define_transform(mat_transf)
    desenha_modelo(verticeInicial_pedra, qtdVertices_pedra, (0.05, 0.05, 0.05), alpha=1.0, wire_overlay=False)


def desenha_areia():
    # The sand mesh is already generated near y = -1.0, so do not push it in z.
    mat_transf = operar_vertices(0.0, 0.0, 0.0, 0.0, 0.68, 1.0, 0.58)
    define_transform(mat_transf)

    if mesh_mode:
        desenha_modelo(verticeInicial_areia, qtdVertices_areia, (0.84, 0.77, 0.60), alpha=0.35, wire_overlay=True)
    else:
        desenha_modelo(verticeInicial_areia, qtdVertices_areia, (0.84, 0.77, 0.60), alpha=1.0, wire_overlay=False)


def desenha_aquario():
    mat_transf = operar_vertices(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    define_transform(mat_transf)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)

    # translucent glass
    desenha_modelo(verticeInicial_aquario, qtdVertices_aquario, (0.68, 0.87, 0.98), alpha=0.18, wire_overlay=False)

    # stronger edges
    glUniform4f(loc_color_global, 0.38, 0.63, 0.82, 0.90)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, verticeInicial_aquario, qtdVertices_aquario)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glDepthMask(GL_TRUE)


def __main__():
    global angulo_helice, v_angulo
    global verticeInicial_peixe, qtdVertices_peixe
    global verticeInicial_alga, qtdVertices_alga
    global verticeInicial_pedra, qtdVertices_pedra
    global verticeInicial_baiacu, qtdVertices_baiacu, s_baiacu
    global verticeInicial_areia, qtdVertices_areia
    global vertices_list, program, verticeInicial_helice, qtdVertices_helice
    global verticeInicial_aquario, qtdVertices_aquario
    global verticeInicial_filtro, qtdVertices_filtro
    global fish_x, fish_y, fish_vx, fish_facing
    global loc_color_global

    window, program = config.init()

    # Existing meshes
    verticeInicial_peixe, qtdVertices_peixe = load_obj('peixe.txt')
    verticeInicial_helice, qtdVertices_helice = load_obj('helice.txt')
    verticeInicial_alga, qtdVertices_alga = load_obj('alga.txt')
    verticeInicial_baiacu, qtdVertices_baiacu = load_obj('baiacu.txt')
    verticeInicial_pedra, qtdVertices_pedra = load_obj('pedra.txt')
    verticeInicial_areia, qtdVertices_areia = load_obj('areia.txt')

    # Procedural aquarium glass box
    aquario_vertices, aquario_faces = create_box_geometry(
        AQUARIUM_WIDTH, AQUARIUM_HEIGHT, AQUARIUM_DEPTH,
        center=(0.0, AQUARIUM_CENTER_Y, 0.0)
    )
    verticeInicial_aquario, qtdVertices_aquario = append_model(aquario_vertices, aquario_faces)

    # Small filter housing so the propeller does not look like it is floating
    filtro_vertices, filtro_faces = create_box_geometry(
        0.30, 0.48, 0.18,
        center=(0.0, 0.0, 0.0)
    )
    verticeInicial_filtro, qtdVertices_filtro = append_model(filtro_vertices, filtro_faces)

    buffer_vbo, vertices = buffer_object()

    loc_vertices = glGetAttribLocation(program, "position")
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)

    loc_color_global = glGetUniformLocation(program, "color")

    glEnableVertexAttribArray(loc_vertices)
    glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

    glfw.set_key_callback(window, key_event)
    glfw.show_window(window)

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    angulo_helice = 0.0
    v_angulo = 0.2
    s_baiacu = 0.62

    while not glfw.window_should_close(window):
        glfw.poll_events()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)

        angulo_helice += v_angulo

        # Scene contents
        desenha_corpo_filtro()
        desenha_helice(angulo_helice, -0.68, 0.36, -0.16)
        desenha_areia()

        # Algae: fewer instances and staggered depth so the scene reads as 3D
        for i in range(18):
            x = -0.82 + i * 0.095
            z = -0.24 if i % 2 == 0 else -0.12
            scale_x = 0.34 if i % 3 else 0.28
            scale_y = 0.52 if i % 2 == 0 else 0.46
            desenha_alga(x, -0.86, z, scale_x, scale_y)

        desenha_baiacu(0.12, -0.18, 0.26, s_baiacu, s_baiacu, s_baiacu)

        desenha_pedra(-0.52, -0.86, 0.12, scale=0.21)
        desenha_pedra(0.54, -0.86, -0.04, scale=0.24)
        desenha_pedra(0.12, -0.90, -0.18, scale=0.17)

        fish_x += fish_vx
        fish_x = max(min(fish_x, 0.68), -0.68)
        desenha_peixe(fish_x, fish_y, 0.10, facing=fish_facing)

        eye_x = fish_x + fish_facing * -fish_eye_offset_x
        eye_y = fish_y + fish_eye_offset_y
        desenha_olho_peixe(eye_x, eye_y, 0.20)

        # Aquarium glass must be drawn last
        desenha_aquario()

        glfw.swap_buffers(window)

    glfw.terminate()


__main__()
