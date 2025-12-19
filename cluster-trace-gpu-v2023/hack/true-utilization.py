import threading
import time
import yaml
import sys
import os
from kubernetes import client, config, watch
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

data_lock = threading.Lock()
V100Fp32 = 14000
V100Mem = 16000
LAST_POD_NAME = os.getenv('LAST_POD_NAME')
LAST_POD = False

MIG_INSTANCES_FP32= {
    '1': 1 / 7, 
    '2': 2 / 7,
    '3': 3 / 7,
    '4': 4 / 7,
    '7' : 1
    }

MIG_INSTANCES_MEM= {
    '1': 1 / 8, 
    '2': 2 / 8,
    '3': 4 / 8,
    '4': 4 / 8,
    '7' : 1
    }

def total_memory_fp32_gpu():
    fp32Total = 0
    memTotal = 0
    gpuTotal = 0

    with data_lock:
        for node in ALL_NODES:
            for gpu in ALL_NODES[node]:
                fp32Total += gpu[FP32_TOTAL_NAME]
                memTotal += gpu[MEM_TOTAL_NAME]
                gpuTotal += 1
    
    return fp32Total, memTotal, gpuTotal


def request_with_to_int(num):
    if 'k' in num:
        number = int(float(num.lower().replace('k', '')) * 1000)
    else:
        number = int(num)
    return number

def calculate_allocated(nodeName, gpuPos, tipo, podFp32, podMem, isolation, migSize):

    totalFp32 = ALL_NODES[nodeName][gpuPos][FP32_TOTAL_NAME]
    totalMem = ALL_NODES[nodeName][gpuPos][MEM_TOTAL_NAME]

    if tipo == 'ADDED':
        if isolation:
            if migSize != '':
                ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] += MIG_INSTANCES_FP32[migSize] * totalFp32
                ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] += MIG_INSTANCES_MEM[migSize] * totalMem
            else:
                ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] = totalFp32
                ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] = totalMem
        else:
            ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] += podFp32
            ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] += podMem

    elif tipo == 'DELETED':
        if isolation:
            if migSize != '':
                ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] -= MIG_INSTANCES_FP32[migSize] * totalFp32
                ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] -= MIG_INSTANCES_MEM[migSize] * totalMem
            else:
                ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] = 0
                ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] = 0
        else:
            ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] -= podFp32
            ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] -= podMem

def k8s_watch_thread(v1):
    """Hilo encargado de escuchar eventos de Kubernetes"""

    global ALL_NODES
    global LAST_POD

    w = watch.Watch()
    print("Iniciando Watcher...")
    while True:
        try:
            for event in w.stream(v1.list_namespaced_pod, namespace=NAMESPACE_TARGET):
                tipo = event['type']
                pod = event['object']

                if tipo == 'MODIFIED':
                    continue

                annotations = pod.metadata.annotations
                if annotations is None or GPU_POS not in annotations:
                    continue
                
                podName = pod.metadata.name
                nodeName = pod.spec.node_name
                gpuPos = int(pod.metadata.annotations[GPU_POS])
                podFp32 = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpufp32"])
                podMem = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpuMemory"])
                isolation = False
                migSize = ''    
                allocated = 0

                if MIG_SIZE_NAME in annotations:
                    migSize = pod.metadata.annotations[MIG_SIZE_NAME]

                if V100Fp32 == podFp32 and V100Mem == podMem:
                    isolation = True
                
                with data_lock:
                    if tipo == 'ADDED': # or tipo == 'MODIFIED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] += podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] += podMem

                    elif tipo == 'DELETED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] -= podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] -= podMem

                        if podName == LAST_POD_NAME:
                            LAST_POD = True
                            print("Último pod")

                    # print(f"nodeName: {'kwok-node-1'}, Fp32: {ALL_NODES['kwok-node-1'][gpuPos][FP32_USED_NAME]}, Mem: {ALL_NODES['kwok-node-1'][gpuPos][MEM_USED_NAME]}")
                                            
                    calculate_allocated(nodeName, gpuPos, tipo, podFp32, podMem, isolation, migSize)

                # print(f"fp32_used: {ALL_NODES[nodeName][gpuPos][FP32_USED_NAME]}, mem_used: {ALL_NODES[nodeName][gpuPos][MEM_USED_NAME]}")
                # print(f"Usage: {ALL_NODES[nodeName][gpuPos][USAGE_NAME]}, Allocated: {ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME]}")

        except Exception as e:
            print(f"Error en Watcher: {e}. Reintentando...")
            time.sleep(2)

def saver_thread():
    """Hilo encargado de guardar el estado cada 5 segundos"""

    time.sleep(2)

    global FIN

    fp32Total, memTotal, gpuTotal = total_memory_fp32_gpu()
    print(f"gpuTotal: {gpuTotal}")
    gpuUtilization = []
    gpuAllocated = []
    gpuOccupation = []
    timeline = []
    INIT_TIME = int(time.time())

    # print(f"fp32Total: {fp32Total}, memTotal: {memTotal}")

    while True:

        with data_lock:
            if FIN:
                plt.plot(timeline, gpuOccupation, label='Ocupación', linestyle='-')
                plt.plot(timeline, gpuUtilization, label='Asignación', linestyle='--')
                plt.plot(timeline, gpuAllocated, label='Utilización', linestyle='-.')
                plt.ylim(0, 100)
                plt.legend()
                plt.savefig("plots/utilization.png")
                sys.exit()

        fp32Used = 0
        memUsed = 0
        fp32Allocated = 0
        memAllocated = 0
        numGpuOccuped = 0
        
        with data_lock:
            for node in ALL_NODES:
                for gpu in ALL_NODES[node]:
                    fp32Used += gpu[FP32_USED_NAME]
                    memUsed += gpu[MEM_USED_NAME]
                    fp32Allocated += gpu[FP32_ALLOCATED_NAME]
                    memAllocated += gpu[MEM_ALLOCATED_NAME]

                    if fp32Used != 0 or memUsed != 0: ## mirar esto
                        numGpuOccuped += 1

        Occupation = int((numGpuOccuped / gpuTotal)  * 100)
        Utilization = int((((fp32Used / fp32Total) + (memUsed / memTotal)) / 2) * 100)
        Allocated = int((((fp32Allocated / fp32Total) + (memAllocated / memTotal)) / 2) * 100)

        gpuOccupation.append(Occupation)
        gpuUtilization.append(Utilization)
        gpuAllocated.append(Allocated)
        timeline.append(int(time.time() - INIT_TIME))
        # print(f"Utilization: {Utilization}, Allocated: {Allocated}")
        print(f"Occupation: {Occupation}, numGpuOccuped: {numGpuOccuped}")
            
        time.sleep(WAIT_TIME)

if __name__ == "__main__":

    GPU_POS = 'gpuPos'
    FP32_TOTAL_NAME = 'fp32Total'
    MEM_TOTAL_NAME = 'memTotal'
    FP32_USED_NAME = 'fp32Used'
    MEM_USED_NAME = 'memUsed'
    FP32_ALLOCATED_NAME = 'fp32Allocated'
    MEM_ALLOCATED_NAME = 'memAllocated'
    MIG_SIZE_NAME = 'migSize'
    NAMESPACE_TARGET = 'default'
    FIELD_SELECTOR = 'status.phase=Running'
    WAIT_TIME = 3
    FIN = False

    try:
        with open("all-nodes.yaml", "r") as archivo:
            ALL_NODES = yaml.safe_load(archivo)
    except FileNotFoundError:
        print("Error: El archivo no existe.")
    except yaml.YAMLError as e:
        print(f"Error al leer el archivo YAML: {e}")

    config.load_kube_config()
    v1 = client.CoreV1Api()

    # Creamos los dos hilos
    hilo_escucha = threading.Thread(target=k8s_watch_thread, daemon=True, args=(v1,))
    hilo_guardado = threading.Thread(target=saver_thread, daemon=False)
    
    # Los iniciamos
    hilo_escucha.start()
    hilo_guardado.start()
    
    # Mantenemos el programa principal vivo
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        while True:
            with data_lock:
                if LAST_POD:
                    pods = v1.list_namespaced_pod(
                        namespace=NAMESPACE_TARGET,
                        field_selector=FIELD_SELECTOR, 
                        watch=False
                    )

                    if len(pods.items) == 0:
                        print("Finalizando...")
                        FIN = True
                        sys.exit()
            time.sleep(WAIT_TIME)
    except KeyboardInterrupt:
        print("Deteniendo monitor...")