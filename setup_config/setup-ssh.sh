#!/bin/bash

EXP=$(ls /proj/gpu4k8s-PG0/exp/)
AUTHORIZED_KEYS="$HOME/.ssh/authorized_keys"
SSH_DIR="$HOME/.ssh"
KEY="nodekey"
SHARED_DIR="/proj/gpu4k8s-PG0/exp/$EXP/tmp"
WAIT_TIME=5
KEY_ID=ssh-ed25519

# Ejecución nodo master
if [[ $NODENUM == "node1" ]]; then

    if [[ ! -f "$SSH_DIR/$KEY" ]]; then
        run_command  "ssh-keygen -t ed25519 -f $SSH_DIR/$KEY -q -N ''" "Creando par de claves para ssh"
    fi

    run_command "cp $SSH_DIR/$KEY.pub $SHARED_DIR" "Copiando la clave pública al directorio compartido"

    if ! grep -q $KEY_ID "$AUTHORIZED_KEYS"; then
        run_command "cat $SSH_DIR/$KEY.pub >> $AUTHORIZED_KEYS" "Añadiendo la clave pública en authorized keys"
    fi

    # Comprobación del agente ssh
    if ssh-add -l > /dev/null 2>&1; then
        log_success "El agente SSH está activo."
    else
        log_info "El agente SSH no está funcionando. Iniciándolo..."
        eval "$(ssh-agent -s)"
        log_success "Agente SSH iniciado."
    fi

    run_command "ssh-add $SSH_DIR/$KEY" "Añadiendo clave al agente ssh"

    log_info "Esperando a que hayan copiado todo los nodos workers la clave pública"

    # Esperamos a los nodos workers
    for ((num=2; num <= NUM_WORKERS + 1; num++)) do
        NODE_WAIT="node$num"
        while [[ ! -f "$SHARED_DIR/$NODE_WAIT" ]]; do
            log_info "Esperando al nodo $NODE_WAIT"
            sleep $WAIT_TIME
        done
    done

    log_success "Todos los workers ya tienen la clave pública"

# Ejecución nodos workers
else

    # Se espera a la clave pública
    while [[ ! -f "$SHARED_DIR/$KEY.pub" ]]; do
        log_info "Esperando a la clave pública $KEY.pub"
        sleep $WAIT_TIME
    done

    run_command "cp $SHARED_DIR/$KEY.pub $SSH_DIR" "Copiando la clave pública al directorio personal $HOME/.ssh"

    if ! grep -q $KEY_ID "$AUTHORIZED_KEYS"; then
        run_command "cat $SSH_DIR/$KEY.pub >> $AUTHORIZED_KEYS" "Añadiendo la clave pública en authorized keys"
    fi

    run_command "touch $SHARED_DIR/$NODENUM" "Creando el fichero para avisar configuración ssh finalizada"

fi