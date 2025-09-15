# --- Funciones de Utilidad y Colores ---
# Para hacer los mensajes más visuales, definimos colores.
readonly GREEN='\033[1;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[1;31m'
readonly NC='\033[0m' # Sin color

# Rutas
PROJECT_DIR="/local/cloudlab-k8s"
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