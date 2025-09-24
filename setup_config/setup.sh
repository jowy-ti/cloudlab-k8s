#!/bin/bash

# Creación y configuración del cluster

# Se detiene inmediatamente si cualquier comando falla.
set -e

NODES=""
export readonly NODENUM=$(echo $HOSTNAME | cut -d . -f 1)
PWD=$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Comprobación de que el repositorio está en el directrio correcto
if [[ $PWD != "/local"* ]]; then
    echo "El projecto no está dentro de /local"
    exit 1

elif [[ $PWD != "/local/repository"* ]]; then
    echo "Cambiando nombre del directorio del repo a 'repository'"
    cd /local
    sudo mv "cloudlab-k8s" "repository"
fi

# Funciones y variables auxiliares
source /local/repository/setup_config/env.sh

# Comprobación de parámetros pasados
if [ "$#" -ne 2 ] || [ "$1" != "-n" ]; then
    log_error "Debes pasar la cantidad de workers que va a tener el cluster de la siguiente forma:\n./scale.sh -n num_workers"
    exit 1

elif [[ ! $2 =~ ^[0-9]+$ ]]; then
    log_error "La variable \$2 NO es un número natural."
    exit 1
fi

export readonly NUM_WORKERS=$2

# Pasos para establecer las claves en los nodos
$SETUP_DIR/setup-ssh.sh

exit 0

# Si el nodo no es el master se detiene la configuración
if [[ $NODENUM != "node1" ]]; then
    exit 0
fi

log_info "Validaciones correctas. Iniciando despliegue del cluster..."
echo

# Se configura e inicialliza el nodo master
if command -v kubectl &> /dev/null; then
    NODES=$(kubectl get nodes -o custom-columns=NAME:.metadata.name --no-headers)
fi

if [[ -z $NODES ]] || [$NODES != "node1"]; then
    $SETUP_DIR/iniCluster.sh

else
    log_info "Ya existía el cluster con el nodo master, se procede a añadir workers"
fi

# Se añaden los nodos worker
$SETUP_DIR/scale.sh

log_success "Proceso de creación y escalado del cluster completado." 