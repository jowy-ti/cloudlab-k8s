import time
import yaml
import sys
import os
from kubernetes import client, config
from dotenv import load_dotenv

def scrapping():

    last_pod = False
    pastPodsName = set()
    runningPodsName = set()
    podTimes = []

    config.load_kube_config()
    v1 = client.CoreV1Api()

    while True:
        time.sleep(WAIT_TIME)
        try:
            pods = v1.list_namespaced_pod(
                namespace=NAMESPACE_TARGET, 
                field_selector="status.phase=Running"
            ).items

            runningPodsName = {p.metadata.name for p in pods}
            newPodsName = runningPodsName - pastPodsName
            newPods = [p for p in pods if p.metadata.name in newPodsName]

            for pod in newPods:
                annotations = pod.metadata.annotations
                podName = pod.metadata.name
                podSchedulingTime = float(annotations.get(ANNOTATION_NAME))

                if podName == LAST_POD_NAME:
                    last_pod = True

                res = podSchedulingTime/1000.0
                podTimes.append(round(res, 3))

            if len(pods.items) == 0 and last_pod:
                with open(SCHEDULING_TIMES_PATH, 'w', encoding='utf-8') as archivo:
                        yaml.dump(podTimes, archivo, allow_unicode=True)
                sys.exit()

            pastPodsName = runningPodsName
        
        except Exception as e:
            print(f"Error watch: {e}. Reintentando...")
            time.sleep(2)

if __name__ == "__main__":

    load_dotenv()

    LAST_POD_NAME = os.getenv('LAST_POD_NAME')
    WAIT_TIME = 1
    NAMESPACE_TARGET = 'default'
    SCHEDULING_TIMES_PATH = 'objects/gpu_scale.yaml'
    ANNOTATION_NAME = 'schedulingDuration'

    scrapping()