#!/bin/bash

# ==============================================================================
# Script para escalar el cluster de Kubernetes
# con Kubespray, Prometheus y el operador de GPU de NVIDIA.
#
# Incluye comprobación de errores y mensajes de estado para cada paso.
# ==============================================================================

# Detiene el script inmediatamente si un comando falla
set -e

# Activar entorno virtual
log_info "Activando entorno virtual"
if [[ -f "$VENV_DIR/bin/activate" ]] && [[ -z "$VIRTUAL_ENV" ]]; then
    source "$VENV_DIR/bin/activate"
    log_success "Entorno virtual activado."
fi

# Añadir repositorios de Helm
log_info "Configurando Helm..."
# run_command "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts" "Añadiendo el repositorio de Helm de Prometheus Community"
run_command "helm repo add nvidia https://helm.ngc.nvidia.com/nvidia" "Añadiendo el repositorio de Helm de NVIDIA"
run_command "helm repo add kwok https://kwok.sigs.k8s.io/charts/" "Añadiendo repo de kwok"
# run_command "helm repo add scheduler-plugins https://scheduler-plugins.sigs.k8s.io" "Añadiendo repo del scheduler plugin"

# Instalando helm charts
log_info "Desplegando componentes con Helm..."
run_command "helm repo update" "Actualizando los repositorios de Helm"
# run_command "helm install prometheus prometheus-community/kube-prometheus-stack -f $MANIFESTS_DIR/prometheus_stack_values.yaml --namespace monitoring --create-namespace" "Instalando la stack de Prometheus"
# run_command "helm install gpu-operator nvidia/gpu-operator --namespace gpu-operator --create-namespace" "Instalando el operador de GPU de NVIDIA"
run_command "helm upgrade -i gpu-operator oci://ghcr.io/run-ai/fake-gpu-operator/fake-gpu-operator -f $MANIFESTS_DIR/fake-gpu-operator-values.yaml --namespace fake-gpu-operator --create-namespace" "Instalando el fake-gpu-operator"
run_command "kubectl apply -f $MANIFESTS_DIR/gpu-servicemonitor.yaml -n fake-gpu-operator" "Aplicando service monitor del dcgm exporter"
run_command "kubectl label ns fake-gpu-operator pod-security.kubernetes.io/enforce=privileged" "pod-security configuration"
run_command "helm upgrade --install kwok kwok/kwok --namespace kube-system" "Instalando kwok helm chart"
run_command "helm upgrade --install kwok kwok/stage-fast" "Aplicando default stage policy kwok"

run_command "kubectl apply -f $MANIFESTS_DIR/crd.yaml" "Aplicando CRD"

# KWOK nodes

# run_command "$SETUP_DIR/kwok-nodes.sh" "Creando kwok nodes"

# fi
log_success "Se han añadido los nodos worker al cluster correctamente"