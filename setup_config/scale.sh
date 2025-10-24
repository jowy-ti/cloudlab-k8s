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
    source "$VENV_DIR/bin/activate"
    log_success "Entorno virtual activado."
fi

# Verificar la conexión de Ansible y añadimos nodos al cluster
log_info "Cambiando al directorio 'kubespray'"
cd "$KUBESPRAY_DIR" || log_error "No se pudo cambiar al directorio 'kubespray'"
run_command "ansible -i $INVENTORY_FILE all -m ping" "Verificando la conexión con todos los nodos vía Ansible"
run_command "ansible-playbook -i $INVENTORY_FILE -b scale.yml" "Escalando el clúster de Kubernetes (esto puede tardar bastante)"

# Añadir repositorios de Helm
log_info "Configurando Helm..."
run_command "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts" "Añadiendo el repositorio de Helm de Prometheus Community"
run_command "helm repo add nvidia https://helm.ngc.nvidia.com/nvidia" "Añadiendo el repositorio de Helm de NVIDIA"
run_command "helm repo add kwok https://kwok.sigs.k8s.io/charts/" "Añadiendo repo de kwok"

# Instalando helm charts
log_info "Desplegando componentes con Helm..."
run_command "helm repo update" "Actualizando los repositorios de Helm"
run_command "helm install prometheus prometheus-community/kube-prometheus-stack -f $MANIFESTS_DIR/prometheus_stack_values.yaml --namespace monitoring --create-namespace" "Instalando la stack de Prometheus"
# run_command "helm install gpu-operator nvidia/gpu-operator --namespace gpu-operator --create-namespace" "Instalando el operador de GPU de NVIDIA"
run_command "helm upgrade -i gpu-operator oci://ghcr.io/run-ai/fake-gpu-operator/fake-gpu-operator -f $MANIFESTS_DIR/fake-gpu-operator-values.yaml --namespace fake-gpu-operator --create-namespace" "Instalando el fake-gpu-operator"
run_command "kubectl apply -f $MANIFESTS_DIR/gpu-servicemonitor.yaml -n fake-gpu-operator" "Aplicando service monitor del dcgm exporter"
run_command "kubectl label ns fake-gpu-operator pod-security.kubernetes.io/enforce=privileged" "pod-security configuration"
run_command "helm upgrade --namespace kube-system --install kwok kwok/kwok" "Instalando kwok helm chart"
run_command "helm upgrade --install kwok kwok/stage-fast" "Aplicando default stage policy kwok"

# for ((i = 2, j = 0; i <= $NUM_WORKERS+1; i++, j++)) do
#     run_command "kubectl label node node${i} run.ai/simulated-gpu-node-pool=gpu${j}" "Etiquetando los nodos para asignar pool de GPU"
# done

# fi
log_success "Se han añadido los nodos worker al cluster correctamente"