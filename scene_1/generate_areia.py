def gerar_areia(width=3.0, height=0.1, depth=2.0, pos_y=-1.0):
    """
    Gera uma caixa plana de areia no fundo da cena
    width: largura (x)
    height: altura (y) - deve ser pequena
    depth: profundidade (z)
    pos_y: posição y (fundo)
    """
    
    vertices = []
    faces = []
    
    # Half dimensions
    hw = width / 2.0
    hh = height / 2.0
    hd = depth / 2.0
    
    # Bottom face (y = pos_y - hh)
    y_bottom = pos_y - hh
    # Top face (y = pos_y + hh)
    y_top = pos_y + hh
    
    # Define 8 vertices
    # Bottom face (y_bottom)
    vertices.append([-hw, y_bottom, -hd])  # 0
    vertices.append([hw, y_bottom, -hd])   # 1
    vertices.append([hw, y_bottom, hd])    # 2
    vertices.append([-hw, y_bottom, hd])   # 3
    
    # Top face (y_top)
    vertices.append([-hw, y_top, -hd])     # 4
    vertices.append([hw, y_top, -hd])      # 5
    vertices.append([hw, y_top, hd])       # 6
    vertices.append([-hw, y_top, hd])      # 7
    
    # Define 6 faces (2 triangles each for 6 sides = 12 triangles total)
    # Bottom face (y_bottom) - normal pointing down
    faces.append([0, 3, 1])
    faces.append([1, 3, 2])
    
    # Top face (y_top) - normal pointing up
    faces.append([4, 5, 7])
    faces.append([5, 6, 7])
    
    # Front face (z = -hd)
    faces.append([0, 1, 4])
    faces.append([1, 5, 4])
    
    # Back face (z = hd)
    faces.append([2, 3, 6])
    faces.append([3, 7, 6])
    
    # Left face (x = -hw)
    faces.append([3, 0, 7])
    faces.append([0, 4, 7])
    
    # Right face (x = hw)
    faces.append([1, 2, 5])
    faces.append([2, 6, 5])
    
    return vertices, faces

vertices_final, faces = gerar_areia()

with open("areia.txt", "w", encoding="utf-8") as f:
    for x, y, z in vertices_final:
        f.write(f"v {x} {y} {z}\n")
    
    for a, b, c in faces:
        f.write(f"f {a+1} {b+1} {c+1}\n")
