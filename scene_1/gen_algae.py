import math

#Generates vertices and faces for algae using a sine wave pattern
def gerar_alga(height=0.9, segments=30, width=0.08, amplitude=0.2, frequency=6.0, z=0.0):
    
    vertices = []
    faces = []

    # Vertices
    for i in range(segments+1):
        t = i/segments
        y = t*height
        x_centro = amplitude*math.sin(frequency*y)
        width_local = width*(1.0-0.7*t)

        v_esq = [x_centro-width_local/2.0, y, z]
        v_dir = [x_centro+width_local/2.0, y, z]

        vertices.append(v_esq)
        vertices.append(v_dir)

    # Faces
    for i in range(1 , segments):
        base = 2 * i
        v0 = base
        v1 = base + 1
        v2 = base + 2
        v3 = base + 3

        faces.append([v0, v1, v2])
        faces.append([v1, v3, v2])

    return vertices, faces

vertices_final, faces = gerar_alga()

# Writes to file
with open("alga.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")

    for a, b, c in faces:
        f.write(f"f {a} {b} {c}\n")
