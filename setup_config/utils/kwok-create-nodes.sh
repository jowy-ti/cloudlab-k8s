#!/bin/bash

CREATE_CRS=/local/repository/setup_config/utils/create-crs.sh
export KWOK_NODES=2
declare -a poolnodes=(1 2)  #poolnodes=(3 5 6)
POOL=0
NUMCPU=0
MEM=0

for ((i = 0; KWOK_NODES > i; i++)); do

  NODE_NAME="kwok-node-$i"

  if [[ i -ge poolnodes[$POOL] ]]; then
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
      kubernetes.io/hostname: kwok-node-0
      kubernetes.io/os: linux
      kubernetes.io/role: agent
      node-role.kubernetes.io/agent: "" 
      run.ai/simulated-gpu-node-pool: $GPU_POOL
      type: kwok
    name: $NODE_NAME
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

sleep 10

$CREATE_CRS