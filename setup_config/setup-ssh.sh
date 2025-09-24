#!/bin/bash

EXP=$(ls /proj/gpu4k8s-PG0/exp/)

SSH_DIR="~/.ssh"
KEY="nodekey"
SHARED_DIR="/proj/gpu4k8s-PG0/exp/$EXP/tmp"
WAIT_TIME=5
FIRST_WORKER="node2"

if [[ $NODENUM == "node1" ]]; then
    run_command  "ssh-keygen -t ed25519 -f $SSH_DIR/$KEY -q -N ''" "Creando par de claves para ssh"
    run_command "cp $SSH_DIR/$KEY.pub $SHARED_DIR" "Copiando la clave pública al directorio compartido"
    run_command "cat $SSH_DIR/$KEY.pub >> $SSH_DIR/authorized_keys" "Añadiendo la clave pública en authorized keys"

    # Comprobación del agente ssh
    if ssh-add -l > /dev/null 2>&1; then
        log_success "El agente SSH está activo."
    else
        log_info "El agente SSH no está funcionando. Iniciándolo..."
        eval $(ssh-agent -s)
        log_success "Agente SSH iniciado."
    fi

    run_command "ssh-add $SSH_DIR/$KEY" "Añadiendo clave al agente ssh"

    NODE_WAIT="node$((NUM_WORKERS+1))"

    echo $NODE_WAIT

    log_info "Esperando a que hayan copiado todo los nodos workers la clave pública"

    while [[ ! -f "$SHARED_DIR/$NODE_WAIT" ]]; do
        log_info "Esperando al nodo $SHARED_DIR/$NODE_WAIT"
        sleep $WAIT_TIME
    done

    log_success "Todos los workers ya tienen la clave pública"

else

    if [[ $NODENUM != $FIRST_WORKER ]]; then

        NUM=$((${NODENUM:4} - 1))  
        NODE_WAIT="node${NUM}"

        while [[ ! -f "$SHARED_DIR/$NODE_WAIT" ]]; do
            log_info "Esperando al nodo $SHARED_DIR/$NODE_WAIT"
            sleep $WAIT_TIME
        done
    fi

    while [[ ! -f "$SHARED_DIR/$KEY.pub" ]]; do
        log_info "Esperando a la clave pública $SHARED_DIR/$KEY.pub"
        sleep $WAIT_TIME
    done

    run_command "cp $SHARED_DIR/$KEY.pub $SSH_DIR" "Copiando la clave pública al directorio personal ~/.ssh"
    run_command "cat $SSH_DIR/$KEY.pub >> $SSH_DIR/authorized_keys" "Añadiendo la clave pública en authorized keys"
    run_command "touch $SHARED_DIR/$NODENUM" "Creando el fichero para avisar configuración ssh finalizada"

fi