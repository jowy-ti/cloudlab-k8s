import numpy as np
import matplotlib.pyplot as plt
import os
import pandas as pd
import math


if __name__ == '__main__':
    # dfp = pd.read_csv('../csv/trace.csv', dtype={'gpu_index': str})
    dfp = pd.read_csv('../csv/openb_pod_list_cpu0.csv', dtype={'gpu_index': str})

    deletionTime = dfp['deletion_time'].to_numpy()
    scheduledTime = dfp['scheduled_time'].to_numpy()
    creationTime = dfp['creation_time'].to_numpy()

    # Si el valor en scheduledTime es NaN, toma el de creationTime, si no, deja el de scheduledTime
    scheduledTime = np.where(np.isnan(scheduledTime), creationTime, scheduledTime)
    
    podDurations = deletionTime - scheduledTime

    # Calcula la diferencia entre elementos consecutivos
    # [a, b, c] -> [a, b-a, c-b]
    creationTime = np.diff(creationTime, prepend=creationTime[0])

    q1 = np.percentile(podDurations, 25)
    q3 = np.percentile(podDurations, 95)
    iqr = q3 - q1

    # Definimos los límites (típicamente 1.5 veces el IQR)
    limite_superior = q3 + 1.5 * iqr

    # Filtramos: nos quedamos solo con los que NO son outliers
    mask_limpios = podDurations <= limite_superior
    podDurations_filt = podDurations[mask_limpios]
    # creationTime_filt = creationTime[mask_limpios]

    print(f"Pods eliminados: {len(podDurations) - len(podDurations_filt)}")

    conj_pods = 500
    n_bloques_c = len(creationTime) // conj_pods
    n_bloques_d = len(podDurations_filt) // conj_pods

    creation_reshape = creationTime[:n_bloques_c*conj_pods].reshape(-1, conj_pods)
    duration_reshape = podDurations_filt[:n_bloques_d*conj_pods].reshape(-1, conj_pods)

    # 2. Sumamos cada fila (cada bloque de 500)
    creation_por_bloque = np.sum(creation_reshape, axis=1)
    duration_por_bloque = np.sum(duration_reshape, axis=1)

    print("pod waits")
    cont = 0
    for num in creation_por_bloque:
        print(f"({cont*conj_pods}-{(cont+1)*conj_pods}): {num/conj_pods}")
        cont += 1

    print("pod durations")
    cont = 0
    for num in duration_por_bloque:
        print(f"({cont*conj_pods}-{(cont+1)*conj_pods}): {num}")
        cont += 1
    # cont = 0
    # for num1, num2 in zip(creation_por_bloque, duration_por_bloque):
    #     print(f"({cont*conj_pods}-{(cont+1)*conj_pods}): {num2/num1}")
    #     cont += 1
    cont = 0
    salt = 499
    lindar = 10000
    for i, num in enumerate(podDurations):
        if num > lindar:
            cont += 1
        if salt <= i:
            print(f"tareas mayores({salt-499}-{salt}): {cont}")
            salt += conj_pods
            cont = 0

    # for num in range(0, len(deletionTime), conj_pods):
    #     plt.figure(figsize=(10, 6))
    #     plt.plot(range(len(podDurations_filt[num:num+conj_pods])), podDurations_filt[num:num+conj_pods], label='Duración', color='darkred', linestyle=':')

    #     plt.title('Duración de pods', fontsize=14)
    #     plt.xlabel('Pods', fontsize=12)
    #     plt.ylabel('Tiempo', fontsize=12)
    #     plt.legend()
    #     plt.savefig(f"plots/trace_analisis/pod_traffic({num}-{num+conj_pods}).png")

    #     plt.figure(figsize=(10, 6))
    #     plt.plot(range(len(creationTime[num:num+conj_pods])), creationTime[num:num+conj_pods], label='Espera de creación', color='darkred', linestyle=':')

    #     plt.title('Tiempos entre creación', fontsize=14)
    #     plt.xlabel('Pods', fontsize=12)
    #     plt.ylabel('Tiempo', fontsize=12)
    #     plt.legend()
    #     plt.savefig(f"plots/trace_analisis/wait_pods({num}-{num+conj_pods}).png")