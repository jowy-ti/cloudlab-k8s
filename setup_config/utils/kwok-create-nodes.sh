#!/bin/bash

declare -a poolnodes=(0 125)
declare -a fp32=(30000 60000)
declare -a MIGinstances=(0 7)

# Función para generar el YAML de un solo nodo
generate_node_yaml() {
  local name=$1
  local pool_idx=$2
  local gpu_pool="pool$pool_idx"
  
  cat <<EOF
apiVersion: v1
kind: Node
metadata:
  annotations:
    node.alpha.kubernetes.io/ttl: "0"
    kwok.x-k8s.io/node: fake
  labels:
    beta.kubernetes.io/arch: amd64
    beta.kubernetes.io/os: linux
    kubernetes.io/arch: amd64
    kubernetes.io/hostname: "$name"
    kubernetes.io/os: linux
    kubernetes.io/role: agent
    node-role.kubernetes.io/agent: "" 
    run.ai/simulated-gpu-node-pool: "$gpu_pool"
    nvidia.com/gpu.fp32.GFLOPS: "${fp32[$pool_idx]}"
    mig-instances: "${MIGinstances[$pool_idx]}"
    type: kwok
  name: "$name"
spec:
  taints:
  - effect: NoSchedule
    key: node
    value: fake
status:
  allocatable:
    cpu: 32
    memory: 64Gi
    pods: 110
  capacity:
    cpu: 32
    memory: 64Gi
    pods: 110
  nodeInfo:
    architecture: amd64
    kubeProxyVersion: fake
    kubeletVersion: fake
    operatingSystem: linux
  phase: Running
---
EOF
}

echo "Generando configuración para los nodos..."

# Usamos un subshell o un archivo temporal para enviar todo a kubectl de una vez
{
  CURRENT_NODE_COUNT=0
  for ((p=0; p<${#poolnodes[@]}; p++)); do
    NUM_NODES=${poolnodes[$p]}
    
    for ((n=0; n<NUM_NODES; n++)); do
      NODE_NAME="kwok-node-$CURRENT_NODE_COUNT"
      generate_node_yaml "$NODE_NAME" "$p"
      ((CURRENT_NODE_COUNT++))
    done
  done
} | kubectl apply -f -

# echo "¡Listo! Se han procesado $CURRENT_NODE_COUNT nodos."