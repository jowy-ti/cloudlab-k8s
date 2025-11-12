#!/bin/bash

KWOK_NODES=2 # temp

# generate_mig_blocks() {
# $(echo "$STRING" | grep -oP '\d+')
# }

generate_gpu_blocks() {
  local count=$1
  for ((i = 0; i < count; i++)); do
    echo "  - available: 10"
  done
}

for ((i = 0; KWOK_NODES > i; i++)); do

  Allocatable=$(kubectl get node kwok-node-$i -o jsonpath='{.status.allocatable}')

  GpuCount=$(echo "$Allocatable" | jq -r '."nvidia.com/gpu"')

  MigDevices=$(echo "$Allocatable" | jq 'del(."nvidia.com/gpu", .cpu, .memory, .pods)')

  echo "$MigDevices"
  echo "kwok-node-$i: $GpuCount"

# kubectl apply -f - <<EOF
# apiVersion: gpu.com/v1
# kind: Specification
# metadata:
#   name: kwok-node-$i
#   namespace: default
# spec:
#   gpus:
# $(generate_gpu_blocks "$GpuCount")
# $(generate_mig_blocks "$MigDevices")
# EOF

done

# echo "$Allocatable"

  # - mig-slices:
  #   - size: 4
  #   position: 0
  #   available: 10
  #   - size: 3
  #   position: 4
  #   available: 10