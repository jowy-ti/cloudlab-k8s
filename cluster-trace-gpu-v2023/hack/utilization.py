import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import sys
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

FIELD_SELECTOR = 'status.phase=Running'
NAMESPACE_TARGET = 'default'
POLL_INTERVAL_SECONDS = 5
LAST_POD_NAME = os.getenv('LAST_POD_NAME')
INICIO = True
LAST_POD = False

def main():
    """
    Función principal que configura la conexión y el bucle de POLING periódico.
    """
    print("Iniciando el monitor de Pods en el Control Plane (Modo Polling)...")
    
    # Carga de la configuración Kube-Config
    try:
        config.load_kube_config()
        print("Configuración Kube-Config local cargada correctamente.")
    except Exception as e:
        print(f"ERROR: No se pudo cargar la configuración de Kubernetes. Asegúrate de que el archivo kubeconfig es accesible. {e}")
        return
    
    v1 = client.CoreV1Api()

    global INICIO
    global LAST_POD
    Utilization = []
    Times = []
    SumTime = 0

    while True:
        try:

            pods = v1.list_namespaced_pod(
                namespace=NAMESPACE_TARGET,
                field_selector=FIELD_SELECTOR, 
                watch=False
            )

            num_pods = len(pods.items)
            
            if LAST_POD and num_pods == 0:
                print("Guardando gráfico...")
                fig, ax = plt.subplots()
                ax.plot(Times, Utilization)
                plt.savefig("plots/utilization.png")
                sys.exit()

            for pod in pods.items:
                
                pod_name = pod.metadata.name

                if INICIO:
                    INICIO = False

                if not INICIO and pod_name == LAST_POD_NAME:
                    LAST_POD = True            

            if not INICIO:
                Utilization.append(num_pods)
                Times.append(SumTime)
                SumTime += POLL_INTERVAL_SECONDS

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