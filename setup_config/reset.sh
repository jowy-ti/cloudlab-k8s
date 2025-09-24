#!/bin/bash

readonly PROJECT_DIR="/local/repository"
readonly SETUP_DIR="$PROJECT_DIR/setup_config"
readonly VENV_DIR="$PROJECT_DIR/venv"
readonly KUBESPRAY_DIR="$PROJECT_DIR/kubespray"
readonly INVENTORY_FILE="inventory/mycluster/inventory.ini"

# Script para resetear un clúster de Kubernetes desplegado con Kubespray
# y limpiar el entorno de trabajo local.
#
# Se detiene inmediatamente si cualquier comando falla.
set -e

# --- Funciones para mejorar la legibilidad ---
# Imprime un mensaje informativo.
info() {
    echo -e "\n[INFO] $1"
}

# --- Confirmación del Usuario ---
# Añade una capa de seguridad para evitar ejecuciones accidentales.
info "Este script reseteará el clúster de Kubernetes y eliminará el entorno virtual local."
read -p "¿Estás seguro de que quieres continuar? (s/N): " confirmation
if [[ "$confirmation" != "s" && "$confirmation" != "S" ]]; then
    echo "Operación cancelada."
    exit 0
fi

# --- Lógica Principal ---

# Salimos del entorno virtual
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Tienes que salir del entorno virtual con el comando deactive"
    exit 1
else
    echo "Not in a virtual environment. Nothing to deactivate."
fi

# Desinstalar componentes de helm
info "Desinstalando componentes de helm..."

helm list --no-headers | while read -r name rest; do
    if [[ $name != " " ]]; then
        helm uninstall $name
    fi
done

# Activar el entorno virtual
info "Activando el entorno virtual en $VENV_DIR..."
if [[ -f "$VENV_DIR/bin/activate" ]]; then
    source "$VENV_DIR/bin/activate"
else
    echo "[ERROR] No se encontró el entorno virtual. Abortando." >&2
    exit 1
fi

# Cambiar al directorio de Kubespray (CAMBIO CLAVE)
info "Cambiando al directorio de trabajo de Kubespray en $KUBESPRAY_DIR..."
cd "$KUBESPRAY_DIR"

# Ejecutar el playbook de reseteo de Ansible
info "Ejecutando el playbook de reseteo de Kubespray... Esto puede tardar varios minutos."
ansible-playbook -i "$INVENTORY_FILE" -b "reset.yml"

info "¡Proceso de reseteo completado con éxito!"

# Eliminar el entorno virtual
info "Eliminando el entorno virtual..."
# Se usa la ruta absoluta en la variable para evitar problemas
rm -rf "$VENV_DIR"

# Desisntalar python3-venv
sudo apt purge -y python3-venv

# Borrar KUBECONFIG de ~/.bashrc
#sed -i '/KUBECONFIG/d' ~/.bashrc
