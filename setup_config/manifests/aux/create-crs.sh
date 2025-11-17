#!/bin/bash

MIG_BLOCK=6

# Funcion para crear las particiones MIG
generate_mig_blocks() {

  local MigFormated=$1
  local MigQuantities=$2
  local NumGpu=$((-1))

  local STRING=""

  # Bucle para iterar todos los tipos de particion MIG de cada GPU
  for ((j = 0, k = 0; ${#MigFormated} > j; j += 7, k += 2)); do

    MigPartition="${MigFormated:$j:$MIG_BLOCK}"

    if [ $NumGpu -lt $((${MigPartition:0:1})) ]; then
      ((NumGpu++))
      STRING+="\n  - mig-enabled: true\n    mig-slices:"
    fi

    NUM_PARTITION=${MigQuantities:$k:1}

    # Se añaden tantas particiones de un tipo según su cantidad en la GPU
    for ((x = 0; NUM_PARTITION > x; x++)); do
      STRING+="\n"
      STRING+="    - size: ${MigPartition:2:1}\n"
      STRING+="      mem: ${MigPartition:4:2}\n"
      STRING+="      available: 10"
    done
  done
  echo -e "$STRING"
}

# Funcion para crear las gpu
generate_gpu_blocks() {
  local count=$1
  local STRING=""

  for ((j = 0; j < count; j++)); do
    STRING+="  - mig-enabled: false\n    available: 10\n"
  done
  echo -e "$STRING"
}

# Se itera por cada nodo
for ((i = 0; KWOK_NODES > i; i++)); do

  Allocatable=$(kubectl get node kwok-node-$i -o jsonpath='{.status.allocatable}')

  GpuCount=$(echo "$Allocatable" | jq -r '."nvidia.com/gpu"')

  MigDevices=$(echo "$Allocatable" | jq 'del(."nvidia.com/gpu", .cpu, .memory, .pods)')

  MigFormated=$(echo "$MigDevices" | jq -r 'keys[]' | grep -oP '\d+')

  MigQuantities=$(echo "$MigDevices" | jq -r 'values[]' | grep -oP '\d+')

kubectl apply -f - <<EOF
apiVersion: gpu.com/v1
kind: Specification
metadata:
  name: kwok-node-$i
  namespace: default
spec:
  gpus:
$(generate_gpu_blocks "$GpuCount")
$(generate_mig_blocks "$MigFormated" "$MigQuantities")
EOF

done