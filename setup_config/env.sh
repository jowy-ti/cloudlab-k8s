#!/bin/bash

# --- Funciones de Utilidad y Colores ---
# Para hacer los mensajes más visuales, definimos colores.
readonly GREEN='\033[1;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[1;31m'
readonly NC='\033[0m' # Sin color

# Rutas
readonly PROJECT_DIR="/local/repository"
readonly SETUP_DIR="$PROJECT_DIR/setup_config"
readonly MANIFESTS_DIR="$SETUP_DIR/manifests"
readonly VENV_DIR="$PROJECT_DIR/venv"
readonly KUBESPRAY_DIR="$PROJECT_DIR/kubespray"
readonly INVENTORY_FILE="inventory/mycluster/inventory.ini"

# Usuario y Grupo
readonly MY_USER="$(id -un)"
readonly MY_GROUP="$(id -gn)"

# Función para registrar mensajes de información
log_info() {
    echo -e "${YELLOW}[INFO] $1${NC}" >> $PROJECT_DIR/logs.log
}

# Función para registrar mensajes de éxito
log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" >> $PROJECT_DIR/logs.log
}

# Función para registrar errores y salir
log_error() {
    local message="${RED}[ERROR] $1. Abortando misión.${NC}"
    echo -e "$message" >&2
    echo -e "$message" >> $PROJECT_DIR/logs.log
    exit 1
}

# Función para ejecutar un comando y comprobar su resultado
run_command() {
    local cmd="$1"
    local msg="$2"

    log_info "$msg"
   
    if ! eval "$cmd"; then
        log_error "Falló la ejecución de: '$cmd'"
    fi
    log_success "$msg - ¡Completado!"
    echo
}

export -f log_info
export -f log_success
export -f log_error
export -f run_command

export PROJECT_DIR
export SETUP_DIR
export MANIFESTS_DIR
export VENV_DIR
export KUBESPRAY_DIR
export INVENTORY_FILE
export MY_USER
export MY_GROUP