# log_info "Desplegando componentes con Helm..."
# run_command "helm install prometheus prometheus-community/kube-prometheus-stack -f $SETUP_DIR/prometheus_stack_values.yaml" "Instalando la stack de Prometheus"
# run_command "helm install gpu-operator nvidia/gpu-operator" "Instalando el operador de GPU de NVIDIA"