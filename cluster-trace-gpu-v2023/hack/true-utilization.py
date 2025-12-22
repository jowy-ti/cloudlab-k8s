import threading
import time
import yaml
import sys
import os
from kubernetes import client, config, watch
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np

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


def request_to_int(num):
    if 'k' in num:
        number = int(float(num.lower().replace('k', '')) * 1000)
    else:
        number = int(num)
    return number

def newpods_calculate_resources(nodeName, gpuPos, podFp32, podMem, isolation, migSize):

    global ALL_NODES

    totalFp32 = ALL_NODES[nodeName][gpuPos][FP32_TOTAL_NAME]
    totalMem = ALL_NODES[nodeName][gpuPos][MEM_TOTAL_NAME]

    ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] += podFp32
    ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] += podMem

    if isolation:
        if migSize != INVALID_MIGSIZE:
            ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] += MIG_INSTANCES_FP32[migSize] * totalFp32
            ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] += MIG_INSTANCES_MEM[migSize] * totalMem
        else:
            ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] = totalFp32
            ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] = totalMem
    else:
        ALL_NODES[nodeName][gpuPos][FP32_ALLOCATED_NAME] += podFp32
        ALL_NODES[nodeName][gpuPos][MEM_ALLOCATED_NAME] += podMem

def deadpods_calculate_resources(nodeName, gpuPos, podFp32, podMem, isolation, migSize):

    global ALL_NODES

    totalFp32 = ALL_NODES[nodeName][gpuPos][FP32_TOTAL_NAME]
    totalMem = ALL_NODES[nodeName][gpuPos][MEM_TOTAL_NAME]

    ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] -= podFp32
    ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] -= podMem

    if isolation:
        if migSize != INVALID_MIGSIZE:
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
    realDurationPods = []
    theoryDurationPods = []
    realCreationTimeName = 'realCreationTime'
    realDeletionTimeName = 'realDeletionTime'
    theoryScheduledTimeName = 'customresource.com/scheduled-time'
    theoryDeletionTimeName = 'customresource.com/deletion-time'
    podsAnnotations = {}
    podsResourceFp32 = {}
    podsResourceMem = {}
    podsNode = {}
    pastPodsName = set()
    runningPodsName = set()

    config.load_kube_config()
    v1 = client.CoreV1Api()

    while True:
        time.sleep(WAIT_TIME/4)
        try:
            pods = v1.list_namespaced_pod(
                namespace=NAMESPACE_TARGET, 
                field_selector="status.phase=Running"
            ).items

            runningPodsName = {p.metadata.name for p in pods}
            newPodsName = runningPodsName - pastPodsName
            deadPodsName = pastPodsName - runningPodsName

            newPods = [p for p in pods if p.metadata.name in newPodsName]

            for pod in newPods:
                
                INICIO = True
                annotations = pod.metadata.annotations
                podName = pod.metadata.name
                nodeName = pod.spec.node_name
                gpuPos = annotations.get(GPU_POS_NAME)
                migSize = annotations.get(MIG_SIZE_NAME)

                if annotations is None or nodeName is None or gpuPos is None or migSize is None:
                    continue      
                
                gpuPos = int(gpuPos)
                podFp32 = request_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpufp32"])
                podMem = request_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpuMemory"])
                isolation = False

                podsAnnotations[podName] = annotations
                podsResourceFp32[podName] = podFp32
                podsResourceMem[podName] = podMem
                podsNode[podName] = nodeName

                if V100Fp32 == podFp32 and V100Mem == podMem:
                    isolation = True

                with data_lock:
                    newpods_calculate_resources(nodeName, gpuPos, podFp32, podMem, isolation, migSize)

                print(f"added pod: {podName}, podFp32: {podFp32}, podMem: {podMem}")

            for podName in deadPodsName:
                annotations = podsAnnotations[podName]
                podFp32 = podsResourceFp32[podName]
                podMem = podsResourceMem[podName]
                nodeName = podsNode[podName]
                gpuPos = int(annotations.get(GPU_POS_NAME))
                migSize = annotations.get(MIG_SIZE_NAME)
                isolation = False

                if V100Fp32 == podFp32 and V100Mem == podMem:
                    isolation = True

                with data_lock:
                    deadpods_calculate_resources(nodeName, gpuPos, podFp32, podMem, isolation, migSize)

                realCreationTime = int(annotations[realCreationTimeName])
                realDeletionTime = int(annotations[realDeletionTimeName])
                theoryScheduledTime = int(annotations[theoryScheduledTimeName])
                theoryDeletionTime = int(annotations[theoryDeletionTimeName])

                realDurationPods.append(realDeletionTime - realCreationTime)
                theoryDurationPods.append(theoryDeletionTime - theoryScheduledTime)

                if podName == LAST_POD_NAME:
                    with data_lock:
                        LAST_POD = True

                # print(f"deleted pod: {podName}, podFp32: {podFp32}, podMem: {podMem}")

            pastPodsName = runningPodsName
                    
            if LAST_POD and len(pods) == 0:
                theoryDurationPods.sort()
                realDurationPods.sort()

                y_teorica = np.linspace(0, 1, len(theoryDurationPods))
                y_real = np.linspace(0, 1, len(realDurationPods))

                plt.figure(figsize=(10, 6))

                # Dibujar las líneas de la CDF (usando drawstyle='steps-post' para que sea escalonado)
                plt.step(theoryDurationPods, y_teorica, label='Tiempo Teórico', where='post', linewidth=2, linestyle='-')
                plt.step(realDurationPods, y_real, label='Tiempo Real', where='post', linewidth=2, color='orange', linestyle='--')

                # Personalización estética (Sin líneas que crucen las barras/curvas)
                plt.title('CDF: Comparativa de Tiempos Teóricos vs Reales', fontsize=14)
                plt.xlabel('Tiempo de Ejecución (segundos)', fontsize=12)
                plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

                # Mostrar el 50% (mediana)
                plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
                plt.text(max(realDurationPods)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

                plt.legend()
                plt.tight_layout()
                plt.savefig("plots/duration_pods.png")
                sys.exit()

        except Exception as e:
            print(f"Error watch: {e}. Reintentando...")
            time.sleep(2)

def saver_thread():
    """Hilo encargado de guardar el estado cada 5 segundos"""

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

            # print(f"fp32Used: {fp32Used}, memUsed: {memUsed}, numGpuOccuped: {numGpuOccuped}, LAST_POD: {LAST_POD}")
            if LAST_POD and numGpuOccuped == 0:
                plt.figure(figsize=(10, 6))
                plt.plot(timeline, gpuOccupation, label='Ocupación', color='blue', linestyle='-')
                plt.plot(timeline, gpuUtilization, label='Utilización', color='red', linestyle='--')
                plt.plot(timeline, gpuAllocated, label='Asignación', color='green', linestyle='-.')
                plt.ylim(0, 100)
                plt.legend()
                plt.savefig("plots/utilization1.png")

                plt.figure(figsize=(10, 6))
                plt.plot(timeline, gpuUtilizationFp32, label='Utilización fp32', color='darkred', linestyle=':')
                plt.plot(timeline, gpuUtilizationMem, label='Utilización mem', color='darkgreen', linestyle='--')
                plt.plot(timeline, gpuAllocatedFp32, label='Asignación fp32', color='lightcoral', linestyle='-.')
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
    INVALID_MIGSIZE = '-1'
    LAST_POD_NAME = os.getenv('LAST_POD_NAME')
    LAST_POD = False
    WAIT_TIME = 4
    FIN = False
    INICIO = False

    data_lock = threading.Lock()

    try:
        with open("objects/all-nodes.yaml", "r") as archivo:
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