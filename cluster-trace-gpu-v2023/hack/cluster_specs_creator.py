from kubernetes import client, config
from kubernetes.client.rest import ApiException

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

    MIG_INSTANCES = 'mig-instances'
    ALL_NODES = []
    NODE = []
    GPU = {
        "mem": 0,
        "fp32": 0,
        "migLength": 0,
        "migInstances": []
    }
    MIG_INSTANCE = {
        "size": 0,
        "mem": 0,
        "fp32": 0
    }

    try:
        
        nodes = v1.list_node()

        prefix = 'kwok'
        nodes_kwok = [
            n for n in nodes.items 
            if n.metadata.name.startswith(prefix) # Que empiece por...
        ]

        for node in nodes_kwok:
            Instances = node.metadata.labels[MIG_INSTANCES]

    except ApiException as e:
        # Manejar interrupciones o errores de la conexión
        print(f"Error de API, esperando 5 segundos antes de reintentar: {e}")
    except Exception as e:
        # Manejar errores inesperados
        print(f"Error inesperado, esperando 10 segundos antes de reintentar: {e}")


if __name__ == '__main__':
    main()