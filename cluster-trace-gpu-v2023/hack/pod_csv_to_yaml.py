import sys
import yaml
import pandas as pd
from pathlib import Path
import math
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

USAGE_PROMPT="""Usage:
python3 pod_csv_to_yaml.py data/csv/openb_pod_list_gpuspec10.csv
"""
OUTPUT_DIR_DEFAULT="data/new_output"

MILLI = 1000
DATA_CREATION_TIME = "creation_time"
DATA_DELETION_TIME = "deletion_time"
DATA_SCHEDULED_TIME ="scheduled_time"

# Mis custom resources
StandardMem  = int(os.getenv('STANDARD_MEM'))
StandardFp32 = int(os.getenv('STANDARD_FP32'))
GpuFp32      = "customresource.com/gpufp32"
GpuMemory    = "customresource.com/gpuMemory"
CreationTime = "customresource.com/creation-time"
DeletionTime = "customresource.com/deletion-time"
ScheduledTime = "customresource.com/scheduled-time"
HardIsolation = "hardIsolation"
DesiredTime = int(os.getenv('DESIRED_TIME')) # segundos que dura el creation time de inicio a fin
F_Deletion = int(os.getenv('F_DELETION'))

ResourceName = "alibabacloud.com/gpu-milli"      # GPU milli, i.e., 1000 == 1 GPU, for pod only, node is 1000 by default
CountName    = "alibabacloud.com/gpu-count"      # GPU number request (or allocatable), for pod and node
DeviceIndex  = "alibabacloud.com/gpu-index"      # Exists when the pod are assigned/predefined to a GPU device
ModelName    = "alibabacloud.com/gpu-card-model" # GPU card model, for pod and node
AssumeTime   = "alibabacloud.com/assume-time"    # To retrieve the scheduling latency
# CreationTime = "alibabacloud.com/creation-time"  # creation timestamp
# DeletionTime = "alibabacloud.com/deletion-time"  # deletion timestamp
PodNsNameSep = "/"
DevIdSep     = "-"

def generate_pod_yaml(workload_name='paib-pod-10',
                      workload_namespace='default', # Cambiado el namespace al default
                      container_name='main',
                      container_image='tensorflow:latest',
                      container_requests={'cpu': '6000m'},
                      container_limits={'cpu': '6000m'},
                      node_selector_node_ip="",
                      annotations={},
                      labels={}):
    pod_template = """
    apiVersion: v1
    kind: Pod
    metadata:
      name: single-pod
      labels:
        app: fake-pod
    spec:
      schedulerName: scheduler-plugin
      tolerations:
      - key: node
        operator: Equal
        value: fake
        effect: NoSchedule
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: type
                operator: In
                values:
                - kwok
      containers:
      - name: php-redis
        image: gcr.io/google-samples/gb-frontend:v4
        imagePullPolicy: Always
        resources:
          requests:
            cpu: 100m
          limits:
            cpu: 100m
      restartPolicy: "OnFailure"
      dnsPolicy: "Default"
    """
    workload_yaml = yaml.safe_load(pod_template)
    workload_yaml['metadata']['name'] = workload_name
    workload_yaml['metadata']['namespace'] = workload_namespace
    workload_yaml['spec']['containers'][0]['name'] = container_name
    workload_yaml['spec']['containers'][0]['image'] = container_image
    workload_yaml['spec']['containers'][0]['resources']['requests'] = container_requests
    workload_yaml['spec']['containers'][0]['resources']['limits'] = container_limits

    if len(node_selector_node_ip) > 0:
        if 'nodeSelector' not in workload_yaml['spec']:
            workload_yaml['spec']['nodeSelector'] = {}
        workload_yaml['spec']['nodeSelector']['node-ip'] = node_selector_node_ip
    elif 'nodeSelector' in workload_yaml['spec']:
        if 'node-ip' in workload_yaml["spec"]["nodeSelector"]:
            del workload_yaml['spec']['nodeSelector']['node-ip']

    for k, v in annotations.items():
        if 'annotations' not in workload_yaml['metadata']:
            workload_yaml['metadata']['annotations'] = {}
        if v is not None:
            workload_yaml['metadata']['annotations'][k] = v  # e.g., {"alibabacloud.com/gpu-index":"2-3-4"}
    for k, v in labels.items():
        workload_yaml['metadata'][k] = v

    return workload_yaml

# funció principal
# dfp: Información del csv
def output_pod(dfp, outfile='pod.yaml', node_select=False):
    num_pod = len(dfp)

    DeletionArray = dfp[DATA_DELETION_TIME].to_numpy()
    ScheduledArray = dfp[DATA_SCHEDULED_TIME].to_numpy()
    CreationArray = dfp[DATA_CREATION_TIME].to_numpy()

    TotalTimeCreation = CreationArray[-1] - CreationArray[0]
    offset = CreationArray[0]
    F_lineal = DesiredTime / TotalTimeCreation

    DeletionArray = ((DeletionArray - offset) * F_lineal * F_Deletion) + 3
    ScheduledArray = (ScheduledArray - offset) * F_lineal
    CreationArray = (CreationArray - offset) * F_lineal

    for index, row in dfp.iterrows():
        if 'name' in row: 
            workload_name = row['name']
        elif 'job_id' in row:
            workload_name = f"job-{row['job_id']:04}" # float is not allowed
        else:
            exit("neither name nor job_id in row")
           
        container_requests = {}
        annotations = {}

        if int(row['num_gpu']) != 0:
            if node_select:
                annotations[DeviceIndex] = row['gpu_index'] if type(row['gpu_index']) == str else ""
            if 'gpu_milli' not in row:
                MilliGpu = 1000
            else:
                MilliGpu = "%d" % (int(row['gpu_milli'])) if 0 < row['gpu_milli'] <= 1000 else "1000" if row['gpu_milli'] > 1000 else "0"

            RatioGpu = float(MilliGpu) / 1000.0
            container_requests[GpuMemory] = int(RatioGpu * StandardMem )
            container_requests[GpuFp32] = int(RatioGpu * StandardFp32)
            
            # if int(MilliGpu) == 1000:
            #     annotations[HardIsolation] = 'true'
            # else:
            #     annotations[HardIsolation] = 'false'
            annotations[HardIsolation] = 'true'

            if 'gpu_spec' in row:
                gpu_req_val = [x for x in row['gpu_spec'].split('|') if len(x) > 0]
                gpu_req_out = "|".join(x for x in gpu_req_val)
                if len(gpu_req_out) > 0:
                    annotations[ModelName] = gpu_req_out

        container_limits = container_requests.copy()

        host_node_ip = row['ip'] if node_select else ""

        annotations[CreationTime] = "%s" % int(CreationArray[index])

        if math.isnan(ScheduledArray[index]):
          annotations[ScheduledTime] = annotations[CreationTime]
        else :
          annotations[ScheduledTime] = "%s" % int(ScheduledArray[index])

        if math.isnan(DeletionArray[index]):
            annotations[DeletionTime] = annotations[ScheduledTime]
        else:
            annotations[DeletionTime] = "%s" % int(DeletionArray[index])

        pod_yaml = generate_pod_yaml(workload_name=workload_name, container_requests=container_requests,
                                     container_limits=container_limits, node_selector_node_ip=host_node_ip,
                                     annotations=annotations)

        if index == 0:
            with open(outfile, 'w') as file:
                yaml.dump(pod_yaml, file)
        else:
            with open(outfile, 'a') as file:
                file.writelines(['\n---\n\n'])
                yaml.dump(pod_yaml, file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        exit(USAGE_PROMPT)
    pod_csv_file = Path(sys.argv[1])
    if not pod_csv_file.exists():
        exit(f"CSV File: {pod_csv_file} does not exist")
    
    dfp = pd.read_csv(pod_csv_file, dtype={'gpu_index': str})
    if 'gpu_spec' in dfp:
        dfp.gpu_spec = dfp.gpu_spec.fillna('')
    
    output_dir = pod_csv_file.stem # .csv to ""
    if len(output_dir) <= 0:
        output_dir_path = Path(OUTPUT_DIR_DEFAULT)
    else:
        output_dir_path = Path(output_dir)
    output_dir_path.mkdir(exist_ok=True)

    pod_yaml_file = output_dir_path / (pod_csv_file.stem + '.yaml') # .csv to .yaml
    output_pod(dfp, pod_yaml_file, node_select=False)
    print("OUTPUT: %s (len: %d)" % (pod_yaml_file, len(dfp)))





