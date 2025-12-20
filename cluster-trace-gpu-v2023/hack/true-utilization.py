import threading
import time
import yaml
import sys
import os
from kubernetes import client, config, watch
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

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

def k8s_watch_thread():
    """Hilo encargado de escuchar eventos de Kubernetes"""

    global ALL_NODES
    global LAST_POD
    global INICIO

    V100Fp32 = 14000
    V100Mem = 16000
    totalGpusFp32Used = 0
    totalGpusMemUsed = 0
    podCont = 0
    amountPods = []
    realDurationPods = []
    theoryDurationPods = []
    podsAdded = []
    realCreationTimeName = 'realCreationTime'
    realDeletionTimeName = 'realDeletionTime'
    theoryCreationTimeName = 'customresource.com/creation-time'
    theoryDeletionTimeName = 'customresource.com/deletion-time'
    contADD = 0
    contDEL = 0

    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()
    print("Iniciando Watcher...")
    while True:
        try:
            for event in w.stream(v1.list_namespaced_pod, namespace=NAMESPACE_TARGET):
                tipo = event['type']
                pod = event['object']

                annotations = pod.metadata.annotations

                if annotations is None:
                    continue                    
                
                podName = pod.metadata.name

                if tipo == 'ADDED':
                    podsAdded.append(podName)

                nodeName = pod.spec.node_name
                gpuPos = int(pod.metadata.annotations[GPU_POS_NAME])
                migSize = pod.metadata.annotations[MIG_SIZE_NAME]
                podFp32 = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpufp32"])
                podMem = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpuMemory"])
                isolation = False
                migSize = ''

                print(f"migSize: {migSize}")
                print(f" gpuPos: {pod.metadata.annotations[GPU_POS_NAME]}")

                if V100Fp32 == podFp32 and V100Mem == podMem:
                    isolation = True

                with data_lock:
                    if tipo == 'MODIFIED' and podName in podsAdded: # or tipo == 'MODIFIED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] += podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] += podMem
                        totalGpusFp32Used += podFp32
                        totalGpusMemUsed += podMem
                        INICIO = True
                        podsAdded.remove(podName)
                        contADD += 1

                    elif tipo == 'DELETED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] -= podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] -= podMem
                        totalGpusFp32Used -= podFp32
                        totalGpusMemUsed -= podMem
                        contDEL += 1

                        podCont += 1
                        realCreationTime = int(annotations[realCreationTimeName])
                        realDeletionTime = int(annotations[realDeletionTimeName])
                        theoryCreationTime = int(annotations[theoryCreationTimeName])
                        theoryDeletionTime = int(annotations[theoryDeletionTimeName])

                        amountPods.append(podCont)
                        realDurationPods.append(realDeletionTime - realCreationTime)
                        theoryDurationPods.append(theoryDeletionTime - theoryCreationTime)

                        if podName == LAST_POD_NAME:
                            LAST_POD = True

                    if LAST_POD:
                        print(f"totalGpusFp32Used: {totalGpusFp32Used}, totalGpusMemUsed: {totalGpusMemUsed}")
                        print(f"contADD: {contADD}, contDEL: {contDEL}")
                    if LAST_POD and totalGpusFp32Used == 0 and totalGpusMemUsed == 0:
                        plt.figure(1)
                        plt.plot(amountPods, realDurationPods, label='real duration', linestyle='-')
                        plt.plot(amountPods, theoryDurationPods, label='theory duration', linestyle='--')
                        plt.xticks(range(min(amountPods), max(amountPods) + 1))
                        plt.legend()
                        plt.savefig("plots/duration_pods.png")
                                                                    
                    calculate_allocated(nodeName, gpuPos, tipo, podFp32, podMem, isolation, migSize)

        except Exception as e:
            print(f"Error en Watcher: {e}. Reintentando...")
            time.sleep(2)

def saver_thread():
    """Hilo encargado de guardar el estado cada 5 segundos"""

    time.sleep(2)

    global FIN
    global LAST_POD

    fp32Total, memTotal, gpuTotal = total_memory_fp32_gpu()

    gpuUtilization = []
    gpuAllocated = []
    gpuOccupation = []
    timeline = []
    gpuUtilizationFp32 = []
    gpuUtilizationMem = []
    gpuAllocatedFp32 = []
    gpuAllocatedMem = []
    INIT_TIME = int(time.time())

    while True:   

        time.sleep(WAIT_TIME)

        if not INICIO:
            continue

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

                    if gpu[FP32_USED_NAME] != 0 or gpu[MEM_USED_NAME] != 0: 
                        numGpuOccuped += 1

            if LAST_POD and numGpuOccuped == 0:
                plt.figure(2)
                plt.plot(timeline, gpuOccupation, label='Ocupación', color='blue', linestyle='-')
                plt.plot(timeline, gpuUtilization, label='Utilización', color='red', linestyle='--')
                plt.plot(timeline, gpuAllocated, label='Asignación', color='green', linestyle='-.')
                plt.ylim(0, 100)
                plt.legend()
                plt.savefig("plots/utilization1.png")

                plt.figure(3)
                plt.plot(timeline, gpuUtilizationFp32, label='Utilización fp32', color='darkred', linestyle=':')
                plt.plot(timeline, gpuUtilizationMem, label='Utilización mem', color='lightcoral', linestyle='--')
                plt.plot(timeline, gpuAllocatedFp32, label='Asignación fp32', color='darkgreen', linestyle='-.')
                plt.plot(timeline, gpuAllocatedMem, label='Asignación mem', color='lightgreen', linestyle='-')
                plt.ylim(0, 100)
                plt.legend()
                plt.savefig("plots/utilization2.png")
                FIN = True
                sys.exit()

        Occupation = int((numGpuOccuped / gpuTotal)  * 100)
        Utilization = int((((fp32Used / fp32Total) + (memUsed / memTotal)) / 2) * 100)
        Allocated = int((((fp32Allocated / fp32Total) + (memAllocated / memTotal)) / 2) * 100)
        UtilizationFp32Ratio = int((fp32Used / fp32Total) * 100)
        UtilizationMemRatio = int((memUsed / memTotal) * 100)
        AllocatedFp32Ratio = int((fp32Allocated / fp32Total) * 100)
        AllocatedMemRatio = int((memAllocated / memTotal) * 100)

        gpuOccupation.append(Occupation)
        gpuUtilization.append(Utilization)
        gpuAllocated.append(Allocated)
        gpuUtilizationFp32.append(UtilizationFp32Ratio)
        gpuUtilizationMem.append(UtilizationMemRatio)
        gpuAllocatedFp32.append(AllocatedFp32Ratio)
        gpuAllocatedMem.append(AllocatedMemRatio)

        timeline.append(int(time.time() - INIT_TIME))

if __name__ == "__main__":

    GPU_POS_NAME = 'gpuPos'
    FP32_TOTAL_NAME = 'fp32Total'
    MEM_TOTAL_NAME = 'memTotal'
    FP32_USED_NAME = 'fp32Used'
    MEM_USED_NAME = 'memUsed'
    FP32_ALLOCATED_NAME = 'fp32Allocated'
    MEM_ALLOCATED_NAME = 'memAllocated'
    MIG_SIZE_NAME = 'migSize'
    NAMESPACE_TARGET = 'default'
    LAST_POD_NAME = os.getenv('LAST_POD_NAME')
    LAST_POD = False
    WAIT_TIME = 4
    FIN = False
    INICIO = False

    data_lock = threading.Lock()

    try:
        with open("all-nodes.yaml", "r") as archivo:
            ALL_NODES = yaml.safe_load(archivo)
    except FileNotFoundError:
        print("Error: El archivo no existe.")
    except yaml.YAMLError as e:
        print(f"Error al leer el archivo YAML: {e}")

    # Creamos los dos hilos
    hilo_escucha = threading.Thread(target=k8s_watch_thread, daemon=True)
    hilo_guardado = threading.Thread(target=saver_thread, daemon=True)
    
    # Los iniciamos
    hilo_escucha.start()
    hilo_guardado.start()
    
    # Mantenemos el programa principal vivo
    try:
        while True:
            with data_lock:
                if FIN:
                    sys.exit()

            time.sleep(WAIT_TIME)
    except KeyboardInterrupt:
        print("Deteniendo monitor...")