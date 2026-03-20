import math

def gerar_esfera(raio=0.2, lat=20, lon=30):
    
    vertices = []
    faces = []

    # vértices
    for i in range(lat + 1):
        phi = math.pi*i/lat #[0,pi]

        for j in range(lon + 1):
            theta = 2.0*math.pi*j/lon #[0, 2pi]

            x = raio*math.sin(phi)*math.cos(theta)
            y = raio*math.cos(phi)
            z = raio*math.sin(phi)*math.sin(theta)

            vertices.append([x, y, z])

    # faces
    for i in range(lat):
        for j in range(lon):
            v0 = i*(lon+1)+j
            v1 = v0+1
            v2 = v0+(lon+1)
            v3 = v2+1

            faces.append([v0, v1, v2])
            faces.append([v1, v3, v2])

    return vertices, faces

vertices_final, faces = gerar_esfera()

with open("baiacu.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")

    for a, b, c in faces:
        f.write(f"f {a} {b} {c}\n")
