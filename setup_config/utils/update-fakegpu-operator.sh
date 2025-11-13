#!/bin/bash

SETUP="/local/repository/setup_config"
MANIFESTS="$SETUP/manifests"
UTILS="$SETUP/utils"

helm upgrade gpu-operator oci://ghcr.io/run-ai/fake-gpu-operator/fake-gpu-operator -f $MANIFESTS/fake-gpu-operator-values.yaml --namespace fake-gpu-operator

kubectl delete configmaps -n fake-gpu-operator -l node-topology=true

kubectl delete pods -n fake-gpu-operator -l app=device-plugin

kubectl delete pods -n fake-gpu-operator -l app=status-updater

$UTILS/kwok-delete-nodes.sh
$UTILS/kwok-create-nodes.sh