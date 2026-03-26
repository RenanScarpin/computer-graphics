import math
import numpy as np

num_vertices = 100
pi = math.pi
radius = 0.2

#pontos do circulo 
vertices = np.zeros((num_vertices, 3), dtype=np.float32)
#assume z = 0 -> gerando os pontos da circunferencia 
angle = 0.0
for i in range(num_vertices):
    angle += 2 * pi / num_vertices
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius
    vertices[i] = [x, y, 0]

#vértice central
centro = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)

vertices_final = np.vstack([centro, vertices])

faces = []
#faces = conectar i, i+1 e centro pra triangularizar
for i in range(num_vertices):
    a = 1
    b = i + 2
    c = ((i + 1) % num_vertices) + 2
    faces.append((a, b, c))

with open("fundo_helice.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")

    for a, b, c in faces:
        f.write(f"f {a} {b} {c}\n")
