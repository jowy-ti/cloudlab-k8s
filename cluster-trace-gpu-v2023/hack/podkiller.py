import time
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# --- Configuración ---
# La clave de la anotación que contiene el tiempo de finalización (Unix Timestamp en segundos)
ANNOTATION_KEY_KILL_TIME = 'deadline'
# Intervalo de tiempo (en segundos) que el script esperará entre revisiones de Pods.
POLL_INTERVAL_SECONDS = 1
FIELD_SELECTOR = 'status.phase=Running'
NAMESPACE_TARGET = 'default'
LAST_POD_NAME = os.getenv('LAST_POD_NAME')
INITIAL_TIME = 0
INICIO = True
LAST_POD = False

def kill_pod_if_expired(v1: client.CoreV1Api, pod):
    """
    Comprueba las anotaciones del Pod y lo elimina si su tiempo de vida ha expirado.
    """
    global INITIAL_TIME
    global INICIO
    global LAST_POD
    pod_name = pod.metadata.name
    namespace = pod.metadata.namespace

    # Miramos si es el primer pod
    if INICIO:
        INITIAL_TIME = int(time.time())
        INICIO = False
        print('El cronómetro comienza ahora!')

    if pod_name == LAST_POD_NAME and not INICIO:
        LAST_POD = True
    
    # Ignorar Pods en fase de terminación
    if pod.metadata.deletion_timestamp:
        return

    annotations = pod.metadata.annotations
    if not annotations or ANNOTATION_KEY_KILL_TIME not in annotations:
        return # No tiene la anotación de tiempo, ignorar.

    # Obtener el tiempo actual como Unix Epoch Time (entero)
    current_time = int(time.time())
    
    try:
        # Leer el timestamp de la anotación y convertirlo a entero
        kill_timestamp = int(annotations[ANNOTATION_KEY_KILL_TIME])
    except ValueError:
        print(f"Advertencia: Anotación '{ANNOTATION_KEY_KILL_TIME}' en Pod {namespace}/{pod_name} no es un número válido. Ignorando.")
        return
        
    # Lógica de Eliminación: ¿El tiempo de finalización ya pasó?
    if current_time >= kill_timestamp:
        # print(f"!!! TIEMPO EXPIRADO - ACTIVANDO ELIMINACIÓN !!!")
        # print(f"  Pod: {namespace}/{pod_name}")
        # print(f"  Tiempo actual: {current_time}, Tiempo límite: {kill_timestamp}")
        
        # Eliminar el Pod
        try:
            # print(f"Intentando eliminar el Pod: {pod_name} en namespace {namespace}...")
            v1.delete_namespaced_pod(
                name=pod_name, 
                namespace=namespace, 
                body=client.V1DeleteOptions()
            )
            # print(f"Pod {pod_name} eliminado exitosamente.")
        except ApiException as e:
            if e.status == 404:
                print(f"Advertencia: Pod {pod_name} ya no existe.")
            else:
                # Si hay un error de permisos (403), la ejecución fallará aquí.
                print(f"Error al eliminar Pod {pod_name}: {e}")
    else:
        # El Pod aún tiene tiempo de vida. 
        # print(f"Pod {pod_name} con tiempo restante: {kill_timestamp - current_time}s")
        pass


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
    
    # Bucle infinito de POLLING
    while True:
        try:
            # print(f"\n--- REVISIÓN PERIÓDICA: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} ---")
            
            # 2. Listar todos los Pods (el Polling)
            pods = v1.list_namespaced_pod(
                namespace=NAMESPACE_TARGET,
                field_selector=FIELD_SELECTOR, 
                watch=False
            )

            if LAST_POD and len(pods.items) == 0:
                print(f"Tiempo total: {int(time.time()) - INITIAL_TIME}")
                sys.exit()

            # 3. Procesar cada Pod
            for pod in pods.items:
                kill_pod_if_expired(v1, pod)

            # 4. Esperar el intervalo de Polling
            # print(f"Revisión completada. Esperando {POLL_INTERVAL_SECONDS} segundos...")
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