import threading
import time
import yaml
import sys
from kubernetes import client, config, watch

data_lock = threading.Lock()

def request_with_to_int(num):
    if 'k' in num:
        number = int(float(num.lower().replace('k', '')) * 1000)
    else:
        number = int(num)
    return number

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

                annotations = pod.metadata.annotations
                if annotations is None or GPU_POS not in annotations:
                    continue
            
                nodeName = pod.spec.node_name
                gpuPos = int(pod.metadata.annotations[GPU_POS])
                podFp32 = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpufp32"])
                podMem = request_with_to_int(pod.spec.containers[0].resources.requests["customresource.com/gpuMemory"])
                
                with data_lock:
                    if tipo == 'ADDED' or tipo == 'MODIFIED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] += podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] += podMem
                    elif tipo == 'DELETED':
                        ALL_NODES[nodeName][gpuPos][FP32_USED_NAME] -= podFp32
                        ALL_NODES[nodeName][gpuPos][MEM_USED_NAME] -= podMem
                        
                print(f"fp32_used: {ALL_NODES[nodeName][gpuPos][FP32_USED_NAME]}, mem_used: {ALL_NODES[nodeName][gpuPos][MEM_USED_NAME]}")
        except Exception as e:
            print(f"Error en Watcher: {e}. Reintentando...")
            time.sleep(2)

def saver_thread():
    """Hilo encargado de guardar el estado cada 5 segundos"""
    print("Iniciando Guardado Periódico (cada 5s)...")
    while True:
        time.sleep(5) # Espera exacta de 5 segundos
        
        # with data_lock:
        #     # Tomamos una "foto" del estado actual
        #     snapshot = {
        #         "timestamp": time.strftime("%H:%M:%S"),
        #         "total_pods": len(monitor_data["pods_activos"]),
        #         "detalle_pods": monitor_data["pods_activos"].copy()
        #     }
            
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

# --- Lanzamiento del programa ---

if __name__ == "__main__":

    GPU_POS = 'gpuPos'
    FP32_NAME = 'fp32'
    MEM_NAME = 'mem'
    FP32_USED_NAME = 'fp32Used'
    MEM_USED_NAME = 'memUsed'

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