from OpenGL.GL import *
import glfw
import glm
import numpy as np
from utils import * 
from shader_s import *

altura = 700
largura = 700
ativo = [0, 0, 0, 0, 0]

global vertices_list
vertices_list = []    
global textures_coord_list
textures_coord_list = []

# Inicializando a posição da câmera usando glm.vec3
cameraPos   = glm.vec3(0.0, 0.0, 3.0)
cameraFront = glm.vec3(0.0, 0.0, -1.0)
cameraUp    = glm.vec3(0.0, 1.0, 0.0)

firstMouse = True
yaw   = -90.0	# yaw is initialized to -90.0 degrees since a yaw of 0.0 results in a direction vector pointing to the right so we initially rotate a bit to the left.
pitch =  0.0
lastX =  largura / 2.0
lastY =  altura / 2.0
fov   =  45.0

# timing
deltaTime = 0.0	# time between current frame and last frame


firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX =  largura/2
lastY =  altura/2



def key_event(window,key,scancode,action,mods):
    global cameraPos, cameraFront, cameraUp, polygonal_mode, deltaTime

    print(deltaTime)

    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)
    
    cameraSpeed = 50 * deltaTime
    if key == glfw.KEY_W and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += cameraSpeed * cameraFront
    
    if key == glfw.KEY_S and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= cameraSpeed * cameraFront
    
    if key == glfw.KEY_A and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos -= glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed
        
    if key == glfw.KEY_D and (action == glfw.PRESS or action == glfw.REPEAT):
        cameraPos += glm.normalize(glm.cross(cameraFront, cameraUp)) * cameraSpeed

    if key == glfw.KEY_P and action == glfw.PRESS:
        polygonal_mode = not polygonal_mode
        


def framebuffer_size_callback(window, largura, altura):
    glViewport(0, 0, largura, altura)

# Mouse callback (alterado para usar glm)
def mouse_callback(window, xpos, ypos):
    global cameraFront, lastX, lastY, firstMouse, yaw, pitch
   
    if (firstMouse):

        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos # reversed since y-coordinates go from bottom to top
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1 # change this value to your liking
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # make sure that when pitch is out of bounds, screen doesn't get flipped
    if (pitch > 89.0):
        pitch = 89.0
    if (pitch < -89.0):
        pitch = -89.0

    front = glm.vec3()
    front.x = glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    front.y = glm.sin(glm.radians(pitch))
    front.z = glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    cameraFront = glm.normalize(front)

# Scroll callback
def scroll_callback(window, xoffset, yoffset):
    global fov

    fov -= yoffset
    if (fov < 1.0):
        fov = 1.0
    if (fov > 45.0):
        fov = 45.0


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



# Matrizes de transformação e modelagem
def model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    
    angle = math.radians(angle)
    
    matrix_transform = glm.mat4(1.0) # instanciando uma matriz identidade
       
    # aplicando translacao (terceira operação a ser executada)
    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z))    
    
    # aplicando rotacao (segunda operação a ser executada)
    if angle!=0:
        matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(r_x, r_y, r_z))
    
    # aplicando escala (primeira operação a ser executada)
    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))
    
    matrix_transform = np.array(matrix_transform)
    
    return matrix_transform

def view():
    global cameraPos, cameraFront, cameraUp
    mat_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp);
    mat_view = np.array(mat_view)
    return mat_view

def projection():
    global altura, largura
    # perspective parameters: fovy, aspect, near, far
    mat_projection = glm.perspective(glm.radians(fov), largura/altura, 0.1, 100.0)

    
    mat_projection = np.array(mat_projection)    
    return mat_projection

# Funções de drawing
def draw_bakery(angle, id, ativo, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z, textureId):
    mat_model = model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z)
    loc_model = glGetUniformLocation(program, "model")
    glUniformMatrix4fv(loc_model, 1, GL_TRUE, mat_model)
    
    glBindTexture(GL_TEXTURE_2D, textureId)
    
    if ativo[id]:
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glDrawArrays(GL_TRIANGLES, verticeInicial_caixa, quantosVertices_caixa)
    
    if ativo[id]:
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

# Função de upload dos dados
def upload_vertex(vertices):
    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[0])
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
    stride = vertices.strides[0]
    offset = ctypes.c_void_p(0)
    loc_vertices = glGetAttribLocation(program, "position")
    glEnableVertexAttribArray(loc_vertices)
    glVertexAttribPointer(loc_vertices, 3, GL_FLOAT, False, stride, offset)
    return stride, offset, loc_vertices

def upload_texture(textures):
    glBindBuffer(GL_ARRAY_BUFFER, buffer_VBO[1])
    glBufferData(GL_ARRAY_BUFFER, textures.nbytes, textures, GL_STATIC_DRAW)
    stride = textures.strides[0]
    offset = ctypes.c_void_p(0)
    loc_texture_coord = glGetAttribLocation(program, "texture_coord")
    glEnableVertexAttribArray(loc_texture_coord)
    glVertexAttribPointer(loc_texture_coord, 2, GL_FLOAT, False, stride, offset)
    return stride, offset, loc_texture_coord


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

def main():

    global polygonal_mode, window, program, buffer_VBO, deltaTime
    global verticeInicial_caixa, quantosVertices_caixa

    window, program = initOpenGL(largura, altura)

    if window is None:
        return

    buffer_VBO = glGenBuffers(2)

    # Carregar objetos .obj e textura
    verticeInicial_caixa, quantosVertices_caixa = load_obj_and_texture(
        'objetos/padaria/OBJ/WOOD_WALL.obj', 
        ['objetos/padaria/textures/dark_wood_diff_4k.jpg']
    )

    # Para enviar as coordenadas dos vértices para GPU
    vertices = np.zeros(len(vertices_list), [("position", np.float32, 3)])
    vertices['position'] = vertices_list

    # Upload data - vertex
    stride, offset, loc_vertices = upload_vertex(vertices)

    textures = np.zeros(len(textures_coord_list), [("position", np.float32, 2)]) # duas coordenadas
    textures['position'] = textures_coord_list

    # Upload data - texture
    stride, offset, loc_texture_coord = upload_texture(textures)

    
    glfw.set_key_callback(window,key_event)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)
    glfw.set_cursor_pos_callback(window, mouse_callback)
    glfw.set_scroll_callback(window, scroll_callback)

    # tell GLFW to capture our mouse
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)
    glfw.show_window(window)

    glEnable(GL_DEPTH_TEST)  # Importante para 3D
    polygonal_mode = False 
    lastFrame = 0.0

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

        # Desenha a padaria
        draw_bakery(0.0, 0, ativo, 0, 0, 0, 0, 0, -10, 1, -1, 1, 0)
        
        mat_view = view()
        loc_view = glGetUniformLocation(program, "view")
        glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

        mat_projection = projection()
        loc_projection = glGetUniformLocation(program, "projection")
        glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    
        

        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()