import os
import glfw
from OpenGL.GL import *
import OpenGL.GL.shaders
import numpy as np
import glm
import math
from utils import *
import ctypes

# -----------------------------
# Scene state
# -----------------------------
v_angle = 0.2
angle_fan = 0.0
mesh_mode = False
vertices_list = []

# Fish movement state
fish_y = -0.20
fish_progress = -0.18
fish_velocity = 0.0
fish_facing = 1.0  # 1.0 = swimming to the right, -1.0 = swimming to the left
fish_speed = 0.012

FISH_YAW_RIGHT = 120.0
FISH_YAW_LEFT = 300.0
FISH_PATH_CENTER_X = -0.02
FISH_PATH_CENTER_Z = 0.02
FISH_PATH_HALF_LENGTH = 0.62
FISH_PATH_DIR_X = 0.5
FISH_PATH_DIR_Z = 0.8660254

# Fish eye scale
fish_eye_scale_x = 0.03
fish_eye_scale_y = 0.05

# Global scene transform to create an isometric perspective
SCENE_SCALE = 0.72
SCENE_ROT_X = -20.0
SCENE_ROT_Y = 20.0
SCENE_SHIFT_Y = -0.02

# Aquarium dimensions
AQUARIUM_WIDTH = 2.15
AQUARIUM_HEIGHT = 1.75
AQUARIUM_DEPTH = 1.35
AQUARIUM_CENTER_Y = -0.10

# ==============================
# Procedural geometry generation
# ==============================

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

# ============================
# Model loading and processing
# ============================

#Loads vertices and faces from file
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

# Appends a model's vertices to the global list and returns the starting index and count of vertices for that model
def append_model(vertices, faces):
    vertex_inicial = len(vertices_list)

    for face in faces:
        for vertex_id in face:
            vertices_list.append(vertices[int(vertex_id)])

    vertices_final = len(vertices_list)
    return vertex_inicial, vertices_final - vertex_inicial

# Loads a model from file and appends its vertices to the global list, returning the starting index and count of vertices for that model
def load_obj(obj_file):
    model = load_model_from_file(obj_file)

    vertex_inicial = len(vertices_list)
    print(f'Processando model {obj_file}. vertex inicial: {vertex_inicial}')

    for face in model['faces']:
        for vertex_id in circular_sliding_window_of_three(face):
            vertices_list.append(model['vertices'][int(vertex_id) - 1])

    vertices_final = len(vertices_list)
    print(f'Processando model {obj_file}. vertex final: {vertices_final}')

    return vertex_inicial, vertices_final - vertex_inicial

# ==============
# OpenGL related
# ==============

# Creates a VBO for the vertices and uploads the data to the GPU
def buffer_object():
    vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
    vertices['position'] = vertices_list

    buffer_vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, buffer_vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)

    return buffer_vbo, vertices

# Uploads the transformation matrix to the shader
def define_transform(mat_transf):
    loc_model = glGetUniformLocation(program, "mat_transformation")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_transf)

# ===============
# Transformations
# ===============

# Creates global scene transformation matrix
def matrix_scene():
    mat_translate = translation_matrix(0.0, SCENE_SHIFT_Y, 0.0)
    mat_rot_y = rotation_y_matrix(SCENE_ROT_Y)
    mat_rot_x = rotation_x_matrix(SCENE_ROT_X)
    mat_scale = scale_matrix(SCENE_SCALE, SCENE_SCALE, SCENE_SCALE)

    scene = matrix_mult(mat_rot_y, mat_rot_x)
    scene = matrix_mult(scene, mat_scale)
    scene = matrix_mult(mat_translate, scene)
    return scene

# Generates transformation matrices
def operar_vertices(angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=0.0, rot_x=0.0, apply_scene=True):
    mat_translate = translation_matrix(t_x, t_y, t_z)
    mat_rotation_z = rotation_z_matrix(angle_z)
    mat_rotation_y = rotation_y_matrix(rot_y)
    mat_rotation_x = rotation_x_matrix(rot_x)
    mat_scale = scale_matrix(s_x, s_y, s_z)

    local_rotation = matrix_mult(mat_rotation_z, mat_rotation_y)
    local_rotation = matrix_mult(local_rotation, mat_rotation_x)
    matrix_transform = matrix_mult(local_rotation, mat_scale)
    matrix_transform = matrix_mult(mat_translate, matrix_transform)

    if apply_scene:
        matrix_transform = matrix_mult(matrix_scene(), matrix_transform)

    return matrix_transform

def transform_point(local_point, angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=0.0, rot_x=0.0):
    mat = operar_vertices(angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=rot_y, rot_x=rot_x, apply_scene=False)
    point = np.array([local_point[0], local_point[1], local_point[2], 1.0], dtype=np.float32)
    transformed = mat.reshape(4, 4) @ point
    return float(transformed[0]), float(transformed[1]), float(transformed[2])

# =================
# Fish related
# =================

# Determines fish yaw based on facing direction
def get_fish_yaw(facing):
    return FISH_YAW_RIGHT if facing >= 0.0 else FISH_YAW_LEFT

# Updates fish position based on velocity and path
def get_fish_position():
    x = FISH_PATH_CENTER_X + fish_progress * FISH_PATH_DIR_X
    z = FISH_PATH_CENTER_Z + fish_progress * FISH_PATH_DIR_Z
    return x, fish_y, z

# =================
# Drawing functions
# =================

# Generalized model drawing
def draw_model(inicio, quantidade, color, alpha=1.0, wire_overlay=False):
    glUniform4f(loc_color_global, color[0], color[1], color[2], alpha)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glDrawArrays(GL_TRIANGLES, inicio, quantidade)

    if wire_overlay:
        glUniform4f(loc_color_global, 0.0, 0.0, 0.0, 1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glDrawArrays(GL_TRIANGLES, inicio, quantidade)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

# Draws fan
def draw_fan(angle, t_x, t_y, t_z):
    mat_transf = operar_vertices(
        angle, t_x, t_y, t_z,
        0.42, 0.42, 0.42,
        rot_y=SCENE_ROT_X, rot_x=SCENE_ROT_Y,
        apply_scene=False
    )
    define_transform(mat_transf)

    # Transparent faces
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)

    glUniform4f(loc_color_global, 0.12, 0.14, 0.16, 0.22)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    glDrawArrays(GL_TRIANGLES, firstVertex_fan, nVertices_fan)

    glDepthMask(GL_TRUE)

    # Black outline
    glUniform4f(loc_color_global, 0.0, 0.0, 0.0, 1.0)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, firstVertex_fan, nVertices_fan)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

#Draws algae
def draw_algae(t_x, t_y, t_z, s_x, s_y):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, s_x, s_y, 0.65)
    define_transform(mat_transf)

    if mesh_mode:
        draw_model(firstVertex_alga, nVertices_alga, (0.22, 0.72, 0.34), alpha=0.35, wire_overlay=True)
    else:
        draw_model(firstVertex_alga, nVertices_alga, (0.22, 0.72, 0.34), alpha=1.0, wire_overlay=False)

#Draws pufferfish mouth using rock
def draw_mouth_pufferfish(t_x, t_y, t_z):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.07, 0.045, 0.06)
    define_transform(mat_transf)
    draw_model(firstVertex_rock, nVertices_rock, (0.93, 0.20, 0.62), alpha=1.0, wire_overlay=False)

#Draws pufferfish eye using rock
def draw_eye_pufferfish(t_x, t_y, t_z):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.05, 0.05, 0.05)
    define_transform(mat_transf)
    draw_model(firstVertex_rock, nVertices_rock, (0.05, 0.05, 0.05), alpha=1.0, wire_overlay=False)

# Draws whole pufferfish
def draw_pufferfish(t_x, t_y, t_z, s_x, s_y, s_z):
    body_angle_z = 270.0
    body_rot_y = 180.0
    mat_transf = operar_vertices(body_angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=body_rot_y)
    define_transform(mat_transf)

    if mesh_mode:
        draw_model(firstVertex_pufferfish, nVertices_pufferfish, (0.95, 0.80, 0.35), alpha=0.35, wire_overlay=True)
    else:
        draw_model(firstVertex_pufferfish, nVertices_pufferfish, (0.95, 0.80, 0.35), alpha=1.0, wire_overlay=False)

    # Anchor pufferfish eyes and mouth to pufferfish local space
    eye_right = transform_point((0.05, 0.11, 0.23), body_angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=body_rot_y)
    eye_left = transform_point((0.05, -0.11, 0.23), body_angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=body_rot_y)
    mouth = transform_point((-0.03, 0.0, 0.26), body_angle_z, t_x, t_y, t_z, s_x, s_y, s_z, rot_y=body_rot_y)

    # Draws pufferfish eyes and mouth
    draw_eye_pufferfish(*eye_right)
    draw_eye_pufferfish(*eye_left)
    draw_mouth_pufferfish(*mouth)

# Draws rock
def draw_rocks(t_x, t_y, t_z, scale=0.22):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, scale, scale, scale)
    define_transform(mat_transf)

    if mesh_mode:
        draw_model(firstVertex_rock, nVertices_rock, (0.55, 0.56, 0.58), alpha=0.35, wire_overlay=True)
    else:
        draw_model(firstVertex_rock, nVertices_rock, (0.55, 0.56, 0.58), alpha=1.0, wire_overlay=False)

# Draws fish eye using rock
def draw_eye_fish(t_x, t_y, t_z):
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, fish_eye_scale_x, fish_eye_scale_y, 0.035)
    define_transform(mat_transf)
    draw_model(firstVertex_rock, nVertices_rock, (0.05, 0.05, 0.05), alpha=1.0, wire_overlay=False)

# Draws whole fish
def draw_fish(t_x, t_y, t_z, facing=1.0):
    yaw = get_fish_yaw(facing)
    mat_transf = operar_vertices(0.0, t_x, t_y, t_z, 0.24, 0.24, 0.24, rot_y=yaw)
    define_transform(mat_transf)

    if mesh_mode:
        draw_model(firstVertex_fish, nVertices_fish, (1.0, 0.45, 0.12), alpha=0.35, wire_overlay=True)
    else:
        draw_model(firstVertex_fish, nVertices_fish, (1.0, 0.45, 0.12), alpha=1.0, wire_overlay=False)
    
    fish_yaw = get_fish_yaw(fish_facing)
    fish_eye_side = 0.10 if fish_facing > 0.0 else -0.10
    eye_x, eye_y, eye_z = transform_point(
        (-0.17, 0.05, fish_eye_side),
        0.0,
        t_x,
        t_y,
        t_z,
        0.24,
        0.24,
        0.24,
        rot_y=fish_yaw,
    )
    draw_eye_fish(eye_x, eye_y, eye_z)

# Draws sand
def draw_sand():
    mat_transf = operar_vertices(0.0, 0.0, 0.0, 0.0, 0.68, 1.0, 0.58)
    define_transform(mat_transf)

    if mesh_mode:
        draw_model(firstVertex_sand, nVertices_sand, (0.84, 0.77, 0.60), alpha=0.35, wire_overlay=True)
    else:
        draw_model(firstVertex_sand, nVertices_sand, (0.84, 0.77, 0.60), alpha=1.0, wire_overlay=False)

# Draws aquarium glass box
def draw_aquarium():
    mat_transf = operar_vertices(0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0)
    define_transform(mat_transf)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDepthMask(GL_FALSE)

    # Transparent Glass
    draw_model(firstVertex_aquarium, nVertices_aquarium, (0.68, 0.87, 0.98), alpha=0.18, wire_overlay=False)

    # Draw hard edges
    glUniform4f(loc_color_global, 0.38, 0.63, 0.82, 0.90)
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, firstVertex_aquarium, nVertices_aquarium)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    glDepthMask(GL_TRUE)

# =============================
# Defines keyboard interactions
# =============================
def key_event(window, key, scancode, action, mods):
    global v_angle, s_pufferfish, mesh_mode
    global fish_velocity, fish_facing, fish_speed

    # 'D' Stops or starts fan rotation
    if key == glfw.KEY_D and action == glfw.PRESS:
        v_angle = 0.0 if v_angle != 0.0 else 0.2
    
    # 'A' Inflates the pufferfish, 'S' deflates it, with limits to avoid extreme sizes
    elif key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        s_pufferfish = min(s_pufferfish + 0.05, 1.0)
    elif key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        s_pufferfish = max(s_pufferfish - 0.05, 0.5)
    
    # 'Z' Moves the fish left, 'X' moves it right. Releasing the keys stops the movement.
    elif key == glfw.KEY_Z:
        if action == glfw.PRESS or action == glfw.REPEAT:
            fish_velocity = -fish_speed
            fish_facing = -1.0
        elif action == glfw.RELEASE and fish_velocity < 0:
            fish_velocity = 0.0
    elif key == glfw.KEY_X:
        if action == glfw.PRESS or action == glfw.REPEAT:
            fish_velocity = fish_speed
            fish_facing = 1.0
        elif action == glfw.RELEASE and fish_velocity > 0:
            fish_velocity = 0.0
    
    # 'P' Toggles mesh mode
    elif key == glfw.KEY_P and action == glfw.PRESS:
        mesh_mode = not mesh_mode
        print("Mesh mode:", mesh_mode)

# =============
# Main function
# =============
def __main__():
    global angle_fan, v_angle
    global firstVertex_fish, nVertices_fish
    global firstVertex_alga, nVertices_alga
    global firstVertex_rock, nVertices_rock
    global firstVertex_pufferfish, nVertices_pufferfish, s_pufferfish
    global firstVertex_sand, nVertices_sand
    global vertices_list, program, firstVertex_fan, nVertices_fan
    global firstVertex_aquarium, nVertices_aquarium
    global fish_y, fish_progress, fish_velocity, fish_facing
    global loc_color_global

    window, program = initOpenGL()

    # Loading existing meshes
    firstVertex_fish, nVertices_fish = load_obj('fish.txt')
    firstVertex_fan, nVertices_fan = load_obj('fan.txt')
    firstVertex_alga, nVertices_alga = load_obj('alga.txt')
    firstVertex_pufferfish, nVertices_pufferfish = load_obj('pufferfish.txt')
    firstVertex_rock, nVertices_rock = load_obj('rock.txt')

    # Procedural sand box generation
    sand_vertices, sand_faces = create_box_geometry(
        3.0, 0.1, 2.0, 
        center=(0.0, -1.0, 0.0)
    )
    firstVertex_sand, nVertices_sand = append_model(sand_vertices, sand_faces)

    # Procedural aquarium glass box generation
    aquarium_vertices, aquarium_faces = create_box_geometry(
        AQUARIUM_WIDTH, AQUARIUM_HEIGHT, AQUARIUM_DEPTH,
        center=(0.0, AQUARIUM_CENTER_Y, 0.0)
    )
    firstVertex_aquarium, nVertices_aquarium = append_model(aquarium_vertices, aquarium_faces)

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

    angle_fan = 0.0
    v_angle = 0.2
    s_pufferfish = 0.62

    # Execution loop
    while not glfw.window_should_close(window):
        glfw.poll_events()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)

        # Process the filter fan angle and draw it
        angle_fan += v_angle
        draw_fan(angle_fan, -0.34, 0.12, -0.145)

        draw_sand()

        # Generate algae in different positions
        for i in range(18):
            x = -0.82 + i * 0.095
            z = -0.24 if i % 2 == 0 else -0.12
            scale_x = 0.34 if i % 3 else 0.28
            scale_y = 0.52 if i % 2 == 0 else 0.46
            draw_algae(x, -0.86, z, scale_x, scale_y)

        draw_pufferfish(-0.24, -0.18, 0.26, s_pufferfish, s_pufferfish, s_pufferfish)

        # Draw different sizes rocks in different places
        draw_rocks(-0.52, -0.86, 0.12, scale=0.21)
        draw_rocks(0.54, -0.86, -0.04, scale=0.24)
        draw_rocks(0.12, -0.90, -0.18, scale=0.17)

        # Process fish position and draws fish
        fish_progress += fish_velocity
        fish_progress = max(min(fish_progress, FISH_PATH_HALF_LENGTH), -FISH_PATH_HALF_LENGTH)
        fish_x, fish_y_current, fish_z = get_fish_position()
        draw_fish(fish_x, fish_y_current, fish_z, facing=fish_facing)

        # Draws aquarium last
        draw_aquarium()

        glfw.swap_buffers(window)

    glfw.terminate()


__main__()
