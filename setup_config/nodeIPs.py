import sys

# Inputs: env (test/JoelGJ) | node_type (master/worker) | amount_workers

env = sys.argv[1]
node_type = sys.argv[2]
inventory_file = "/local/cloudlab-k8s/kubespray/inventory/mycluster/inventory.ini"

def insert_line(role, entity):

    # Leer inventario actual
    with open(inventory_file, "r") as f:
        lines = f.readlines()

    for j, line in enumerate(lines):
        if line.strip() == role:
            # Insertar justo después de este bloque
            lines.insert(j + 1, entity)
            break

    # Guardar cambios
    with open(inventory_file, "w") as f:
        f.writelines(lines)


if (node_type == "worker"):
    workers = int(sys.argv[3])
    nodes = []
    ansible_hosts = []
    role = "[kube_node]"

    # Lista de workers
    for i in range(workers):
            nodes.append(f"node{i+2}")

    if env == "JoelGJ":
        ansible_hosts = nodes
        user = "JoelGJ"

    else:
        for num in range(workers):
            ansible_hosts.append(f"192.168.122.{10+num+2}")
        user = "test"

    for i in range(workers):

        entity = f"{nodes[i]} ansible_host={ansible_hosts[i]} ansible_user={user} ansible_python_interpreter=/usr/bin/python3.12\n"

        insert_line(role, entity)

        print(f"Nodo {nodes[i]} agregado a {role}")

else:
    node = "node1"
    role = "[kube_control_plane]"

    if env == "JoelGJ":
        ansible_host = node
        user = "JoelGJ"

    else:
        ansible_host = "192.168.122.11"
        user = "test"

    entity = f"{node} ansible_host={ansible_host} ansible_user={user} ansible_python_interpreter=/usr/bin/python3.12 ansible_connection=local\n"

    insert_line(role, entity)

    print(f"Nodo {node} agregado a {role}")
