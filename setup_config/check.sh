#!/bin/bash

SHARED_DIR="/proj/gpu4k8s-PG0/exp/*/tmp"
KEY="nodekey"

if [[ ! -f "/proj/gpu4k8s-PG0/exp/*/tmp/nodekey.pub" ]]; then
    echo "no está $SHARED_DIR/$KEY.pub"

else
    echo "si está"
fi