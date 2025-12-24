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

    print(f"Pods eliminados: {len(podDurations) - len(podDurations_filt)}")

    ventana = 500
    cont = 0
    n_bloques = len(creationTime) // 500
    datos_remodelados = creationTime[:n_bloques*500].reshape(-1, 500)

    # 2. Sumamos cada fila (cada bloque de 500)
    cargas_por_bloque = np.sum(datos_remodelados, axis=1)

    for num in cargas_por_bloque:
        print(f"({cont*ventana}-{(cont+1)*ventana}): {num}")
        cont += 1


    for num in range(0, len(deletionTime), 500):
        plt.figure(figsize=(10, 6))
        plt.plot(range(len(podDurations_filt[num:num+500])), podDurations_filt[num:num+500], label='Duración', color='darkred', linestyle=':')

        plt.title('Duración de pods', fontsize=14)
        plt.xlabel('Pods', fontsize=12)
        plt.ylabel('Tiempo', fontsize=12)
        plt.legend()
        plt.savefig(f"plots/trace_analisis/pod_traffic({num}-{num+500}).png")

        plt.figure(figsize=(10, 6))
        plt.plot(range(len(creationTime[num:num+500])), creationTime[num:num+500], label='Espera de creación', color='darkred', linestyle=':')

        plt.title('Tiempos entre creación', fontsize=14)
        plt.xlabel('Pods', fontsize=12)
        plt.ylabel('Tiempo', fontsize=12)
        plt.legend()
        plt.savefig(f"plots/trace_analisis/wait_pods({num}-{num+500}).png")