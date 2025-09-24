#!/bin/bash

SSH_DIR="$HOME/.ssh"
KEY="nodekey"

if [[ ! -f "$SSH_DIR/$KEY" ]]; then
    echo "no está $SSH_DIR/$KEY.pub"
else
    echo "si está"
fi