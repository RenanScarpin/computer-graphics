import math

def normalizar(v):
    x, y, z = v
    norma = math.sqrt(x*x + y*y + z*z)
    if norma == 0:
        return [0.0, 0.0, 0.0]
    return [x/norma, y/norma, z/norma]

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

def add_espinhos(vertices, faces, alt_espinho = 0.05, passo = 10):

    novas_faces = []

    for id, face in enumerate(faces):
        a, b, c = face 
        va = vertices[a]
        vb = vertices[b]
        vc = vertices[c]

        #algumas faces com espinho
        if id % passo == 0:

            centro = [
                (va[0] + vb[0] + vc[0]) / 3.0,
                (va[1] + vb[1] + vc[1]) / 3.0,
                (va[2] + vb[2] + vc[2]) / 3.0,
            ]

            dir = normalizar(centro)

            ponta = [
                centro[0] + dir[0]*alt_espinho,
                centro[1] + dir[1]*alt_espinho,
                centro[2] + dir[2]*alt_espinho,
            ]

            ind_ponta = len(vertices)
            vertices.append(ponta)

            novas_faces.append([a, b, ind_ponta])
            novas_faces.append([b, c, ind_ponta])
            novas_faces.append([c, a, ind_ponta])
        else:
            novas_faces.append(face)
    
    return vertices, novas_faces


vertices_final, faces = gerar_esfera()
vertices_final, faces = add_espinhos(vertices_final, faces)

with open("baiacu.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")

    for a, b, c in faces:
        f.write(f"f {a+1} {b+1} {c+1}\n")
 