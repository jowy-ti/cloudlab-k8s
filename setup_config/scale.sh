#!/bin/bash

# Contenido del Script
# ===============================================================================================================

# python3 $SETUP_DIR/nodeIPs.py $MY_USER worker $2

# cd $KUBESPRAY_DIR

# ansible -i $INVENTORY_FILE all -m ping

# ansible-playbook -i $INVENTORY_FILE -b scale.yml

# helm install prometheus prometheus-community/kube-prometheus-stack -f $SETUP_DIR/prometheus_stack_values.yaml

# helm install gpu-operator nvidia/gpu-operator

# ===============================================================================================================

# ==============================================================================
# Script para escalar el cluster de Kubernetes
# con Kubespray, Prometheus y el operador de GPU de NVIDIA.
#
# Incluye comprobación de errores y mensajes de estado para cada paso.
# ==============================================================================

# Detiene el script inmediatamente si un comando falla
set -e

# --- Funciones de Utilidad y Colores ---
# Para hacer los mensajes más visuales, definimos colores.
readonly GREEN='\033[1;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[1;31m'
readonly NC='\033[0m' # Sin color

# Rutas
PROJECT_DIR="/opt/cloudlab-k8s"
SETUP_DIR="$PROJECT_DIR/setup_config"
VENV_DIR="$PROJECT_DIR/venv"
KUBESPRAY_DIR="$PROJECT_DIR/kubespray"
INVENTORY_FILE="inventory/mycluster/inventory.ini"

# User 
MY_USER=$(id -un)
MY_GROUP=$(id -gn)

# Función para registrar mensajes de información
log_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

# Función para registrar mensajes de éxito
log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Función para registrar errores y salir
log_error() {
    echo -e "${RED}[ERROR] $1. Abortando misión.${NC}" >&2
    exit 1
}

# Función para ejecutar un comando y comprobar su resultado
run_command() {
    local cmd="$1"
    local msg="$2"

    log_info "$msg"
    # Ejecutamos el comando, redirigiendo la salida a /dev/null si no queremos verla
    # o dejándola visible para depuración. Para este script, es útil ver la salida.
    if ! eval "$cmd"; then
        log_error "Falló la ejecución de: '$cmd'"
    fi
    log_success "$msg - ¡Completado!"
    echo # Añadir una línea en blanco para mayor claridad
}

# Comprobación de parámetros pasados
if [ "$#" -ne 2 ] || [ "$1" != "-n" ]; then
    log_error "Debes pasar la cantidad de workers que va a tener el cluster de la siguiente forma:\n./scale.sh -n num_workers"
    exit 1

elif [[ ! $2 =~ ^[0-9]+$ ]]; then
    log_error "La variable \$2 NO es un número."
    exit 1
fi

# Ejecutar script de configuración de IPs
run_command "sed -i '/\[kube_node\]/q' $KUBESPRAY_DIR/$INVENTORY_FILE" "Eliminando workers actuales en inventory.ini"
run_command "python3 $SETUP_DIR/nodeIPs.py $MY_USER worker $2" "Ejecutando el script para configurar las IPs de los nodos"
log_success "Nodos añadidos en el inventory.ini de kubespray"

# Activar entorno virtual
log_info "Activando entorno virtual"
if [ -f "$VENV_DIR/bin/activate" ] && [[ -z "$VIRTUAL_ENV" ]]; then
    source $VENV_DIR/bin/activate
    log_success "Entorno virtual activado."
fi

# Verificar la conexión de Ansible y añadimos nodos al cluster
log_info "Cambiando al directorio 'kubespray'"
cd $KUBESPRAY_DIR || log_error "No se pudo cambiar al directorio 'kubespray'"
run_command "ansible -i $INVENTORY_FILE all -m ping" "Verificando la conexión con todos los nodos vía Ansible"
run_command "ansible-playbook -i $INVENTORY_FILE -b scale.yml" "Escalando el clúster de Kubernetes (esto puede tardar bastante)"

# Instalando y aplicando los charts de GPU operator y prometheus-stack
log_info "Desplegando componentes con Helm..."
run_command "helm install prometheus prometheus-community/kube-prometheus-stack -f $SETUP_DIR/prometheus_stack_values.yaml" "Instalando la stack de Prometheus"
run_command "helm install gpu-operator nvidia/gpu-operator" "Instalando el operador de GPU de NVIDIA"

log_success "Se han añadido los nodos worker al cluster correctamente"