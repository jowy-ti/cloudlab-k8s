import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import sys

FIELD_SELECTOR = 'status.phase=Running'
NAMESPACE_TARGET = 'default'
POLL_INTERVAL_SECONDS = 5

def main():
    """
    Función principal que configura la conexión y el bucle de POLING periódico.
    """
    print("Iniciando el monitor de Pods en el Control Plane (Modo Polling)...")
    
    # 1. Carga de la configuración Kube-Config
    try:
        config.load_kube_config()
        print("Configuración Kube-Config local cargada correctamente.")
    except Exception as e:
        print(f"ERROR: No se pudo cargar la configuración de Kubernetes. Asegúrate de que el archivo kubeconfig es accesible. {e}")
        return
    
    v1 = client.CoreV1Api()

    INICIO_FIN = True

    while True:
        try:

            pods = v1.list_namespaced_pod(
                namespace=NAMESPACE_TARGET,
                field_selector=FIELD_SELECTOR,  # Opcional: para filtrar por estado
                watch=False
            )

            if pods.items and INICIO_FIN: # Utilizar el nombre del pod para dar el inicio y el final
                INICIO_FIN = False

            if not pods.items and not INICIO_FIN: # Utilizar el nombre del pod para dar el inicio y el final
                sys.exit()
            
            # print(f"{len(pods.items)}")

            time.sleep(POLL_INTERVAL_SECONDS)


        except ApiException as e:
            # Manejar interrupciones o errores de la conexión
            print(f"Error de API, esperando 5 segundos antes de reintentar: {e}")
            time.sleep(5)
        except Exception as e:
            # Manejar errores inesperados
            print(f"Error inesperado, esperando 10 segundos antes de reintentar: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()