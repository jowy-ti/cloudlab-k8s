#!/bin/bash

VALUES="/local/repository/setup_config/manifests/fake-gpu-operator-values.yaml"

helm upgrade gpu-operator oci://ghcr.io/run-ai/fake-gpu-operator/fake-gpu-operator -f $VALUES --namespace fake-gpu-operator

kubectl delete configmaps -n fake-gpu-operator -l node-topology=true

kubectl delete pods -n fake-gpu-operator -l app=device-plugin

kubectl delete pods -n fake-gpu-operator -l app=status-updater