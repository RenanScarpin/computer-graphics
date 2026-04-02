import math

"""
Função seno triangularizada pra gerar a alga 
Argumentos:
#altura da alga, quantas divisões ao longo da altura, 
# largura inicial, ampltiude ("variação lateral"), 
# frequencia (quantidade de ondulações), deslocamento da senoide, posição no eixo z, profundidade (espessura)
"""
def gerar_alga(altura=0.9, segmentos=30, largura=0.08, amplitude=0.2, frequencia=6.0, z=0.0, profundidade=-0.05):
    
    vertices = []
    faces = []

    # Gerar vértices da frente
    for i in range(segmentos+1):
        t = i/segmentos
        y = t*altura
        x_centro = amplitude*math.sin(frequencia*y)
        largura_local = largura*(1.0-0.7*t)

        v_esq = [x_centro-largura_local/2.0, y, z]
        v_dir = [x_centro+largura_local/2.0, y, z]

        vertices.append(v_esq)
        vertices.append(v_dir)

    # Gerar vértices de trás (cópia com z deslocado)
    offset_back = len(vertices)
    for i in range(segmentos+1):
        t = i/segmentos
        y = t*altura
        x_centro = amplitude*math.sin(frequencia*y)
        largura_local = largura*(1.0-0.7*t)

        v_esq = [x_centro-largura_local/2.0, y, z - profundidade]
        v_dir = [x_centro+largura_local/2.0, y, z - profundidade]

        vertices.append(v_esq)
        vertices.append(v_dir)

    # Faces da frente
    for i in range(segmentos):
        base = 2 * i
        v0 = base
        v1 = base + 1
        v2 = base + 2
        v3 = base + 3

        faces.append([v0, v1, v2])
        faces.append([v1, v3, v2])

    # Faces de trás (mesma triangulação, mas com offset)
    for i in range(segmentos):
        base = 2 * i + offset_back
        v0 = base
        v1 = base + 1
        v2 = base + 2
        v3 = base + 3

    #    faces.append([v0, v2, v1])  # invertido para normal para fora
    #    faces.append([v1, v2, v3])

    # Faces laterais (conectando frente e trás)
    #for i in range(segmentos):
    #    front_left = 2 * i
    #    front_right = 2 * i + 1
    #    back_left = 2 * i + offset_back
    #    back_right = 2 * i + 1 + offset_back

        # Lado esquerdo
    #    faces.append([front_left, back_left, front_left + 2])
    #    faces.append([back_left, back_left + 2, front_left + 2])

        # Lado direito
    #    faces.append([front_right, front_right + 2, back_right])
    #    faces.append([back_right, front_right + 2, back_right + 2])

    return vertices, faces

vertices_final, faces = gerar_alga()

with open("alga.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")

    for a, b, c in faces:
        f.write(f"f {a} {b} {c}\n")
