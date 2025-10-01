#!/bin/bash

source /local/repository/setup_config/env.sh

kubectl label node --selector='!node-role.kubernetes.io/control-plane' run.ai/simulated-gpu-node-pool=default

helm upgrade -i gpu-operator oci://ghcr.io/run-ai/fake-gpu-operator/fake-gpu-operator -f $SETUP_DIR/ --namespace gpu-operator --create-namespace

kubectl label ns gpu-operator pod-security.kubernetes.io/enforce=privileged

