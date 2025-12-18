import threading
import time
import yaml
import sys
from kubernetes import client, config, watch

data_lock = threading.Lock()
WAIT_TIME = 5
V100Fp32 = 14000
V100Mem = 16000

MIG_SIZE= {
    '1': int((((1/8) + (1/7)) / 2) * 100), 
    '2': int((((2/8) + (2/7)) / 2) * 100),
    '3': int((((4/8) + (3/7)) / 2) * 100),
    '4': int((((4/8) + (4/7)) / 2) * 100),
    '7' : 100
    }

def total_memory_fp32():
    fp32Total = 0
    memTotal = 0

    with data_lock:
        for node in ALL_NODES:
            for gpu in ALL_NODES[node]:
                fp32Total += gpu[FP32_NAME]
                memTotal += gpu[MEM_NAME]
    
    return fp32Total, memTotal


def request_with_to_int(num):
    if 'k' in num:
        number = int(float(num.lower().replace('k', '')) * 1000)
    else:
        number = int(num)
    return number

def calculate_usage(nodeName, gpuPos, tipo, podFp32, podMem, usage):

    if tipo == 'ADDED':
        ALL_NODES[nodeName][gpuPos][USAGE_NAME] += usage
    elif tipo == 'DELETED':
        ALL_NODES[nodeName][gpuPos][USAGE_NAME] -= usage

def calculate_allocated(nodeName, gpuPos, tipo, podFp32, podMem, isolation, migSize, usage):

    if tipo == 'ADDED':
        if isolation:
            if migSize != '':
                ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME] += MIG_SIZE[migSize]
            else:
                ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME] = 1
        else:
            ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME] += usage

    elif tipo == 'DELETED':
        if isolation:
            if migSize != '':
                ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME] -= MIG_SIZE[migSize]
            else:
                ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME] = 0
        else:
            ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME] -= usage

def k8s_watch_thread():
    """Hilo encargado de escuchar eventos de Kubernetes"""

    global ALL_NODES

    config.load_kube_config()
    v1 = client.CoreV1Api()
    w = watch.Watch()
    print("Iniciando Watcher...")
    while True:
        try:
            for event in w.stream(v1.list_pod_for_all_namespaces):
                tipo = event['type']
                pod = event['object']

                if tipo == 'MODIFIED':
                    continue

                annotations = pod.metadata.annotations
                if annotations is None or GPU_POS not in annotations:
                    continue
                 
                nodeName = pod.spec.node_name
                gpuPos = int(pod.metadata.annotations[GPU_POS])
                podFp32 = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpufp32"])
                podMem = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpuMemory"])
                isolation = False
                migSize = ''
                allocated = 0

                if annotations[MIG_SIZE_NAME] is not None:
                    migSize = pod.metadata.annotations[MIG_SIZE_NAME]

                if V100Fp32 == podFp32 and V100Mem == podMem:
                    isolation = True
                
                with data_lock:
                    if tipo == 'ADDED': # or tipo == 'MODIFIED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] += podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] += podMem
                        # Allocated
                        if isolation:
                            if migSize != '':
                                allocated = MIG_SIZE[migSize]
                            else:
                                allocated = 1

                    elif tipo == 'DELETED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] -= podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] -= podMem
                        # Allocated
                        if isolation:
                            if migSize != '':
                                allocated = -MIG_SIZE[migSize]
                            else:
                                allocated = -1
                                            
                    totalFp32 = ALL_NODES[nodeName][gpuPos][FP32_NAME]
                    totalMem = ALL_NODES[nodeName][gpuPos][MEM_NAME]

                    fp32RatioUsage = podFp32 / totalFp32
                    memRatioUsage = podMem / totalMem
                    usage = int(((fp32RatioUsage + memRatioUsage) / 2) * 100)

                    calculate_usage(nodeName, gpuPos, tipo, podFp32, podMem, usage)
                    calculate_allocated(nodeName, gpuPos, tipo, podFp32, podMem, isolation, migSize, usage)

                print(f"fp32_used: {ALL_NODES[nodeName][gpuPos][FP32_USED_NAME]}, mem_used: {ALL_NODES[nodeName][gpuPos][MEM_USED_NAME]}")
                print(f"Usage: {ALL_NODES[nodeName][gpuPos][USAGE_NAME]}, Allocated: {ALL_NODES[nodeName][gpuPos][ALLOCATED_NAME]}")
        except Exception as e:
            print(f"Error en Watcher: {e}. Reintentando...")
            time.sleep(2)

def saver_thread():
    """Hilo encargado de guardar el estado cada 5 segundos"""
    print("Iniciando Guardado Periódico (cada 5s)...")

    time.sleep(2)

    fp32Total, memTotal = total_memory_fp32()
    gpuUtilization = []
    gpuAllocated = []
    gpuOccupation = []

    # print(f"fp32Total: {fp32Total}, memTotal: {memTotal}")

    while True:
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
                    fp32Allocated += gpu[FP32_NAME] * gpu[ALLOCATED_NAME]
                    memAllocated += gpu[MEM_NAME] * gpu[ALLOCATED_NAME]

                    if fp32Used != 0 or memUsed != 0:
                        numGpuOccuped += 1

        fp32UsedRatio = fp32Used / fp32Total
        memUsedRatio = memUsed / memTotal
        fp32AllocatedRatio = fp32Allocated / fp32Total
        memAllocatedRatio = memAllocated / memTotal

        gpuOccupation.append(numGpuOccuped)
        gpuUtilization.append()
        gpuAllocated.append()
        
        # print(f"fp32Used: {fp32Used}, memUsed: {memUsed}")
            
        # # Guardamos en el archivo YAML (esto no bloquea al Watcher)
        # try:
        #     # Opción A: Sobreescribir el archivo con el estado actual
        #     with open('estado_actual.yaml', 'w') as f:
        #         yaml.dump(snapshot, f, sort_keys=False)
            
        #     # Opción B: Ir acumulando para la gráfica (Append)
        #     with open('historico_para_grafica.yaml', 'a') as f:
        #         f.write("---\n") # Separador de documentos YAML
        #         yaml.dump(snapshot, f, sort_keys=False)
                
        #     print(f"[{snapshot['timestamp']}] Estado guardado correctamente.")
        # except Exception as e:
        #     print(f"Error al guardar: {e}")

        time.sleep(WAIT_TIME)

if __name__ == "__main__":

    GPU_POS = 'gpuPos'
    FP32_NAME = 'fp32'
    MEM_NAME = 'mem'
    FP32_USED_NAME = 'fp32Used'
    MEM_USED_NAME = 'memUsed'
    USAGE_NAME = 'usage'
    ALLOCATED_NAME = 'allocated'
    MIG_SIZE_NAME = 'migSize'

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
            time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo monitor...")