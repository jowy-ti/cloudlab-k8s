#!/bin/bash

SSH_DIR="~/.ssh"
KEY="nodekey"
SHARED_DIR="/proj/gpu4k8s-PG0/exp/*/tmp"
WAIT_TIME=10

if [[ $NODENUM == "node1" ]]; then
    run_command  "ssh-keygen -t ed25519 -f $SSH_DIR/$KEY -q -N """ "Creando par de claves para ssh"
    cp "$SSH_DIR/$KEY.pub" "$SHARED_DIR/$KEY.pub"

    # Comprobación del agente ssh
    if ssh-add -l > /dev/null 2>&1; then
        log_success "El agente SSH está activo."
    else
        log_info "El agente SSH no está funcionando. Iniciándolo..."
        eval $(ssh-agent -s)
        log_success "Agente SSH iniciado."
    fi

    run_command "ssh-add $SSH_DIR/$KEY" "Añadiendo clave al agente ssh"

    NODE_WAIT="node${NUM_WORKERS}"

    echo $NODE_WAIT

    log_info "Esperando a que hayan copiado todo los nodos workers la clave pública"

    while [[ ! -f "$SHARED_DIR/$NODE_WAIT" ]]; do
        sleep $WAIT_TIME
    done

    log_success "Todos los workers ya tienen la clave pública"

else

    while [[ ! -f "$SHARED_DIR/$NODE_WAIT" ]]; do
        sleep $WAIT_TIME
    done

fi