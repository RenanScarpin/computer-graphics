import glfw
from OpenGL.GL import *
import numpy as np
import math

def main():
    # Inicializa o GLFW
    print("Inicializando o GLFW...")
    if not glfw.init():
        print("Falha na inicialização do GLFW")
        return None, None

    # Cria uma janela
    print("Criando a janela...")
    glfw.window_hint(glfw.VISIBLE, glfw.FALSE)

    if not window:
        print("Erro ao criar a janela")
        glfw.terminate()
        return

    glfw.make_context_current(window)

    # Define a cor de fundo para o teste
    glClearColor(0.2, 0.3, 0.3, 1.0)

    while not glfw.window_should_close(window):
        # Limpa a tela
        glClear(GL_COLOR_BUFFER_BIT)

        # Troca os buffers para exibir a janela
        glfw.swap_buffers(window)
        
        # Processa eventos de entrada
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()