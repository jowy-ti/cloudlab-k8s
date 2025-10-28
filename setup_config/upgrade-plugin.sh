#!/bin/bash

kubectl rollout restart deployment -n plugins scheduler-plugin

# helm upgrade -i scheduler-plugins /local/repository/setup_config/scheduler-plugins --namespace plugins -f /local/repository/setup_config/manifests/values_plugin.yaml

# kubectl patch deployment scheduler-plugin \
#     -n plugins \
#     -p '{"spec":{"template":{"spec":{"containers":[{"name":"scheduler-plugins-scheduler","imagePullPolicy":"Always"}]}}}}'

# kubectl patch deployment controller-plugin \
#     -n plugins \
#     -p '{"spec":{"template":{"spec":{"containers":[{"name":"scheduler-plugins-controller","imagePullPolicy":"Always"}]}}}}'

# kubectl describe pods -n plugins scheduler-plugin-fcff44b4b-bj2mp | grep "Image ID"