#!/bin/bash

# --- Funciones de Utilidad y Colores ---
# Para hacer los mensajes más visuales, definimos colores.
readonly GREEN='\033[1;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[1;31m'
readonly NC='\033[0m' # Sin color

# Rutas
export readonly PROJECT_DIR="/local/repository"
export readonly SETUP_DIR="$PROJECT_DIR/setup_config"
export readonly VENV_DIR="$PROJECT_DIR/venv"
export readonly KUBESPRAY_DIR="$PROJECT_DIR/kubespray"
export readonly INVENTORY_FILE="inventory/mycluster/inventory.ini"

# Usuario y Grupo
export readonly MY_USER=$(id -un)
export readonly MY_GROUP=$(id -gn)

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