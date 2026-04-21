from OpenGL.GL import *
import glfw
import glm
import numpy as np
from utils import * 
from shader_s import *

altura = 700
largura = 700
ativo = [0, 0, 0, 0, 0]

# Inicializando a posição da câmera usando glm.vec3
cameraPos = glm.vec3(0.0, -3.0, 5.0)
cameraFront = glm.vec3(0.0, 0.0, -1.0)
cameraUp = glm.vec3(0.0, 1.0, 0.0)

firstMouse = True

yaw   = -90.0  # yaw is initialized to -90.0 degrees
pitch =  0.0
lastX = largura / 2.0
lastY = altura / 2.0
fov   = 90.0

# timing
deltaTime = 0.0  # time between current frame and last frame
lastFrame = 0.0

firstMouse = True
yaw = -90.0 
pitch = 0.0
lastX = largura / 2
lastY = altura / 2


def key_event(window, key, scancode, action, mods):
    global cameraPos, cameraFront, cameraUp, polygonal_mode

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
    
    if key == glfw.KEY_1 and action == glfw.PRESS:
        if ativo[1]:
            ativo[1] = 0
        else:
            ativo[1] = 1
    
    if key == glfw.KEY_2 and action == glfw.PRESS:
        if ativo[2]:
            ativo[2] = 0
        else:
            ativo[2] = 1
    
    if key == glfw.KEY_3 and action == glfw.PRESS:
        if ativo[3]:
            ativo[3] = 0
        else:
            ativo[3] = 1
    
    if key == glfw.KEY_4 and action == glfw.PRESS:
        if ativo[4]:
            ativo[4] = 0
        else:
            ativo[4] = 1


def framebuffer_size_callback(window, largura, altura):
    glViewport(0, 0, largura, altura)

# Mouse callback (alterado para usar glm)
def mouse_callback(window, xpos, ypos):
    global cameraFront, lastX, lastY, firstMouse, yaw, pitch
   
    if firstMouse:
        lastX = xpos
        lastY = ypos
        firstMouse = False

    xoffset = xpos - lastX
    yoffset = lastY - ypos  # reversed since y-coordinates go from bottom to top
    lastX = xpos
    lastY = ypos

    sensitivity = 0.1  # change this value to your liking
    xoffset *= sensitivity
    yoffset *= sensitivity

    yaw += xoffset
    pitch += yoffset

    # make sure that when pitch is out of bounds, screen doesn't get flipped
    if pitch > 89.0:
        pitch = 89.0
    if pitch < -89.0:
        pitch = -89.0

    # Alterando a criação de front para glm
    front = glm.vec3(
        glm.cos(glm.radians(yaw)) * glm.cos(glm.radians(pitch)),
        glm.sin(glm.radians(pitch)),
        glm.sin(glm.radians(yaw)) * glm.cos(glm.radians(pitch))
    )
    cameraFront = glm.normalize(front)

# Scroll callback
def scroll_callback(window, xoffset, yoffset):
    global fov

    fov -= yoffset
    if fov < 1.0:
        fov = 1.0
    if fov > 45.0:
        fov = 45.0

# Matrizes de transformação e modelagem
def model(angle, r_x, r_y, r_z, t_x, t_y, t_z, s_x, s_y, s_z):
    angle = glm.radians(angle)  # Converte o ângulo para radianos com glm
    
    matrix_transform = glm.mat4(1.0)  # Cria uma matriz identidade 4x4
    
    # Translação
    matrix_transform = glm.translate(matrix_transform, glm.vec3(t_x, t_y, t_z)) 
    
    # Rotação
    if angle != 0:
        if r_x:
            matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(1.0, 0.0, 0.0))  # Rotação no eixo x
        if r_y:
            matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(0.0, 1.0, 0.0))  # Rotação no eixo y
        if r_z:
            matrix_transform = glm.rotate(matrix_transform, angle, glm.vec3(0.0, 0.0, 1.0))  # Rotação no eixo z
    
    # Aplica a escala
    matrix_transform = glm.scale(matrix_transform, glm.vec3(s_x, s_y, s_z))
    
    return matrix_transform

def view():
    global cameraPos, cameraFront, cameraUp
    mat_view = glm.lookAt(cameraPos, cameraPos + cameraFront, cameraUp)
    return np.array(mat_view)

def projection():
    global altura, largura
    mat_projection = glm.perspective(glm.radians(fov), largura / altura, 0.1, 100.0)
    return np.array(mat_projection)

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

def main():

    global window, program, buffer_VBO
    global verticeInicial_caixa, quantosVertices_caixa

    window, program = initOpenGL(largura, altura)

    if window is None:
        return

    buffer_VBO = glGenBuffers(2)

    # Carregar objetos .obj e textura
    verticeInicial_caixa, quantosVertices_caixa = load_obj_and_texture(
        'objetos/padaria/padaria.obj', 
        ['objetos/padaria/padaria.jpg']
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

    # Captura o mouse
    glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED)

    glfw.show_window(window)

    glEnable(GL_DEPTH_TEST)  # Importante para 3D
    polygonal_mode = False 

    lastFrame = glfw.get_time() 
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

        # Envia as matrizes de visualização e projeção
        mat_view = view()
        loc_view = glGetUniformLocation(program, "view")
        glUniformMatrix4fv(loc_view, 1, GL_TRUE, mat_view)

        mat_projection = projection()
        loc_projection = glGetUniformLocation(program, "projection")
        glUniformMatrix4fv(loc_projection, 1, GL_TRUE, mat_projection)    

        # Desenha a padaria
        draw_bakery(0.0, 0, ativo, 0, 0, 0, 0, 0, -10, 0.125, 0.125, 0.125, 0)
        
        glfw.swap_buffers(window)

    glfw.terminate()

if __name__ == "__main__":
    main()