#!/bin/bash

# ==============================================================================
# Script para escalar el cluster de Kubernetes
# con Kubespray, Prometheus y el operador de GPU de NVIDIA.
#
# Incluye comprobación de errores y mensajes de estado para cada paso.
# ==============================================================================

# Detiene el script inmediatamente si un comando falla
set -e

# Ejecutar script de configuración de IPs
run_command "sed -i '/\[kube_node\]/q' $KUBESPRAY_DIR/$INVENTORY_FILE" "Eliminando workers actuales en inventory.ini"
run_command "python3 $SETUP_DIR/nodeIPs.py $MY_USER worker $NUM_WORKERS" "Ejecutando el script para configurar las IPs de los nodos"
log_success "Nodos añadidos en el inventory.ini de kubespray"

# Activar entorno virtual
log_info "Activando entorno virtual"
if [[ -f "$VENV_DIR/bin/activate" ]] && [[ -z "$VIRTUAL_ENV" ]]; then
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
run_command "helm repo update" "Actualizando los repositorios de Helm"
run_command "helm install prometheus prometheus-community/kube-prometheus-stack -f $SETUP_DIR/prometheus_stack_values.yaml --namespace monitoring --create-namespace" "Instalando la stack de Prometheus"
run_command "helm install gpu-operator nvidia/gpu-operator --namespace gpu-operator --create-namespace" "Instalando el operador de GPU de NVIDIA"

log_success "Se han añadido los nodos worker al cluster correctamente"