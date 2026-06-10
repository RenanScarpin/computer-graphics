from utils import * 

vertices_list = []
textures_coord_list = []
normals_list = []

# Camera state (initialized in main)
cameraPos = None
cameraFront = None
cameraUp = None

# View state 
firstMouse = True
yaw = -90.0     # -90 so the initial cameraFront points along -Z
pitch = 0.0
lastX = WIDTH / 2.0
lastY = HEIGHT / 2.0
fov = 45.0

# Frame timing (used to scale movement speed)
deltaTime = 0.0
lastFrame = 0.0

polygonal_mode = False

# Variables that controls the movement of objects
ang_bolo = 0 
ang_flor = 0 
t_pao_y = 0
t_formiga = 0 
roda_formiga = 1
t_y_pao = 0 
s_pao = 0 

STEP_TRANSLATION = 0.1
STEP_SCALE_FACTOR = 1.1
PLACEMENTS_FILE = 'placements.txt'

"""
Current transform for each model 
(angle, rx, ry, rz, tx, ty, tz, sx, sy, sz)
initialized in main function from defaults and placements file 
"""
placements = {}

"""
Index of the object currently controlled by the numpad keys 
changed with page up/down
"""
selected_idx = 0

# Model loading (.obj with texture coords)
def load_model_from_file(filename):
    
    vertices = []
    texture_coords = []
    normals = []
    faces = []

    material = None
    # opens file for reading
    for line in open(filename, "r", encoding="utf-8"):## para cada linha do arquivo .obj
        if line.startswith('#'):## ignores comments
            continue
        values = line.split()# breaks lines
        if not values:
            continue

        ### recover vertices
        if values[0] == 'v':
            vertices.append(values[1:4])

        ### recovers texture coordinates
        elif values[0] == 'vt':
            texture_coords.append(values[1:3])
        elif values[0] == 'vn':
            normals.append(values[1:4])
        elif values[0] in ('usemtl', 'usemat'):
            material = values[1]
        ### recovers faces 
        elif values[0] == 'f':
            face = []
            face_texture = []
            face_normals = []
            for v in values[1:]:
                w = v.split('/')
                face.append(int(w[0]))
                if len(w) >= 2 and len(w[1]) > 0:
                    face_texture.append(int(w[1]))
                else:
                    face_texture.append(0)
                if len(w) >= 3 and len(w[2]) > 0:
                    face_normals.append(int(w[2]))
                else:
                    face_normals.append(0)
            faces.append((face, face_texture, face_normals, material))

    return {"vertices": vertices, "texture": texture_coords, "normals": normals, "faces": faces}

"""
Return triangle groups from a circular face index list 
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
load an image file into an opengl texture 
"""
def load_texture_from_file(texture_id, img_path):
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    img = Image.open(img_path).convert("RGB")
    img_width, img_height = img.size
    
    image_data = img.tobytes("raw", "RGB", 0, -1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img_width, img_height,
                 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)

"""
load an obj model, append mesh data and create texture 
"""
def load_obj_and_texture(obj_file, textures_list):

    model = load_model_from_file(obj_file)
    ### inserting vertices on vertice list
    vertex_inicial = len(vertices_list)
    print(f'Processing model {obj_file}. Initial vertex: {vertex_inicial}')

    for face in model['faces']:
        for vertex_id in circular_sliding_window_of_three(face[0]):
            vertices_list.append(model['vertices'][vertex_id - 1])
        for texture_id in circular_sliding_window_of_three(face[1]):
            if texture_id > 0 and model['texture']:
                textures_coord_list.append(model['texture'][texture_id - 1])
            else:
                textures_coord_list.append([0.0, 0.0])
        for normal_id in circular_sliding_window_of_three(face[2]):
            if normal_id > 0 and model['normals']:
                normals_list.append(model['normals'][normal_id - 1])
            else:
                normals_list.append([0.0, 1.0, 0.0])

    vertex_final = len(vertices_list)
    print(f'Processing model {obj_file}. Final vertex: {vertex_final}')

    n = len(textures_list)
    if n == 1:
        texture_ids = [int(glGenTextures(1))]
    else:
        texture_ids = [int(x) for x in glGenTextures(n)]

    for tex_id, tex_path in zip(texture_ids, textures_list):
        load_texture_from_file(tex_id, tex_path)

    return vertex_inicial, vertex_final - vertex_inicial, texture_ids


"""
upload vertex and texture data then link to the shader 
"""
def buffer_objects(program):
    """Creates two VBOs — one for positions, one for texture coords — and
    wires them up to the shader's `position` and `texture_coord` attributes.
    This is the dual-buffer equivalent of aquarium.py's buffer_object()."""
    buffer_VBO = glGenBuffers(3)

    # Vertex positions
    vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
    vertices['position'] = vertices_list

    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[0])
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)
    loc_vertices = glGetAttribLocation(program, "position")
    glEnableVertexAttribArray(loc_vertices)
    glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)

    # Texture coordinates
    textures = np.zeros(len(textures_coord_list), [("position", np.float32, 2)])
    textures['position'] = textures_coord_list

    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[1])
    glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
    stride = textures.strides[0]
    offset = ctypes.c_void_p(0)
    loc_texture_coord = glGetAttribLocation(program, "texture_coord")
    glEnableVertexAttribArray(loc_texture_coord)
    glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)

    # Normals
    normals = np.zeros(len(normals_list), [("position", np.float32, 3)])
    normals['position'] = normals_list

    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[2])
    glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
    stride = normals.strides[0]
    offset = ctypes.c_void_p(0)
    loc_normals = glGetAttribLocation(program, "normal")
    glEnableVertexAttribArray(loc_normals)
    glVertexAttribPointer(loc_normals, 3, GL_FLOAT, False, stride, offset)

    return buffer_VBO


"""
Transformation matrices
"""

# Build matrix from translation, rotation and scale 
# Local space -> world space   
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

# Return the camera view matrix 
# world space -> camera/view
def view_matrix():
    return np.array(glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp))

#Return the perspective projection matrix 
# camera space -> clip space 
def projection_matrix():
    return np.array(glm.perspective(glm.radians(fov),
                                    WIDTH / HEIGHT,
                                    0.01, 1000.0))


# Object draw functions 
#Each function draw one registered object applying the specific transformation
def desenha_modelo(program, vertice_inicial, n_vertices, texture_id,
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    """Generic textured-model draw call. Each per-object wrapper below just
    fills in its own (vertice_inicial, n_vertices, texture_id) and forwards
    the transform parameters."""
    mat_model = model_matrix(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
    glUniform1i(glGetUniformLocation(program, "isLightSource"), 0)

    glBindTexture(GL_TEXTURE_2D, texture_id)
    glDrawArrays(GL_TRIANGLES, vertice_inicial, n_vertices)

def set_object_light_profile(program, name):
    """Envia o perfil (peso difuso/especular) do objeto para o shader, definindo
    o quanto ele reage a cada componente de iluminacao."""
    diff_w, spec_w = OBJECT_LIGHT_PROFILES.get(name, DEFAULT_LIGHT_PROFILE)
    glUniform1f(glGetUniformLocation(program, "objDiffuse"), diff_w)
    glUniform1f(glGetUniformLocation(program, "objSpecular"), spec_w)

"""
function of drawing each object in a specific way
"""
def desenha_ambiente(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['ambiente'][0], m['ambiente'][1], m['ambiente'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_mesa(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['mesa'][0], m['mesa'][1], m['mesa'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_bolo(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    global ang_bolo
    desenha_modelo(program, m['bolo'][0], m['bolo'][1], m['bolo'][2][0],
                   angle+ang_bolo, r_x, r_y+ang_bolo, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_pao(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    global s_pao, t_pao_y
    if s_pao + 1 > 1.05:
        s_pao = 0.05 
        t_pao_y = 0.05
    desenha_modelo(program, m['pao'][0], m['pao'][1], m['pao'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y+t_pao_y, t_z, s_x+s_pao, s_y+s_pao, s_z+s_pao)


def desenha_batedeira(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['batedeira'][0], m['batedeira'][1], m['batedeira'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_luminaria(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['luminaria'][0], m['luminaria'][1], m['luminaria'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_poste_luz(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['poste_luz'][0], m['poste_luz'][1], m['poste_luz'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)


def desenha_flor(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    global ang_flor
    desenha_modelo(program, m['flor'][0], m['flor'][1], m['flor'][2][0],
                   angle+ang_flor, r_x, r_y+ang_flor, r_z, t_x, t_y, t_z, s_x, s_y, s_z)

def desenha_concreto(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['concreto'][0], m['concreto'][1], m['concreto'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)

def desenha_ceu(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['ceu'][0], m['ceu'][1], m['ceu'][2][0],
                   angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)

def desenha_formiga(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    global t_formiga, roda_formiga
    desenha_modelo(program, m['formiga'][0], m['formiga'][1], m['formiga'][2][0],
                   angle+90, r_x, r_y+(90*roda_formiga), r_z, t_x+t_formiga, t_y, t_z, s_x, s_y, s_z)

def desenha_plaquinha(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['plaquinha'][0], m['plaquinha'][1], m['plaquinha'][2][0],
                   angle+90, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)

def desenha_desenho(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    desenha_modelo(program, m['desenho'][0], m['desenho'][1], m['desenho'][2][0],
                   angle+90, r_x, r_y+180, r_z, t_x, t_y, t_z, s_x, s_y, s_z)

def desenha_carro(program, m, angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    global t_carro, roda_carro
    desenha_modelo(program, m['carro'][0], m['carro'][1], m['carro'][2][0],
                   angle+90, r_x, r_y+(90*roda_formiga), r_z, t_x+t_formiga, t_y, t_z, s_x, s_y, s_z)


OBJECTS_REGISTRY = [
    ('ambiente',    desenha_ambiente),
    ('mesa',        desenha_mesa),
    ('bolo',        desenha_bolo),
    ('pao',         desenha_pao),
    ('batedeira',   desenha_batedeira),
    ('luminaria',   desenha_luminaria),
    ('poste_luz',   desenha_poste_luz),
    ('flor',        desenha_flor),
    ('concreto',    desenha_concreto),
    ('ceu',         desenha_ceu),
    ('formiga', desenha_formiga), 
    ('plaquinha', desenha_plaquinha), 
    ('desenho', desenha_desenho),
    ('carro', desenha_carro)
]


LUMINARIA_LIGHT_OFFSET = (-0.01532, 8.0, 0.915223)
DESENHO_LIGHT_LOCAL_CENTER = (0.015007, 10.3359, 3.64879)


POSTE_LIGHT_OFFSET = (0.15, 1.8, 0.0)

CARRO_LIGHT_LOCAL_OFFSET = (1.2, 1.0, 3.5)



# Center of inside box
ambiente_center = (0.0, 0.0, 0.0)
INSIDE_BOX_HALF_EXTENTS = (7.5, 6, 8.05)

# Reflexion profiles for objects: (weight_diffuse, weight_specular).
OBJECT_LIGHT_PROFILES = {
    'batedeira':      (0.25, 1.0),
    'desenho':        (0.25, 1.0),
    'luminaria':      (0.25, 1.0),
    'pao':            (1.0, 0.2),   # -> + diffuse
    'bolo':           (1.0, 0.2),
    'poste_luz':      (0.5, 1.0),  # -> + specular
    'carro':          (0.25, 1.0),
    'formiga':        (1.0, 0.2),   # -> + diffuse
    'plaquinha':      (1.0, 0.2),
}
DEFAULT_LIGHT_PROFILE = (2.0, 1.0)

def object_light_position(name, offset=(0.0, 0.0, 0.0)):
    _, _, _, _, tx, ty, tz, _, _, _ = placements[name]
    ox, oy, oz = offset
    return tx + ox, ty + oy, tz + oz

def transformed_object_point(name, local_point=(0.0, 0.0, 0.0),
                             angle_offset=0.0, axis_offset=(0.0, 0.0, 0.0)):
    angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = placements[name]
    ax, ay, az = axis_offset

    matrix_transform = glm.mat4(1.0)
    matrix_transform = glm.translate(matrix_transform, glm.vec3(tx, ty, tz))
    if angle + angle_offset != 0.0:
        matrix_transform = glm.rotate(
            matrix_transform,
            math.radians(angle + angle_offset),
            glm.vec3(rx + ax, ry + ay, rz + az),
        )
    matrix_transform = glm.scale(matrix_transform, glm.vec3(sx, sy, sz))

    point = matrix_transform * glm.vec4(local_point[0], local_point[1], local_point[2], 1.0)
    return point.x, point.y, point.z

def carro_headlight_positions():
    """Posicoes dos dois farois do carro. O offset local e espelhado no eixo X
    local (carro simetrico) e transformado pelo model matrix do carro, da mesma
    forma que o desenho usa transformed_object_point."""
    x, y, z = CARRO_LIGHT_LOCAL_OFFSET
    axis = (0.0, 90.0 * roda_formiga, 0.0)
    left = transformed_object_point('carro', (x, y, z),
                                    angle_offset=90.0, axis_offset=axis)
    right = transformed_object_point('carro', (-x, y, z),
                                     angle_offset=90.0, axis_offset=axis)
    return left, right

def camera_is_inside():
    """True quando a camera esta dentro da caixa centrada no ambiente."""
    cx, cy, cz = ambiente_center
    hx, hy, hz = INSIDE_BOX_HALF_EXTENTS
    return (abs(cameraPos.x - cx) <= hx and
            abs(cameraPos.y - cy) <= hy and
            abs(cameraPos.z - cz) <= hz)

"""
Return the original default placement for each object

Called once at startup

If placements.txt is missing, this recreates the
same visual layout that bakery.py used before the editor takes over
"""
def compute_default_placements(m):
    
    defaults = {}

    amb_start, amb_count, _ = m['ambiente']
    a_minx, a_maxx, a_miny, a_maxy, a_minz, a_maxz = calcula_min_max_objeto(
        vertices_list, amb_start, amb_count
    )
    defaults['ambiente'] = (0.0, 0, 0, 0,  0.0, 0.0, 0.0,  1.0, 1.0, 1.0)

    mesa_start, mesa_count, _ = m['mesa']
    _, mesa_max_x, _, mesa_max_y, _, mesa_max_z = calcula_min_max_objeto(
        vertices_list, mesa_start, mesa_count, escala=(0.4, 0.2, 0.4)
    )
    posx = a_minx + mesa_max_x
    posy = mesa_max_y + a_miny
    posz = mesa_max_z + a_minz
    defaults['mesa'] = (90.0, 0, 90.0, 0, posx, posy, posz, 0.4, 0.2, 0.3)

    bolo_start, bolo_count, _ = m['bolo']
    _, b_maxx, _, b_maxy, _, b_maxz = calcula_min_max_objeto(
        vertices_list, bolo_start, bolo_count, escala=(0.002, 0.002, 0.002)
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
    defaults['plaquinha'] = (0.0, 0, 1, 0,  a_maxx - 1.0, a_miny, a_minz + 1.0,       5.0, 5.0, 5.0)
    return defaults

"""
Reads placements from file - falling back to defaults when needed
expected line format: name angle rx ry rz tx ty tz sx sy sz
Invalid entries are ignored 
"""
def load_placements(filename, defaults):
    
    result = dict(defaults)  # start with full defaults - override per line

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
                print(f"{filename}:{line_no} "
                      f"({len(parts)})")
                continue
            name = parts[0]
            try:
                vals = tuple(float(x) for x in parts[1:])
            except ValueError as e:
                print(f"{filename}:{line_no} ({e})")
                continue
            if name not in defaults:
                print(f"{filename}:{line_no}  "
                      f"'{name}'")
            result[name] = vals
            loaded += 1

    print(f" {loaded} from{filename}.")
    return result

"""
Write placements to file in the expected format 
"""
def save_placements(filename, placements_dict):
    
    registry_names = [name for name, _ in OBJECTS_REGISTRY]
    extras = [n for n in placements_dict.keys() if n not in registry_names]
    ordered_names = registry_names + extras

    with open(filename, 'w', encoding='utf-8') as f:
        for name in ordered_names:
            if name not in placements_dict:
                continue
            angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = placements_dict[name]
            f.write(f"{name} {angle:g} {rx:g} {ry:g} {rz:g} "
                    f"{tx:g} {ty:g} {tz:g} {sx:g} {sy:g} {sz:g}\n")
    print(f"[placements] saved {len(placements_dict)} entries to {filename}.")

"""
Return the selected object name or none if no objects exist
"""
def _selected_name():
    names = [name for name, _ in OBJECTS_REGISTRY]
    if not names:
        return None
    return names[selected_idx % len(names)]

"""
Log the selected object and its current placement 
"""
def print_selected():
    
    name = _selected_name()
    if name is None:
        print("no objects")
        return
    
    names = [n for n, _ in OBJECTS_REGISTRY]
    idx = selected_idx % len(names)
    vals = placements.get(name)
    
    if vals is None:
        print(f"selected [{idx + 1}/{len(names)}] {name} (no placement)")
        return
    
    _, _, _, _, tx, ty, tz, sx, sy, sz = vals
    print(f"selected [{idx + 1}/{len(names)}] {name}  "
          f"pos=({tx:.3f}, {ty:.3f}, {tz:.3f})  "
          f"scale=({sx:.4f}, {sy:.4f}, {sz:.4f})")

"""
Update the selected object's placement 
"""
def _adjust_selected(d_tx=0.0, d_ty=0.0, d_tz=0.0, scale_factor=1.0):
    name = _selected_name()
    if name is None or name not in placements:
        return
    angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = placements[name]
    placements[name] = (
        angle, rx, ry, rz,
        tx + d_tx, ty + d_ty, tz + d_tz,
        sx * scale_factor, sy * scale_factor, sz * scale_factor,
    )

ambient_on = True
light1_on = True
light2_on = True
light3_on = True
light4_on = True

ambient_intensity = 2.0
diffuse_factor = 2.0
specular_factor = 1.0

"""
Captures keyboard events:
0 -> Changes ambient light state (on/off)
1 -> Changes light state 1 (lamp / luminaria) - (on/off)
2 -> Changes light state 2 (wall sign / desenho) - (on/off)
3 -> Changes light state 3 (street lamp / poste_luz) - (on/off)
4 -> Changes light state 4 (car headlights / carro - both) - (on/off)
Z -> Decreases ambient intensity
X -> Increases ambient intensity
C -> Decreases diffuse reflection
V -> Increases diffuse reflection
B -> Decreases specular reflection
N -> Increases specular reflection
"""
def key_event(window, key, scancode, action, mods):
    
    global cameraPos, cameraFront, cameraUp, polygonal_mode
    global selected_idx
    global ambient_on, light1_on, light2_on, light3_on, light4_on
    global ambient_intensity, diffuse_factor, specular_factor
    global t_formiga, roda_formiga

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
    
    # Toggles ambient light
    if key == glfw.KEY_0 and (action == glfw.PRESS):
        ambient_on = not ambient_on
        print("Ambiente:", "ligada" if ambient_on else "desligada")

    # Toggles light 1
    elif key == glfw.KEY_1 and (action == glfw.PRESS):
        light1_on = not light1_on
        print("Luz 1:", "ligada" if light1_on else "desligada")

    # Toggles light 2
    elif key == glfw.KEY_2 and (action == glfw.PRESS):
        light2_on = not light2_on
        print("Luz 2:", "ligada" if light2_on else "desligada")

    # Turns on and off postlamp (light 3)
    elif key == glfw.KEY_3 and (action == glfw.PRESS):
        light3_on = not light3_on
        print("Luz 3 (poste):", "ligada" if light3_on else "desligada")

    # Turns on and off car headlights (light 4)
    elif key == glfw.KEY_4 and (action == glfw.PRESS):
        light4_on = not light4_on
        print("Luz 4 (farois):", "ligada" if light4_on else "desligada")

    # Decreases ambient light intensity
    elif key == glfw.KEY_Z and (action == glfw.PRESS or action == glfw.REPEAT):
        ambient_intensity = max(0.0, ambient_intensity - 0.05)
        print("ambient_intensity =", ambient_intensity)

    # Increases ambient light intensity
    elif key == glfw.KEY_X and (action == glfw.PRESS or action == glfw.REPEAT):
        ambient_intensity += 0.05
        print("ambient_intensity =", ambient_intensity)
    
    # Decreases diffuse reflexion
    elif key == glfw.KEY_C and (action == glfw.PRESS or action == glfw.REPEAT):
        diffuse_factor = max(0.0, diffuse_factor - 0.05)
        print("diffuse_factor =", diffuse_factor)

    # Increases diffuse reflexion
    elif key == glfw.KEY_V and (action == glfw.PRESS or action == glfw.REPEAT):
        diffuse_factor += 0.05
        print("diffuse_factor =", diffuse_factor)

    # Decreases specular reflexion
    elif key == glfw.KEY_B and (action == glfw.PRESS or action == glfw.REPEAT):
        specular_factor = max(0.0, specular_factor - 0.05)
        print("specular_factor =", specular_factor)

    # Increases specular reflexion 
    elif key == glfw.KEY_N and (action == glfw.PRESS or action == glfw.REPEAT):
        specular_factor += 0.05
        print("specular_factor =", specular_factor) 
    
    # Moves ant and car
    elif key == glfw.KEY_L and (action == glfw.PRESS or action == glfw.REPEAT):
        t_formiga = max(0.0, t_formiga - 0.05)
        roda_formiga = 1

    elif key == glfw.KEY_K and (action == glfw.PRESS or action == glfw.REPEAT):
        t_formiga += 0.05 
        roda_formiga = 0
       

    # ensure that camera doesn't pass from both sky or floor  
    if cameraPos.y < 0.37 + 0.8:
        cameraPos.y = 0.37 + 0.8
    if cameraPos.y > 48.0:
        cameraPos.y = 48
    if(cameraPos.x < -48):
        cameraPos.x = -48
    if(cameraPos.x > 48):
        cameraPos.x = 48
    if(cameraPos.z < -48):
        cameraPos.z = -48
    if(cameraPos.z > 48):
        cameraPos.z = 48

    # displays object meshes
    if key == glfw.KEY_P and action == glfw.PRESS:
        polygonal_mode = not polygonal_mode
        print("Polygonal (wireframe) mode:", polygonal_mode)

    """
    Live placement editor - page up/down - help placing the objects at the beginning
    """
    if action == glfw.PRESS:
        n_objects = len(OBJECTS_REGISTRY)
        if key == glfw.KEY_PAGE_DOWN and n_objects > 0:
            selected_idx = (selected_idx + 1) % n_objects
            print_selected()
        elif key == glfw.KEY_PAGE_UP and n_objects > 0:
            selected_idx = (selected_idx - 1) % n_objects
            print_selected()
        elif key == glfw.KEY_HOME:
            save_placements(PLACEMENTS_FILE, placements)
    
    """
    Numpad keys for move and scale the selected object  
    """
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

# Resize opengl viewport to match the window 
def framebuffer_size_callback(window, w, h):
    global WIDTH, HEIGHT
    WIDTH, HEIGHT = max(w, 1), max(h, 1)
    glViewport(0, 0, WIDTH, HEIGHT)

# glfw: whenever the mouse moves, this callback is called
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
    
    # make sure that when pitch is out of bounds, screen doesn't get flipped
    if pitch > 89.0:
        pitch = 89.0
    if pitch < -89.0:
        pitch = -89.0

    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)

# glfw: whenever the mouse scroll wheel scrolls, this callback is called
def scroll_callback(window, xoffset, yoffset):
    global fov
    fov -= yoffset
    fov = max(1.0, min(fov, 45.0))

def __main__():
    global cameraPos, cameraFront, cameraUp
    global deltaTime, lastFrame
    global polygonal_mode
    global normals_list

    window, program = initOpenGL()

    """
    Load models 
    each call returns start, count, tex_id 
    texture ids created inside the function of loading 
    """

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

    m['poste_luz']   = load_obj_and_texture(
        'objetos/poste_luz/poste_luz.obj',
        ['objetos/poste_luz/Base Color.png'])
    m['flor']        = load_obj_and_texture(
        'objetos/flor/flor.obj',
        ['objetos/flor/Scaniverse_2024_01_19_180715.jpg'])
    m['concreto']        = load_obj_and_texture(
        'objetos/concreto/Floor.obj',
        ['objetos/concreto/floor.png'])
    m['ceu']        = load_obj_and_texture(
        'objetos/ceu/ceu.obj',
        ['objetos/ceu/material_emissive.png'])
    
    m['formiga']        = load_obj_and_texture(
        'objetos/formiga/formiga.obj',
        ['objetos/formiga/Ant_Tris_Diffuse.png'])
    
    m['plaquinha']        = load_obj_and_texture(
        'objetos/plaquinha/plaquinha.obj',
        ['objetos/Ambiente/Coffe_Shop_Colour.png'])
    m['desenho']        = load_obj_and_texture(
        'objetos/desenho/desenho.obj',
        ['objetos/desenho/sign_ao.png'])
    m['carro']        = load_obj_and_texture(
        'objetos/car/car3.obj',
        ['objetos/car/baked_texture.png'])
    
    buffer_objects(program)

    #start with default placements then apply saved changes from placements 
    global placements, ambiente_center
    defaults = compute_default_placements(m)
    placements = load_placements(PLACEMENTS_FILE, defaults)

    # Center of coffe shop
    amb_start, amb_count, _ = m['ambiente']
    a_minx, a_maxx, a_miny, a_maxy, a_minz, a_maxz = calcula_min_max_objeto(
        vertices_list, amb_start, amb_count)
    _, _, _, _, atx, aty, atz, _, _, _ = placements['ambiente']
    ambiente_center = (
        (a_minx + a_maxx) / 2.0 + atx,
        (a_miny + a_maxy) / 2.0 + aty,
        (a_minz + a_maxz) / 2.0 + atz,
    )

    
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

    print_selected()

    glUniform1f(glGetUniformLocation(program, "ka"), 0.22)
    glUniform1f(glGetUniformLocation(program, "kd"), 0.85)
    glUniform1f(glGetUniformLocation(program, "ks"), 0.35)
    glUniform1f(glGetUniformLocation(program, "ns"), 32.0)
    
    # Render loop
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

        # Upload view and projection for this frame.
        mat_view = view_matrix()
        loc_view = glGetUniformLocation(program, "view")
        glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

        mat_projection = projection_matrix()
        loc_projection = glGetUniformLocation(program, "projection")
        glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)

        #taking the position of the first light - position of the light fixture + offset
        lx, ly, lz = object_light_position('luminaria', LUMINARIA_LIGHT_OFFSET)
        
        # Send the first internal light position to the shader
        glUniform3f(glGetUniformLocation(program, "lightPos1"), lx, ly, lz)
        
        #Send the on/off states of the ambient light and first internal light
        glUniform1i(glGetUniformLocation(program, "ambientOn"), int(ambient_on))
        glUniform1i(glGetUniformLocation(program, "light1On"), int(light1_on))
        
        # Send the global lighting control factors to the shader
        # ambientIntensity controls the strength of the ambient light
        # diffuseFactor controls how strongly surfaces react to diffuse reflection
        # specularFactor controls the intensity of specular highlights
        glUniform1f(glGetUniformLocation(program, "ambientIntensity"), ambient_intensity)
        glUniform1f(glGetUniformLocation(program, "diffuseFactor"), diffuse_factor)
        glUniform1f(glGetUniformLocation(program, "specularFactor"), specular_factor)

        #taking the position of the second light - position of the coffee sign on the wall + offset
        lx2, ly2, lz2 = transformed_object_point(
            'desenho',
            DESENHO_LIGHT_LOCAL_CENTER,
            angle_offset=90.0,
            axis_offset=(0.0, 180.0, 0.0),
        )
        
        #send the all the information of second light to the shader
        glUniform3f(glGetUniformLocation(program, "lightPos2"), lx2, ly2, lz2)
        glUniform1i(glGetUniformLocation(program, "light2On"), int(light2_on))

        glUniform1f(glGetUniformLocation(program, "ambientIntensity"), ambient_intensity)
        glUniform1f(glGetUniformLocation(program, "diffuseFactor"), diffuse_factor)
        glUniform1f(glGetUniformLocation(program, "specularFactor"), specular_factor)

        # Inside/outside the coffeshop
        glUniform1i(glGetUniformLocation(program, "cameraInside"), int(camera_is_inside()))

        # Light 3 -> postlamp (external)
        lx3, ly3, lz3 = object_light_position('poste_luz', POSTE_LIGHT_OFFSET)
        glUniform3f(glGetUniformLocation(program, "lightPos3"), lx3, ly3, lz3)
        glUniform1i(glGetUniformLocation(program, "light3On"), int(light3_on))

        # Lights 4 and 5 -> car headlights (external, always mirrored).
        # The 4 toggles both headlights together
        if 'carro' in placements:
            farol_esq, farol_dir = carro_headlight_positions()
            glUniform3f(glGetUniformLocation(program, "lightPos4"),
                        farol_esq[0] + t_formiga, farol_esq[1], farol_esq[2])
            glUniform3f(glGetUniformLocation(program, "lightPos5"),
                        farol_dir[0] + t_formiga, farol_dir[1], farol_dir[2])
        glUniform1i(glGetUniformLocation(program, "light4On"), int(light4_on))
        glUniform1i(glGetUniformLocation(program, "light5On"), int(light4_on))


        glUniform3f(glGetUniformLocation(program, "viewPos"), cameraPos.x, cameraPos.y, cameraPos.z)


        #Draw each object with its current placement 
        for name, draw_func in OBJECTS_REGISTRY:
            vals = placements.get(name)
            #skip objects without placement 
            if vals is None:
                continue
            angle, rx, ry, rz, tx, ty, tz, sx, sy, sz = vals
            set_object_light_profile(program, name)
            draw_func(program, m, angle, rx, ry, rz, tx, ty, tz, sx, sy, sz)

        glfw.swap_buffers(window)

    glfw.terminate()


__main__()
