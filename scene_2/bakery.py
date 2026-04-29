import ctypes
import math
import os

import glfw
from OpenGL.GL import *
import numpy as np
import glm
from PIL import Image
from shader_s import Shader

# -----------------------------
# Window / scene state
# -----------------------------
WIDTH = 1080
HEIGHT = 1080

vertices_list = []
textures_coord_list = []

# Camera state (initialized in __main__)
cameraPos = None
cameraFront = None
cameraUp = None

# Mouse / view state
firstMouse = True
yaw = -90.0     # -90 so the initial cameraFront points along -Z
pitch = 0.0
lastX = WIDTH / 2.0
lastY = HEIGHT / 2.0
fov = 45.0

# Frame timing (used to scale movement speed)
deltaTime = 0.0
lastFrame = 0.0

# Wireframe toggle
polygonal_mode = False


# -----------------------------
# Live placement editor state
# -----------------------------
# Step sizes for the keybind editor. Translation is additive in world units;
# scale is multiplicative so a single factor works across the full range of
# object scales (this scene has objects from 0.002× to 55× — additive scaling
# would be useless at one end and runaway at the other).
STEP_TRANSLATION = 0.1
STEP_SCALE_FACTOR = 1.1
PLACEMENTS_FILE = 'placements.txt'

# Maps each model's name to its current transform tuple
# (angle, rx, ry, rz, tx, ty, tz, sx, sy, sz). Filled in __main__() after
# defaults are computed and the placements file (if any) is loaded.
placements = {}

# Index into the OBJECTS_REGISTRY name list — which object the numpad keys
# currently affect. Cycled with Page Up / Page Down.
selected_idx = 0


# =============================================================================
# OpenGL initialization (shaders, window)
# =============================================================================
def initOpenGL():
    """Creates a GLFW window, compiles the textured-MVP shader pair, and
    returns (window, program). Mirrors initOpenGL() from utils.py but with a
    shader pair that supports texture sampling and an MVP transform stack."""

    glfw.init()
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
    window = glfw.create_window(WIDTH, HEIGHT, "Bakery", None, None)

    if window is None:
        print("Failed to create GLFW window")
        glfw.terminate()
        raise RuntimeError("Failed to create GLFW window")

    glfw.make_context_current(window)

    # Load external shaders from the same directory as bakery.py.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vertex_path = os.path.join(base_dir, 'vertex_shader.vs')
    fragment_path = os.path.join(base_dir, 'fragment_shader.fs')
    shader = Shader(vertex_path, fragment_path)
    program = shader.getProgram()
    shader.use()

    # Bind the texture sampler uniform to texture unit 0.
    loc_imagem = glGetUniformLocation(program, 'imagem')
    if loc_imagem != -1:
        glUniform1i(loc_imagem, 0)

    # Texture / blending state expected by the shader
    glEnable(GL_TEXTURE_2D)
    glHint(GL_LINE_SMOOTH_HINT, GL_DONT_CARE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)

    return window, program


# =============================================================================
# Model loading (.obj with texture coords)
# =============================================================================
def load_model_from_file(filename):
    """Loads a Wavefront OBJ file and returns vertices, texture coords, and
    faces. Faces store both vertex indices and texture-coord indices so the
    two streams stay in sync when we expand them into the global arrays."""
    vertices = []
    texture_coords = []
    faces = []

    material = None

    for line in open(filename, "r", encoding="utf-8"):
        if line.startswith('#'):
            continue
        values = line.split()
        if not values:
            continue

        if values[0] == 'v':
            vertices.append(values[1:4])
        elif values[0] == 'vt':
            texture_coords.append(values[1:3])
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

    return {"vertices": vertices, "texture": texture_coords, "faces": faces}


def circular_sliding_window_of_three(arr):
    """Triangulates an n-gon face by fan-windowing its vertex list. Same
    helper used in aquarium.py / the original notebook."""
    if len(arr) == 3:
        return arr
    circular_arr = arr + [arr[0]]
    result = []
    for i in range(len(circular_arr) - 2):
        result.extend(circular_arr[i:i+3])
    return result


def load_texture_from_file(texture_id, img_path):
    """Binds `texture_id` and uploads the image at `img_path` as a 2D texture.
    Forces RGB mode so RGBA / palette / grayscale images all upload cleanly,
    and flips Y so OBJ texture coordinates (origin at bottom-left) match."""
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    img = Image.open(img_path).convert("RGB")
    img_width, img_height = img.size
    # The negative stride flips the image vertically so .obj `vt` coords
    # (origin bottom-left) line up with OpenGL's bottom-left texel origin.
    image_data = img.tobytes("raw", "RGB", 0, -1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_width, img_height,
                 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)


def load_obj_and_texture(obj_file, textures_list):
    """Appends the model's vertices and texture coords to the global lists,
    asks GL for one fresh texture name per image, uploads each one, and
    returns:
        (vertex_inicial, n_vertices, [texture_ids])
    Mirrors aquarium.py's `load_obj` API, extended for textures."""
    model = load_model_from_file(obj_file)

    vertex_inicial = len(vertices_list)
    print(f'Processing model {obj_file}. Initial vertex: {vertex_inicial}')

    for face in model['faces']:
        for vertex_id in circular_sliding_window_of_three(face[0]):
            vertices_list.append(model['vertices'][vertex_id - 1])
        for texture_id in circular_sliding_window_of_three(face[1]):
            textures_coord_list.append(model['texture'][texture_id - 1])

    vertex_final = len(vertices_list)
    print(f'Processing model {obj_file}. Final vertex: {vertex_final}')

    # Ask GL for one fresh texture name per image. glGenTextures(1) returns
    # a numpy scalar, glGenTextures(n) returns an array — normalize to a list.
    n = len(textures_list)
    if n == 1:
        texture_ids = [int(glGenTextures(1))]
    else:
        texture_ids = [int(x) for x in glGenTextures(n)]

    for tex_id, tex_path in zip(texture_ids, textures_list):
        load_texture_from_file(tex_id, tex_path)

    return vertex_inicial, vertex_final - vertex_inicial, texture_ids


# =============================================================================
# Buffer setup
# =============================================================================
def buffer_objects(program):
    """Creates two VBOs — one for positions, one for texture coords — and
    wires them up to the shader's `position` and `texture_coord` attributes.
    This is the dual-buffer equivalent of aquarium.py's buffer_object()."""
    buffer_VBO = glGenBuffers(2)

    # --- Vertex positions ---
    vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
    vertices['position'] = vertices_list

    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[0])
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)
    loc_vertices = glGetAttribLocation(program, "position")
    glEnableVertexAttribArray(loc_vertices)
    glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

    # --- Texture coordinates ---
    textures = np.zeros(len(textures_coord_list), [("position", np.float32, 2)])
    textures['position'] = textures_coord_list

    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[1])
    glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
    stride = textures.strides[0]
    offset = ctypes.c_void_p(0)
    loc_texture_coord = glGetAttribLocation(program, "texture_coord")
    glEnableVertexAttribArray(loc_texture_coord)
    glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)

    return buffer_VBO


# =============================================================================
# Transformation matrices
# =============================================================================
def model_matrix(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    """Builds a model matrix as Translate · Rotate · Scale (applied in that
    order to the incoming point: first scale, then rotate, then translate).
    Cleaner than the notebook version, which was order-ambiguous because of
    glm's right-multiplying mutators."""
    matrix_transform = glm.mat4(1.0)
    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))
    if angle != 0.0:
        matrix_transform = glm.rotate(matrix_transform,
                                      math.radians(angle),
                                      glm.vec3(r_x, r_y, r_z))
    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))

    return np.array(matrix_transform)


def view_matrix():
    return np.array(glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp))


def projection_matrix():
    return np.array(glm.perspective(glm.radians(fov),
                                    WIDTH / HEIGHT,
                                    0.01, 1000.0))


# =============================================================================
# Drawing functions (one per model)
# =============================================================================
def desenha_modelo(program, vertice_inicial, n_vertices, texture_id,
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    """Generic textured-model draw call. Each per-object wrapper below just
    fills in its own (vertice_inicial, n_vertices, texture_id) and forwards
    the transform parameters."""
    mat_model = model_matrix(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)

    glBindTexture(GL_TEXTURE_2D, texture_id)
    glDrawArrays(GL_TRIANGLES, vertice_inicial, n_vertices)


def desenha_ambiente(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['ambiente'][0], m['ambiente'][1], m['ambiente'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_mesa(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['mesa'][0], m['mesa'][1], m['mesa'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_bolo(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['bolo'][0], m['bolo'][1], m['bolo'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_pao(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['pao'][0], m['pao'][1], m['pao'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_batedeira(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['batedeira'][0], m['batedeira'][1], m['batedeira'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_luminaria(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['luminaria'][0], m['luminaria'][1], m['luminaria'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_mesa_picnic(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['mesa_picnic'][0], m['mesa_picnic'][1], m['mesa_picnic'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_poste_luz(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['poste_luz'][0], m['poste_luz'][1], m['poste_luz'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_flor(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['flor'][0], m['flor'][1], m['flor'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


# =============================================================================
# Object registry — single source of truth for every scene object
# =============================================================================
# The registry drives both the rendering loop and the editor's selection
# cycle. To add a new object:
#   1. Load it in __main__ via load_obj_and_texture (m['newname'] = ...).
#   2. Define a desenha_newname function above (or reuse desenha_modelo).
#   3. Append (name, desenha_func) to this list.
#   4. (Optional) Add a default placement in compute_default_placements;
#      otherwise it falls back to the all-zero translation, identity scale.
OBJECTS_REGISTRY = [
    ('ambiente',    desenha_ambiente),
    ('mesa',        desenha_mesa),
    ('bolo',        desenha_bolo),
    ('pao',         desenha_pao),
    ('batedeira',   desenha_batedeira),
    ('luminaria',   desenha_luminaria),
    ('mesa_picnic', desenha_mesa_picnic),
    ('poste_luz',   desenha_poste_luz),
    ('flor',        desenha_flor),
]


# =============================================================================
# Bounding-box helper (used to anchor objects relative to each other, the way
# the original notebook does for placing the table inside the environment and
# the cake on top of the table)
# =============================================================================
def calcula_min_max_objeto(vertice_inicial, n_vertices,
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


# =============================================================================
# Default placements + file I/O for the live editor
# =============================================================================
def compute_default_placements(m):
    """Returns name -> (angle, rx, ry, rz, tx, ty, tz, sx, sy, sz) for every
    object, using the same bounding-box-relative formulas the original
    bakery.py used. Called once at startup so 'no placements.txt' produces
    the original visual layout — the editor takes over from there."""
    defaults = {}

    amb_start, amb_count, _ = m['ambiente']
    a_minx, a_maxx, a_miny, a_maxy, a_minz, a_maxz = calcula_min_max_objeto(
        amb_start, amb_count
    )
    defaults['ambiente'] = (0.0, 0, 0, 0,  0.0, 0.0, 0.0,  1.0, 1.0, 1.0)

    mesa_start, mesa_count, _ = m['mesa']
    _, mesa_max_x, _, mesa_max_y, _, mesa_max_z = calcula_min_max_objeto(
        mesa_start, mesa_count, escala=(0.4, 0.2, 0.4)
    )
    posx = a_minx + mesa_max_x
    posy = mesa_max_y + a_miny
    posz = mesa_max_z + a_minz
    defaults['mesa'] = (90.0, 0, 90.0, 0, posx, posy, posz, 0.4, 0.2, 0.3)

    bolo_start, bolo_count, _ = m['bolo']
    _, b_maxx, _, b_maxy, _, b_maxz = calcula_min_max_objeto(
        bolo_start, bolo_count, escala=(0.002, 0.002, 0.002)
    )
    cent_x, cent_y, cent_z = posx / 2.0, posy / 2.0, posz / 2.0
    defaults['bolo'] = (
        0.0, 0, 0, 0,
        cent_x + b_maxx - 250,
        cent_y + b_maxy + 140,
        cent_z - b_maxz + 50,
        0.002, 0.002, 0.002,
    )

    defaults['pao']         = (0.0, 0, 1, 0,  cent_x - 120, cent_y + 140, cent_z + 80,  0.2, 0.2, 0.2)
    defaults['batedeira']   = (0.0, 0, 1, 0,  a_minx + 0.6, a_miny, a_minz + 0.6,       5.0, 5.0, 5.0)
    defaults['luminaria']   = (0.0, 0, 1, 0,  cent_x, a_maxy - 0.2, cent_z,             50.0, 50.0, 50.0)
    defaults['flor']        = (0.0, 0, 1, 0,  a_minx + 0.3, a_miny, a_minz + 0.3,       50.0, 50.0, 50.0)
    defaults['poste_luz']   = (0.0, 0, 1, 0,  a_maxx - 0.2, a_miny, a_maxz - 0.2,       55.0, 55.0, 55.0)
    defaults['mesa_picnic'] = (0.0, 0, 1, 0,  a_maxx - 1.0, a_miny, a_minz + 1.0,       5.0, 5.0, 5.0)

    return defaults


def load_placements(filename, defaults):
    """Reads a placements file. Each non-comment line:
        name angle rx ry rz tx ty tz sx sy sz   (11 fields total)
    Anything missing or malformed is filled in from `defaults`, so the
    program always has a complete set of valid placements at startup."""
    result = dict(defaults)  # start with full defaults; override per line

    if not os.path.exists(filename):
        print(f"[placements] {filename} not found — using defaults.")
        return result

    loaded = 0
    with open(filename, 'r', encoding='utf-8') as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 11:
                print(f"[placements] {filename}:{line_no} skipped "
                      f"(expected 11 fields, got {len(parts)})")
                continue
            name = parts[0]
            try:
                vals = tuple(float(x) for x in parts[1:])
            except ValueError as e:
                print(f"[placements] {filename}:{line_no} skipped ({e})")
                continue
            if name not in defaults:
                print(f"[placements] {filename}:{line_no} unknown object "
                      f"'{name}' — kept anyway in case you add it later.")
            result[name] = vals
            loaded += 1

    print(f"[placements] loaded {loaded} entries from {filename}.")
    return result


def save_placements(filename, placements_dict):
    """Writes the placements dict to disk in the same format load_placements
    expects. Header documents the format so the file is hand-editable. The
    output orders registry-known objects first (in registry order) and then
    any extras the dict happens to carry."""
    registry_names = [name for name, _ in OBJECTS_REGISTRY]
    extras = [n for n in placements_dict.keys() if n not in registry_names]
    ordered_names = registry_names + extras

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# Bakery scene placements\n")
        f.write("# Format: name angle rx ry rz tx ty tz sx sy sz\n")
        f.write("# Lines starting with # are ignored. Edit by hand or via\n")
        f.write("# the in-app editor (Page Up/Down to switch object, numpad\n")
        f.write("# 4/6/2/8/1/3 to translate, 7/9 to scale, Home to save).\n")
        for name in ordered_names:
            if name not in placements_dict:
                continue
            angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = placements_dict[name]
            f.write(f"{name} {angle:g} {rx:g} {ry:g} {rz:g} "
                    f"{tx:g} {ty:g} {tz:g} {sx:g} {sy:g} {sz:g}\n")
    print(f"[placements] saved {len(placements_dict)} entries to {filename}.")


# =============================================================================
# Input callbacks
# =============================================================================
def _selected_name():
    """Helper: returns the name of the currently selected object, or None
    if the registry is empty (defensive — shouldn't happen in practice)."""
    names = [name for name, _ in OBJECTS_REGISTRY]
    if not names:
        return None
    return names[selected_idx % len(names)]


def _print_selected():
    """Logs the currently selected object plus its current placement, so
    you can see what you're about to edit."""
    name = _selected_name()
    if name is None:
        print("[editor] no objects registered.")
        return
    names = [n for n, _ in OBJECTS_REGISTRY]
    idx = selected_idx % len(names)
    vals = placements.get(name)
    if vals is None:
        print(f"[editor] selected [{idx + 1}/{len(names)}] {name} (no placement)")
        return
    _, _, _, _, tx, ty, tz, sx, sy, sz = vals
    print(f"[editor] selected [{idx + 1}/{len(names)}] {name}  "
          f"pos=({tx:.3f}, {ty:.3f}, {tz:.3f})  "
          f"scale=({sx:.4f}, {sy:.4f}, {sz:.4f})")


def _adjust_selected(d_tx=0.0, d_ty=0.0, d_tz=0.0, scale_factor=1.0):
    """Mutates the current placement of the selected object. Translation is
    additive; scaling is multiplicative (uniform across all three axes — the
    sx:sy:sz ratio is preserved)."""
    name = _selected_name()
    if name is None or name not in placements:
        return
    angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = placements[name]
    placements[name] = (
        angle, rx, ry, rz,
        tx + d_tx, ty + d_ty, tz + d_tz,
        sx * scale_factor, sy * scale_factor, sz * scale_factor,
    )


def key_event(window, key, scancode, action, mods):
    global cameraPos, cameraFront, cameraUp, polygonal_mode
    global selected_idx

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

    cameraSpeed = 5.0 * deltaTime

    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += cameraSpeed * cameraFront
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= cameraSpeed * cameraFront
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed

    # 'P' toggles wireframe rendering, same as aquarium.py's mesh mode.
    if key == glfw.KEY_P and action == glfw.PRESS:
        polygonal_mode = not polygonal_mode
        print("Polygonal (wireframe) mode:", polygonal_mode)

    # ---- Live placement editor -------------------------------------------
    # Page Up / Page Down cycle the selection. PRESS only — holding shouldn't
    # whip through the list.
    if action == glfw.PRESS:
        n_objects = len(OBJECTS_REGISTRY)
        if key == glfw.KEY_PAGE_DOWN and n_objects > 0:
            selected_idx = (selected_idx + 1) % n_objects
            _print_selected()
        elif key == glfw.KEY_PAGE_UP and n_objects > 0:
            selected_idx = (selected_idx - 1) % n_objects
            _print_selected()
        elif key == glfw.KEY_HOME:
            save_placements(PLACEMENTS_FILE, placements)

    # Numpad translate / scale — fire on PRESS *and* REPEAT so holding the
    # key produces continuous movement (matches the WASD camera feel).
    if action == glfw.PRESS or action == glfw.REPEAT:
        s = STEP_TRANSLATION
        if key == glfw.KEY_KP_4:
            _adjust_selected(d_tx=-s)
        elif key == glfw.KEY_KP_6:
            _adjust_selected(d_tx=+s)
        elif key == glfw.KEY_KP_8:
            _adjust_selected(d_ty=+s)
        elif key == glfw.KEY_KP_2:
            _adjust_selected(d_ty=-s)
        elif key == glfw.KEY_KP_1:
            _adjust_selected(d_tz=+s)
        elif key == glfw.KEY_KP_3:
            _adjust_selected(d_tz=-s)
        elif key == glfw.KEY_KP_9:
            _adjust_selected(scale_factor=STEP_SCALE_FACTOR)
        elif key == glfw.KEY_KP_7:
            _adjust_selected(scale_factor=1.0 / STEP_SCALE_FACTOR)


def framebuffer_size_callback(window, w, h):
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = max(w, 1), max(h, 1)
    glViewport(0, 0, WIDTH, HEIGHT)


def mouse_callback(window, xpos, ypos):
    global cameraFront, lastX, lastY, firstMouse, yaw, pitch

    if firstMouse:
        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos  # y is flipped (window y grows downward)
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    if pitch > 89.0:
        pitch = 89.0
    if pitch < -89.0:
        pitch = -89.0

    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)


def scroll_callback(window, xoffset, yoffset):
    global fov
    fov -= yoffset
    fov = max(1.0, min(fov, 45.0))


# =============================================================================
# Main
# =============================================================================
def __main__():
    global cameraPos, cameraFront, cameraUp
    global deltaTime, lastFrame
    global polygonal_mode

    window, program = initOpenGL()

    # ---- Load all models. Each call returns (start, count, [tex_ids]).
    # GL texture names are allocated inside load_obj_and_texture itself, so
    # callers just say what they need and don't track ids. ----
    m = {}
    m['ambiente']    = load_obj_and_texture(
        'objetos/Ambiente/Ambiente.obj',
        ['objetos/Ambiente/Coffe_Shop_Colour.png'])
    m['mesa']        = load_obj_and_texture(
        'objetos/mesa/mesa.obj',
        ['objetos/mesa/wood table1_DefaultMaterial_BaseColor.1001.png'])
    m['bolo']        = load_obj_and_texture(
        'objetos/Bolo/bolo.obj',
        ['objetos/Bolo/cake_basecolor.png'])
    m['pao']         = load_obj_and_texture(
        'objetos/Pao/Pao.obj',
        ['objetos/Pao/BreadRollAlbeo.png'])
    m['batedeira']   = load_obj_and_texture(
        'objetos/batedeira/batedeira.obj',
        ['objetos/batedeira/kneading_machine_basecolor.png'])
    m['luminaria']   = load_obj_and_texture(
        'objetos/luminaria/luminaria.obj',
        ['objetos/luminaria/Body_RGH_2K.jpg'])
    m['mesa_picnic'] = load_obj_and_texture(
        'objetos/mesa_picnic/mesa_picnic.obj',
        ['objetos/mesa_picnic/Wood_Planks_C01_100cm.jpg'])
    m['poste_luz']   = load_obj_and_texture(
        'objetos/poste_luz/poste_luz.obj',
        ['objetos/poste_luz/Base Color.png'])
    m['flor']        = load_obj_and_texture(
        'objetos/flor/flor.obj',
        ['objetos/flor/Scaniverse_2024_01_19_180715.jpg'])

    # Upload everything to the GPU now that all vertex/uv lists are filled.
    buffer_objects(program)

    # ---- Editor bootstrap: compute defaults, then overlay anything the user
    # has saved in placements.txt. The result is a complete `placements` dict
    # the render loop can read every frame. ----
    global placements
    defaults = compute_default_placements(m)
    placements = load_placements(PLACEMENTS_FILE, defaults)

    # ---- Camera. Looks down -Z, up is +Y. (The notebook's original
    #      cameraFront = (0,1,0) was parallel to cameraUp, which makes
    #      lookAt produce a degenerate matrix.) ----
    cameraPos   = glm.vec3(0.0, 1.5, 4.0)
    cameraFront = glm.vec3(0.0, 0.0, -1.0)
    cameraUp    = glm.vec3(0.0, 1.0, 0.0)

    glfw.set_key_callback(window, key_event)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    glfw.show_window(window)
    glEnable(GL_DEPTH_TEST)

    # ---- Help banner ----
    print()
    print("=== Bakery — controls ===")
    print("  WASD + mouse : fly camera     |  scroll : zoom    |  Esc : quit")
    print("  P            : toggle wireframe")
    print("  Page Up/Down : switch selected object")
    print("  Numpad 4/6   : move -X / +X   |  8/2 : move +Y / -Y")
    print("  Numpad 1/3   : move +Z / -Z   |  9/7 : scale up / down")
    print("  Home         : save placements to placements.txt")
    print(f"  Translation step: {STEP_TRANSLATION}  Scale factor: {STEP_SCALE_FACTOR}x")
    print("=========================")
    _print_selected()

    # =========================================================================
    # Render loop
    # =========================================================================
    while not glfw.window_should_close(window):
        currentFrame = glfw.get_time()
        deltaTime = currentFrame - lastFrame
        lastFrame = currentFrame

        glfw.poll_events()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(1.0, 1.0, 1.0, 1.0)

        if polygonal_mode:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # ---- Draw every registered object using its current placement.
        # The editor mutates `placements` in place; this loop just reads it. ----
        for name, draw_func in OBJECTS_REGISTRY:
            vals = placements.get(name)
            if vals is None:
                # Fallback: unknown object with no placement — skip rather
                # than draw at a random transform.
                continue
            angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = vals
            draw_func(program, m, angle, rx, ry, rz, tx, ty, tz, sx, sy, sz)

        # Upload view + projection (model is set per-draw above).
        mat_view = view_matrix()
        loc_view = glGetUniformLocation(program, "view")
        glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

        mat_projection = projection_matrix()
        loc_projection = glGetUniformLocation(program, "projection")
        glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)

        glfw.swap_buffers(window)

    glfw.terminate()


__main__()
