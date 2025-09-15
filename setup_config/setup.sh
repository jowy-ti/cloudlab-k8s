#!/bin/bash

# Creación y configuración del cluster

# Se detiene inmediatamente si cualquier comando falla.
set -e

NODES=""

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

log_info "Validaciones correctas. Iniciando despliegue del cluster..."
echo

# Se configura e inicialliza el nodo master
if command -v kubectl &> /dev/null; then
    NODES=$(kubectl get nodes -o custom-columns=NAME:.metadata.name --no-headers)
fi

if [[ -z $NODES ]] || [$NODES != "node1"]; then
    $SETUP_DIR/iniCluster.sh

else; then
    log_info "Ya existía el cluster con el nodo master, se procede a añadir workers"
fi
# Se añaden los nodos worker
$SETUP_DIR/scale.sh

log_success "Proceso de creación y escalado del cluster completado." 