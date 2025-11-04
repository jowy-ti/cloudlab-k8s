#!/bin/bash

kubectl rollout restart deployment -n plugins scheduler-plugin

# helm upgrade -i scheduler-plugins /local/repository/setup_config/scheduler-plugins --namespace plugins -f 
#   /local/repository/setup_config/manifests/values_plugin.yaml

# kubectl describe pods -n plugins scheduler-plugin-fcff44b4b-bj2mp | grep "Image ID"