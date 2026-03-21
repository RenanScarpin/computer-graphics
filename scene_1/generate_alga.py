import math

"""
Função seno triangularizada pra gerar a alga 
Argumentos:
#altura da alga, quantas divisões ao longo da altura, 
# largura inicial, ampltiude ("variação lateral"), 
# frequencia (quantidade de ondulações), deslocamento da senoide, posição no eixo z 
"""
def gerar_alga(altura=0.9, segmentos=30, largura=0.08, amplitude=0.2, frequencia=6.0, z=0.0):
    
    vertices = []
    faces = []

    #vou calcular pra "segmentos pedaços" um ponto naquele "tempo"
    #assim posso fazer simétrico considerando uma largura_local
    for i in range(segmentos+1):

        #Em que pedaço eu to? 
        t = i/segmentos
        y = t*altura

        #eixo principal da alga em y 
        #Ampltiude controle o efeito "lateral" e frequência a quantidade de oscilações
        x_centro = amplitude*math.sin(frequencia*y)

        #pra afinar a ponta -> largura diminui conforme sobe 
        largura_local = largura*(1.0-0.7*t)

        v_esq = [x_centro-largura_local/2.0, y, z]
        v_dir = [x_centro+largura_local/2.0, y, z]

        vertices.append(v_esq)
        vertices.append(v_dir)

    # triangulação da tira
    for i in range(segmentos):
        base = 2 * i

        # índices dos 4 vértices do quad
        v0 = base
        v1 = base + 1
        v2 = base + 2
        v3 = base + 3

        faces.append([v0, v1, v2])
        faces.append([v1, v3, v2])

    return vertices, faces

vertices_final, faces = gerar_alga()

with open("alga.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")

    for a, b, c in faces:
        f.write(f"f {a} {b} {c}\n")
