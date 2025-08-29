inventory_file = "/home/JoelGJ/cloudlab-k8s/kubespray/inventory/mycluster/inventory.ini"

nodes = ["node1", "node2", "node3"]
user = "JoelGJ"

for i in range(3):

    # Leer inventario actual
    with open(inventory_file, "r") as f:
        lines = f.readlines()

        entity = f"{nodes[i]} ansible_host={nodes[i]} ansible_user={user} ansible_python_interpreter=/usr/bin/python3.12 "

    if i == 0:
        role = "[kube_control_plane]"
        entity += "ansible_connection=local\n"
    else:
        role = "[kube_node]"
        entity += "\n"

    # Buscar dónde insertar
    for j, line in enumerate(lines):
        if line.strip() == role:
            # Insertar justo después de este bloque
            lines.insert(j + 1, entity)
            break

    # Guardar cambios
    with open(inventory_file, "w") as f:
        f.writelines(lines)

    print(f"Nodo {nodes[i]} agregado a {role}")

