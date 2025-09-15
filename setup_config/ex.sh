#!/bin/bash

helm list --no-headers | while read -r name rest; do
    helm uninstall $name
done