#!/bin/bash

sudo apt update

sudo apt install python3-venv

cp ~/cloudlab-k8s/SetupConfig/inventory.ini ~/cloudlab-k8s/kubespray/inventory/mycluster/inventory.ini

cd ~/cloudlab-k8s

python3 SetupConfig/nodeIPs.py

python3 -m venv ~/cloudlab-k8s/venv

source venv/bin/activate

cd ~/cloudlab-k8s/kubespray

pip3 install -U -r requirements.txt

pip3 install kubernetes openshift pyyaml helm

ansible-galaxy collection install community.kubernetes

ansible -i inventory/mycluster/inventory.ini all -m ping

ansible-playbook -i inventory/mycluster/inventory.ini -b cluster.yml

mkdir -p $HOME/.kube

sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config

sudo chown $(id -u):$(id -g) $HOME/.kube/config

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm repo add nvidia https://helm.ngc.nvidia.com/nvidia

helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

helm install gpu-operator nvidia/gpu-operator --namespace gpu-operator --create-namespace