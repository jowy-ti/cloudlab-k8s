#!/bin/bash

declare -a poolnodes=(0 63)  # poolnodes=(3 5 6)
declare -a fp32=(30000 60000) # fp32 de cada pool
declare -a MIGinstances=(0 7) # instancias MIG de cada pool
POOL=0
KWOK_NODES=0

for i in "${poolnodes[@]}"; do
  ((KWOK_NODES += i))
done

for ((i = 0; KWOK_NODES > i; i++)); do

  NODE_NAME="kwok-node-$i"

  if [[ i -ge $((poolnodes[POOL])) ]]; then
    ((POOL++))
  fi

  GPU_POOL="pool$POOL"

  echo "$NODE_NAME    $GPU_POOL"

  kubectl apply -f - <<EOF
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
      kubernetes.io/hostname: "$NODE_NAME"
      kubernetes.io/os: linux
      kubernetes.io/role: agent
      node-role.kubernetes.io/agent: "" 
      run.ai/simulated-gpu-node-pool: "$GPU_POOL"
      nvidia.com/gpu.fp32.GFLOPS: "${fp32[POOL]}"
      mig-instances: "${MIGinstances[POOL]}"
      type: kwok
    name: "$NODE_NAME"
  spec:
    taints: # Avoid scheduling actual running pods to fake Node
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
      bootID: ""
      containerRuntimeVersion: ""
      kernelVersion: ""
      kubeProxyVersion: fake
      kubeletVersion: fake
      machineID: ""
      operatingSystem: linux
      osImage: ""
      systemUUID: ""
    phase: Running
EOF

done