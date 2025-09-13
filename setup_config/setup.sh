#!/bin/bash

# Contenido del Script
#===============================================================================================================
# sudo apt update

# sudo apt install python3-venv

# cp $SETUP_DIR/inventory.ini $KUBESPRAY_DIR/$INVENTORY_FILE

# python3 $SETUP_DIR/$1

# python3 -m venv $VENV_DIR

# source $VENV_DIR/bin/activate

# cd $KUBESPRAY_DIR

# pip3 install -U -r requirements.txt

# ansible-galaxy collection install community.kubernetes

# ansible -i $INVENTORY_FILE all -m ping

# ansible-playbook -i $INVENTORY_FILE -b cluster.yml

# mkdir -p $PROJECT_DIR/.kube

# sudo cp -i /etc/kubernetes/admin.conf $PROJECT_DIR/.kube/config

# sudo chown $(id -u):$(id -g) $PROJECT_DIR/.kube/config

# helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# helm repo add nvidia https://helm.ngc.nvidia.com/nvidia

# helm repo update

# helm install prometheus prometheus-community/kube-prometheus-stack -f $SETUP_DIR/prometheus_stack_values.yaml

# helm install gpu-operator nvidia/gpu-operator
#===============================================================================================================

# ==============================================================================
# Script para automatizar la instalación de un clúster de Kubernetes
# con Kubespray, Prometheus y el operador de GPU de NVIDIA.
#
# Incluye comprobación de errores y mensajes de estado para cada paso.
# ==============================================================================

# Detiene el script inmediatamente si un comando falla
set -e

# --- Funciones de Utilidad y Colores ---
# Para hacer los mensajes más visuales, definimos colores.
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
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


# --- INICIO DEL SCRIPT ---
log_info "Iniciando la configuración del clúster de Kubernetes..."

# 0. Ajustar permisos del repo
run_command "sudo chown -R $(id -un):$(id -gn) $PROJECT_DIR" "Cambiando permisos del repositorio"

# 1. Actualizar paquetes del sistema
run_command "sudo apt update" "Actualizando la lista de paquetes del sistema"

# 2. Instalar el paquete para entornos virtuales de Python
run_command "sudo apt install -y python3-venv" "Instalando python3-venv"

# 3. Copiar el fichero de inventario
# Comprobamos primero que los directorios y el fichero de origen existen
log_info "Preparando la copia del fichero de inventario..."
if [ ! -d "$KUBESPRAY_DIR/inventory/mycluster" ]; then
    log_error "El directorio de destino para el inventario no existe: $KUBESPRAY_DIR/inventory/mycluster"
fi
if [ ! -f "$SETUP_DIR/inventory.ini" ]; then
    log_error "El fichero de inventario de origen no existe: $SETUP_DIR/inventory.ini"
fi
run_command "cp $SETUP_DIR/inventory.ini $KUBESPRAY_DIR/$INVENTORY_FILE" "Copiando el fichero de inventario"

# 4. Ejecutar script de configuración de IPs
run_command "python3 $SETUP_DIR/nodeIPs.py $MY_USER master" "Ejecutando el script para configurar las IPs de los nodos"

# 5. Crear y activar el entorno virtual de Python
run_command "python3 -m venv $VENV_DIR" "Creando el entorno virtual de Python"
log_info "Activando el entorno virtual..."
# 'source' es un comando de shell, no se puede usar directamente en 'run_command'
if [ -f "$VENV_DIR/bin/activate" ]; then
    source $VENV_DIR/bin/activate
    log_success "Entorno virtual activado."
else
    log_error "No se encontró el script de activación del entorno virtual."
fi

# 6. Instalar dependencias de Kubespray
log_info "Cambiando al directorio 'kubespray'"
cd $KUBESPRAY_DIR || log_error "No se pudo cambiar al directorio 'kubespray'"
run_command "pip3 install -U -r requirements.txt" "Instalando dependencias de Python desde requirements.txt"
run_command "ansible-galaxy collection install community.kubernetes" "Instalando la colección de Ansible 'community.kubernetes'"

# 7. Verificar la conexión de Ansible y desplegar el clúster
run_command "ansible -i $INVENTORY_FILE all -m ping" "Verificando la conexión con todos los nodos vía Ansible"
run_command "ansible-playbook -i $INVENTORY_FILE -b cluster.yml" "Desplegando el clúster de Kubernetes (esto puede tardar bastante)"

# 8. Configurar kubectl para el usuario actual
log_info "Configurando kubectl..."
mkdir -p "$PROJECT_DIR/.kube"
run_command "sudo cp /etc/kubernetes/admin.conf $PROJECT_DIR/.kube/config" "Copiando la configuración de admin de Kubernetes"
run_command "sudo chown $($MY_USER):$($MY_GROUP) $PROJECT_DIR/.kube/config" "Ajustando los permisos del fichero de configuración"
run_command "echo 'export KUBECONFIG=$PROJECT_DIR/.kube/config' >> ~/.bashrc" "Añadiendo la variable de entorno al perfil del shell"
run_command "source ~/.bashrc" "Cargando la variable en la sesión actual"

# 9. Añadir repositorios de Helm y desplegar Prometheus y el operador de GPU
log_info "Configurando Helm..."
run_command "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts" "Añadiendo el repositorio de Helm de Prometheus Community"
run_command "helm repo add nvidia https://helm.ngc.nvidia.com/nvidia" "Añadiendo el repositorio de Helm de NVIDIA"
run_command "helm repo update" "Actualizando los repositorios de Helm"

log_info "Desplegando componentes con Helm..."
run_command "helm install prometheus prometheus-community/kube-prometheus-stack -f $SETUP_DIR/prometheus_stack_values.yaml" "Instalando la stack de Prometheus"
run_command "helm install gpu-operator nvidia/gpu-operator" "Instalando el operador de GPU de NVIDIA"

log_success "¡Script finalizado! El clúster de Kubernetes y los componentes adicionales deberían estar listos."
echo "Puedes verificar el estado de los nodos con el comando: kubectl get nodes"
echo "Y el estado de los pods en todos los namespaces con: kubectl get pods --all-namespaces"
