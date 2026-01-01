import yaml
import sys
import os
from dotenv import load_dotenv

load_dotenv()

YAML_FILE_PATH = "trace/trace.yaml"
THEORY_DURATION_PODS_PATH = os.getenv('THEORY_DURATION_PODS_PATH')

if __name__ == "__main__":

    scheduledTimesPods = []

    try:
        with open(YAML_FILE_PATH, 'r') as f:
            documentos = yaml.load_all(f, Loader=yaml.SafeLoader)
        
            for manifiesto in documentos:
                    # Comprobación básica de si el documento es válido/no nulo
                    if manifiesto and isinstance(manifiesto, dict):
                        annotations = manifiesto['metadata']['annotations']

                        scheduledTime = int(annotations['customresource.com/scheduled-time'])
                        deletionTime = int(annotations['customresource.com/deletion-time'])

                        scheduledTimesPods.append(deletionTime-scheduledTime)

        with open(THEORY_DURATION_PODS_PATH, 'w', encoding='utf-8') as archivo:
            yaml.dump(scheduledTimesPods, archivo, allow_unicode=True)
            
            
    except FileNotFoundError:
        print(f"\n❌ Error: El archivo '{YAML_FILE_PATH}' no se encontró.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"\n❌ Error al parsear el archivo YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error al procesar el archivo: {e}")
        sys.exit(1)