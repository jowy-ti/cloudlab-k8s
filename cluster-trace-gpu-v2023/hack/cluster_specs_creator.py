from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml

def main():
    print("Iniciando el monitor de Pods en el Control Plane (Modo Polling)...")
    
    # 1. Carga de la configuración Kube-Config
    try:
        config.load_kube_config()
        print("Configuración Kube-Config local cargada correctamente.")
    except Exception as e:
        print(f"ERROR: No se pudo cargar la configuración de Kubernetes. Asegúrate de que el archivo kubeconfig es accesible. {e}")
        return
    
    v1 = client.CoreV1Api()

    ALL_NODES = {}
    FP32 = "nvidia.com/gpu.fp32.GFLOPS"
    MEM = "nvidia.com/gpu.memory"
    GPU_COUNT = "nvidia.com/gpu.count"

    try:

        nodes = v1.list_node()

        prefix = 'kwok'
        nodes_kwok = [
            n for n in nodes.items 
            if n.metadata.name.startswith(prefix) 
        ]

        for node in nodes_kwok:
            gpusfp32 = node.metadata.labels[FP32]
            gpusmem = node.metadata.labels[MEM]
            numgpu = node.metadata.labels[GPU_COUNT]
            gpuname = node.metadata.name
            NODE = []
            
            for _ in range(int(numgpu)):
                GPU = {}
                GPU["fp32Total"] = int(gpusfp32)
                GPU["memTotal"] = int(gpusmem)
                GPU["fp32Used"] = 0
                GPU["memUsed"] = 0
                GPU["fp32Allocated"] = 0
                GPU["memAllocated"] = 0
                NODE.append(GPU)

            ALL_NODES[gpuname] = NODE
        
        with open("objects/all-nodes.yaml", "w") as archivo:
            yaml.dump(ALL_NODES, archivo, default_flow_style=False, sort_keys=False)

    except ApiException as e:
        # Manejar interrupciones o errores de la conexión
        print(f"Error de API: {e}")
    except Exception as e:
        # Manejar errores inesperados
        print(f"Error inesperado: {e}")


if __name__ == '__main__':
    main()