import yaml
import subprocess
import sys
import os
import time
from dotenv import load_dotenv

load_dotenv()

# --- Configuración ---
# Cambia 'manifiestos.yaml' por la ruta de tu archivo YAML 
YAML_FILE_PATH = "trace/trace.yaml" 
CREATION_TIME_PAST = 0
LAST_POD_NAME = os.getenv('LAST_POD_NAME')
# --- Fin Configuración ---

def aplicar_manifest_por_separado(manifesto_yaml):
    """
    Guarda un único manifesto YAML a un archivo temporal y lo aplica con kubectl.
    """
    global CREATION_TIME_PAST
    temp_file_path = "temp_manifest.yaml"
    
    try:

        creationTime = None
        metadata = manifesto_yaml['metadata']

        if 'annotations' in metadata and metadata['annotations'] is not None:
            annotations = metadata['annotations']
            if 'customresource.com/creation-time' in annotations:
                creationTime = float(annotations['customresource.com/creation-time'])
            else:
                return

        if creationTime == None:
            return
        
        tiempo_restante = int(creationTime - CREATION_TIME_PAST)
        CREATION_TIME_PAST = creationTime

        # print(f"creationTime: {creationTime}")
        print(f"Tiempo de espera del pod: {tiempo_restante}")

        if tiempo_restante > 0:
            time.sleep(tiempo_restante)

        # 1. Escribir el manifiesto individual a un archivo temporal
        with open(temp_file_path, 'w') as temp_file:
            # Dumps crea un string YAML a partir del objeto Python (dict)
            yaml.dump(manifesto_yaml, temp_file, default_flow_style=False)
        
        # 2. Ejecutar el comando kubectl apply
        print(f"\n🚀 Aplicando recurso: {manifesto_yaml.get('kind', 'Recurso Desconocido')}")
        
        resultado = subprocess.run(
            ['kubectl', 'apply', '-f', temp_file_path],
            check=True,  # Lanza CalledProcessError si el comando falla
            capture_output=True,
            text=True
        )
        
        print(f"✅ Éxito:\n{resultado.stdout.strip()}")

        if metadata['name'] == LAST_POD_NAME:
            print("Fin de la creación de pods")
            sys.exit()
        
    except FileNotFoundError:
        print(f"❌ Error: El comando 'kubectl' no se encontró. Asegúrate de que está en tu PATH.")
        sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al aplicar el recurso:")
        print(f"   Código de error: {e.returncode}")
        print(f"   Mensaje de error (stderr):\n{e.stderr.strip()}")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
        
    finally:
        # 3. Limpiar: Eliminar el archivo temporal
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def aplicar_yaml_multifichero(file_path):
    """
    Lee el archivo YAML multifichero y procesa cada documento.
    """
    try:
        with open(file_path, 'r') as f:
            # load_all() es clave: lee todos los documentos separados por '---'
            documentos = yaml.load_all(f, Loader=yaml.SafeLoader)
            
            recursos_aplicados = 0
            for manifesto in documentos:
                # Comprobación básica de si el documento es válido/no nulo
                if manifesto and isinstance(manifesto, dict):
                    aplicar_manifest_por_separado(manifesto)
                    recursos_aplicados += 1

            if recursos_aplicados == 0:
                 print("\n⚠️ Advertencia: No se encontraron recursos válidos en el archivo YAML.")
                 
            print(f"\n✨ Proceso completado. Total de recursos aplicados: {recursos_aplicados}")

    except FileNotFoundError:
        print(f"\n❌ Error: El archivo '{file_path}' no se encontró.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"\n❌ Error al parsear el archivo YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error al procesar el archivo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print(f"Iniciando aplicación de manifiestos desde: {YAML_FILE_PATH}")
    aplicar_yaml_multifichero(YAML_FILE_PATH)