import matplotlib.pyplot as plt
import yaml
import numpy as np
from dotenv import load_dotenv
import os

def workload_duration_policies():
    # Cambiar valores por los reales
    times = {
        'MIG-MPS': 145,
        'MPS-only': 300
    }

    ordered_times = dict(sorted(times.items(), key=lambda item: item[1], reverse=True))
    names = list(ordered_times.keys())
    values = list(ordered_times.values())

    plt.figure(figsize=(10, 6))

    # Usamos un mapa de colores (Colormap) para dar énfasis
    colores = plt.cm.viridis([i/len(values) for i in range(len(values))])

    bars = plt.bar(names, values, color=colores)

    plt.title('Tiempo Total de Ejecución del Workload', fontsize=14, fontweight='bold')
    plt.ylabel('Tiempo (segundos)')
    plt.xticks(rotation=30, ha='right') # Rotar nombres para que no se solapen
    plt.grid(axis='y', linestyle='--', alpha=0.6)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 5, yval, ha='center', va='bottom')

    plt.grid(False)
    plt.tight_layout()
    plt.savefig("plots/total_execution_time.png")

def clusters_sizes():

    with open("objects/100gpu.yaml", "r") as archivo:
        SchedulingDuration1 = yaml.safe_load(archivo)

    with open("objects/250gpu.yaml", "r") as archivo:
        SchedulingDuration2 = yaml.safe_load(archivo)

    with open("objects/500gpu.yaml", "r") as archivo:
        SchedulingDuration3 = yaml.safe_load(archivo)

    with open("objects/750gpu.yaml", "r") as archivo:
            SchedulingDuration4 = yaml.safe_load(archivo)

    with open("objects/1000gpu.yaml", "r") as archivo:
        SchedulingDuration5 = yaml.safe_load(archivo)

    SchedulingDuration1.sort()
    SchedulingDuration2.sort()
    SchedulingDuration3.sort()
    SchedulingDuration4.sort()
    SchedulingDuration5.sort()

    y_1 = np.linspace(0, 1, len(SchedulingDuration1))
    y_2 = np.linspace(0, 1, len(SchedulingDuration2))
    y_3 = np.linspace(0, 1, len(SchedulingDuration3))
    y_4 = np.linspace(0, 1, len(SchedulingDuration4))
    y_5 = np.linspace(0, 1, len(SchedulingDuration5))

    plt.figure(figsize=(10, 6))

    # Dibujar las líneas de la CDF (usando drawstyle='steps-post' para que sea escalonado)
    plt.step(SchedulingDuration1, y_1, label='100 gpu', where='post', linewidth=2, color='red',linestyle='-')
    plt.step(SchedulingDuration2, y_2, label='250 gpu', where='post', linewidth=2, color='orange', linestyle='--')
    plt.step(SchedulingDuration3, y_3, label='500 gpu', where='post', linewidth=2, color='blue', linestyle=':')
    plt.step(SchedulingDuration4, y_4, label='750 gpu', where='post', linewidth=2, color='green', linestyle='-.')
    plt.step(SchedulingDuration5, y_5, label='1000 gpu', where='post', linewidth=2, color='black', linestyle=':')

    # Personalización estética (Sin líneas que crucen las barras/curvas)
    plt.title('CDF: Comparativa de Tiempos de scheduling con clusters de diferentes tamaños', fontsize=14)
    plt.xlabel('Tiempo (milisegundos)', fontsize=12)
    plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

    # Mostrar el 50% (mediana)
    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    plt.text(max(SchedulingDuration5)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

    plt.legend()
    plt.tight_layout()
    plt.savefig("plots/scheduling_times_cluster_sizes.png")

def theory_real_durations():

    with open(THEORY_DURATION_PODS_PATH, "r") as archivo:
            theoryDurationPods = yaml.safe_load(archivo)
    with open(REAL_DURATION_PODS_PATH_MIG_MPS, "r") as archivo:
            realDurationPodsMIG = yaml.safe_load(archivo)
    with open(REAL_DURATION_PODS_PATH_MPS, "r") as archivo:
            realDurationPodsMPS = yaml.safe_load(archivo)

    theoryDurationPods.sort()
    realDurationPodsMIG.sort()
    realDurationPodsMPS.sort()

    theoryDurationPods = np.array(theoryDurationPods)
    realDurationPodsMIG = np.array(realDurationPodsMIG)
    realDurationPodsMPS = np.array(realDurationPodsMPS)

    q1 = np.percentile(theoryDurationPods, 25)
    q3 = np.percentile(theoryDurationPods, 99)
    iqr = q3 - q1

    # Definimos los límites (típicamente 1.5 veces el IQR)
    limite_superior = q3 + 1.5 * iqr

    # Filtramos: nos quedamos solo con los que NO son outliers
    mask_limpios = theoryDurationPods <= limite_superior
    theoryDurationPods_filt = theoryDurationPods[mask_limpios]
    realDurationPodsMIG_filt = realDurationPodsMIG[mask_limpios]
    realDurationPodsMPS_filt = realDurationPodsMPS[mask_limpios]

    y_teorica = np.linspace(0, 1, len(theoryDurationPods_filt))
    # y_realMIG = np.linspace(0, 1, len(realDurationPodsMIG_filt))
    # y_realMPS = np.linspace(0, 1, len(realDurationPodsMPS_filt))
    
    plt.figure(figsize=(10, 6))
    # Dibujar las líneas de la CDF (usando drawstyle='steps-post' para que sea escalonado)
    plt.step(theoryDurationPods_filt, y_teorica, label='Tiempo Teórico', where='post', linewidth=2, linestyle='-')
    plt.step(realDurationPodsMIG_filt, y_teorica, label='Tiempo Real MIG+MPS', where='post', linewidth=2, color='orange', linestyle='--')

    # Personalización estética (Sin líneas que crucen las barras/curvas)
    plt.title('CDF: Comparativa de Tiempos Teóricos vs Reales (MIG+MPS)', fontsize=14)
    plt.xlabel('Tiempo de Ejecución (segundos)', fontsize=12)
    plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

    # Mostrar el 50% (mediana)
    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    plt.text(max(realDurationPodsMIG_filt)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

    plt.legend()
    plt.tight_layout()
    plt.savefig(DURATION_PODS_MIG_MPS)

    plt.figure(figsize=(10, 6))
    plt.step(theoryDurationPods_filt, y_teorica, label='Tiempo Teórico', where='post', linewidth=2, linestyle='-')
    plt.step(realDurationPodsMPS_filt, y_teorica, label='Tiempo Real MPS', where='post', linewidth=2, color='orange', linestyle='--')

    plt.title('CDF: Comparativa de Tiempos Teóricos vs Reales (MPS)', fontsize=14)
    plt.xlabel('Tiempo de Ejecución (segundos)', fontsize=12)
    plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    plt.text(max(realDurationPodsMPS_filt)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

    plt.legend()
    plt.tight_layout()
    plt.savefig(DURATION_PODS_MPS)

    plt.figure(figsize=(10, 6))
    plt.step(theoryDurationPods_filt, y_teorica, label='Tiempo Teórico', where='post', linewidth=2, linestyle='-')
    plt.step(realDurationPodsMPS_filt, y_teorica, label='Tiempo Real MPS', where='post', linewidth=2, color='orange', linestyle='--')
    plt.step(realDurationPodsMIG_filt, y_teorica, label='Tiempo Real MIG+MPS', where='post', linewidth=2, color='green', linestyle='-.')

    plt.title('CDF: Comparativa de Tiempos Teóricos vs MIG+MPS vs MPS', fontsize=14)
    plt.xlabel('Tiempo de Ejecución (segundos)', fontsize=12)
    plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    plt.text(max(realDurationPodsMPS_filt)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

    plt.legend()
    plt.tight_layout()
    plt.savefig(DURATION_PODS_COMP)

def utilization(gpu_occupation_path, 
                gpu_utilization_path, 
                gpu_allocated_path, 
                gpu_utilization_fp32_path, 
                gpu_allocated_fp32_path, 
                gpu_utilization_mem_path,
                gpu_allocated_mem_path,
                timeline_pods,
                general_resources_path,
                resources_fp32_mem_path,
                fragmentation_fp32_mem_path):

    with open(gpu_occupation_path, "r") as archivo:
            gpuOccupation = yaml.safe_load(archivo)
    with open(gpu_utilization_path, "r") as archivo:
            gpuUtilization = np.array(yaml.safe_load(archivo))
    with open(gpu_allocated_path, "r") as archivo:
            gpuAllocated = np.array(yaml.safe_load(archivo))
    with open(gpu_utilization_fp32_path, "r") as archivo:
            gpuUtilizationFp32 = np.array(yaml.safe_load(archivo))
    with open(gpu_allocated_fp32_path, "r") as archivo:
            gpuAllocatedFp32 = np.array(yaml.safe_load(archivo))
    with open(gpu_utilization_mem_path, "r") as archivo:
            gpuUtilizationMem = np.array(yaml.safe_load(archivo))
    with open(gpu_allocated_mem_path, "r") as archivo:
            gpuAllocatedMem = np.array(yaml.safe_load(archivo))
    with open(timeline_pods, "r") as archivo:
            timeline = yaml.safe_load(archivo)

    gpuFragmented = gpuAllocated - gpuUtilization
    fp32Fragmented = gpuAllocatedFp32 - gpuUtilizationFp32
    memFragmented = gpuAllocatedMem - gpuUtilizationMem

    plt.figure(figsize=(10, 6))
    plt.plot(timeline, gpuOccupation, label='Ocupación', color='blue', linestyle='-')
    plt.plot(timeline, gpuUtilization, label='Utilización', color='red', linestyle='--')
    plt.plot(timeline, gpuAllocated, label='Asignación', color='green', linestyle='-.')
    plt.plot(timeline, gpuFragmented, label='Fragmentación', color='orange', linestyle=':')
    plt.ylim(0, 105)

    plt.title('Uso de recursos GPU', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de recursos', fontsize=12)
    plt.legend()
    plt.savefig(general_resources_path)

    plt.figure(figsize=(10, 6))
    plt.plot(timeline, gpuUtilizationFp32, label='Utilización fp32', color='darkred', linestyle=':')
    plt.plot(timeline, gpuUtilizationMem, label='Utilización mem', color='darkgreen', linestyle='--')
    plt.plot(timeline, gpuAllocatedFp32, label='Asignación fp32', color='lightcoral', linestyle='-.')
    plt.plot(timeline, gpuAllocatedMem, label='Asignación mem', color='lightgreen', linestyle='-')
    plt.ylim(0, 105)

    plt.title('Uso de recursos GPU (fp32 y memoria)', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de recursos', fontsize=12)
    plt.legend()
    plt.savefig(resources_fp32_mem_path)

    plt.figure(figsize=(10, 6))
    plt.plot(timeline, fp32Fragmented, label='Fragmentación fp32', color='darkred', linestyle=':')
    plt.plot(timeline, memFragmented, label='Fragmentación mem', color='darkgreen', linestyle='--')
    plt.ylim(0, 100)

    plt.title('Fragmentación de fp32 y memoria GPU', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de fragmentación', fontsize=12)
    plt.legend()
    plt.savefig(fragmentation_fp32_mem_path)     


def comparation_metrics():

    with open(GPU_UTILIZATION_PATH_MIG_MPS, "r") as archivo:
            gpuUtilizationMIG = np.array(yaml.safe_load(archivo))
    with open(GPU_UTILIZATION_PATH_MPS, "r") as archivo:
            gpuUtilizationMPS = np.array(yaml.safe_load(archivo))
    with open(GPU_ALLOCATED_PATH_MIG_MPS, "r") as archivo:
            gpuAllocatedMIG = np.array(yaml.safe_load(archivo))
    with open(GPU_ALLOCATED_PATH_MPS, "r") as archivo:
            gpuAllocatedMPS = np.array(yaml.safe_load(archivo))
    with open(TIMELINE_MPS, "r") as archivo:
            timelineMPS = yaml.safe_load(archivo)

    gpuFragmentedMIG = gpuAllocatedMIG - gpuUtilizationMIG
    gpuFragmentedMPS = gpuAllocatedMPS - gpuUtilizationMPS

    plt.figure(figsize=(10, 6))
    plt.plot(timelineMPS, gpuUtilizationMIG, label='Utilización MIG+MPS', color='blue', linestyle='-')
    plt.plot(timelineMPS, gpuUtilizationMPS, label='Utilización MPS', color='red', linestyle='--')
    plt.ylim(0, 100)

    plt.title('Utilización de recursos GPU (MPS vs MIG+MPS)', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de recursos', fontsize=12)
    plt.legend()
    plt.savefig(UTILIZATION_COMP)

    plt.figure(figsize=(10, 6))
    plt.plot(timelineMPS, gpuFragmentedMIG, label='Fragmentación MIG+MPS', color='darkred', linestyle=':')
    plt.plot(timelineMPS, gpuFragmentedMPS, label='Fragmentación MPS', color='darkgreen', linestyle='--')
    plt.ylim(0, 100)

    plt.title('Fragmentación de recursos GPU (MPS vs MIG+MPS)', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de recursos', fontsize=12)
    plt.legend()
    plt.savefig(FRAGMENTATION_COMP)

if __name__ == "__main__":
    load_dotenv()

    THEORY_DURATION_PODS_PATH=os.getenv('THEORY_DURATION_PODS_PATH')
    DURATION_PODS_COMP=os.getenv('DURATION_PODS_COMP')
    UTILIZATION_COMP=os.getenv('UTILIZATION_COMP')
    FRAGMENTATION_COMP=os.getenv('FRAGMENTATION_COMP')

    REAL_DURATION_PODS_PATH_MIG_MPS=os.getenv('REAL_DURATION_PODS_PATH_MIG_MPS')
    DURATION_PODS_MIG_MPS=os.getenv('DURATION_PODS_MIG_MPS')
    GPU_OCCUPATION_PATH_MIG_MPS=os.getenv('GPU_OCCUPATION_PATH_MIG_MPS')
    GPU_UTILIZATION_PATH_MIG_MPS=os.getenv('GPU_UTILIZATION_PATH_MIG_MPS')
    GPU_ALLOCATED_PATH_MIG_MPS=os.getenv('GPU_ALLOCATED_PATH_MIG_MPS')
    GPU_UTILIZATION_FP32_PATH_MIG_MPS=os.getenv('GPU_UTILIZATION_FP32_PATH_MIG_MPS')
    GPU_ALLOCATED_FP32_PATH_MIG_MPS=os.getenv('GPU_ALLOCATED_FP32_PATH_MIG_MPS')
    GPU_UTILIZATION_MEM_PATH_MIG_MPS=os.getenv('GPU_UTILIZATION_MEM_PATH_MIG_MPS')
    GPU_ALLOCATED_MEM_PATH_MIG_MPS=os.getenv('GPU_ALLOCATED_MEM_PATH_MIG_MPS')
    TIMELINE_MIG_MPS=os.getenv('TIMELINE_MIG_MPS')
    GENERAL_RESOURCES_MIG_MPS=os.getenv('GENERAL_RESOURCES_MIG_MPS')
    RESOURCES_FP32_MEM_MIG_MPS=os.getenv('RESOURCES_FP32_MEM_MIG_MPS')
    FRAGMENTATION_FP32_MEM_MIG_MPS=os.getenv('FRAGMENTATION_FP32_MEM_MIG_MPS')    

    REAL_DURATION_PODS_PATH_MPS=os.getenv('REAL_DURATION_PODS_PATH_MPS')
    DURATION_PODS_MPS=os.getenv('DURATION_PODS_MPS')
    GPU_OCCUPATION_PATH_MPS=os.getenv('GPU_OCCUPATION_PATH_MPS')
    GPU_UTILIZATION_PATH_MPS=os.getenv('GPU_UTILIZATION_PATH_MPS')
    GPU_ALLOCATED_PATH_MPS=os.getenv('GPU_ALLOCATED_PATH_MPS')
    GPU_UTILIZATION_FP32_PATH_MPS=os.getenv('GPU_UTILIZATION_FP32_PATH_MPS')
    GPU_ALLOCATED_FP32_PATH_MPS=os.getenv('GPU_ALLOCATED_FP32_PATH_MPS')
    GPU_UTILIZATION_MEM_PATH_MPS=os.getenv('GPU_UTILIZATION_MEM_PATH_MPS')
    GPU_ALLOCATED_MEM_PATH_MPS=os.getenv('GPU_ALLOCATED_MEM_PATH_MPS')
    TIMELINE_MPS=os.getenv('TIMELINE_MPS')
    GENERAL_RESOURCES_MPS=os.getenv('GENERAL_RESOURCES_MPS')
    RESOURCES_FP32_MEM_MPS=os.getenv('RESOURCES_FP32_MEM_MPS')
    FRAGMENTATION_FP32_MEM_MPS=os.getenv('FRAGMENTATION_FP32_MEM_MPS')
    
    # workload_duration_policies()
    # clusters_sizes()
    theory_real_durations()
    utilization(GPU_OCCUPATION_PATH_MIG_MPS, 
                GPU_UTILIZATION_PATH_MIG_MPS, 
                GPU_ALLOCATED_PATH_MIG_MPS, 
                GPU_UTILIZATION_FP32_PATH_MIG_MPS, 
                GPU_ALLOCATED_FP32_PATH_MIG_MPS,
                GPU_UTILIZATION_MEM_PATH_MIG_MPS,
                GPU_ALLOCATED_MEM_PATH_MIG_MPS,
                TIMELINE_MIG_MPS,
                GENERAL_RESOURCES_MIG_MPS,
                RESOURCES_FP32_MEM_MIG_MPS,
                FRAGMENTATION_FP32_MEM_MIG_MPS)
    
    utilization(GPU_OCCUPATION_PATH_MPS, 
                GPU_UTILIZATION_PATH_MPS, 
                GPU_ALLOCATED_PATH_MPS, 
                GPU_UTILIZATION_FP32_PATH_MPS, 
                GPU_ALLOCATED_FP32_PATH_MPS,
                GPU_UTILIZATION_MEM_PATH_MPS,
                GPU_ALLOCATED_MEM_PATH_MPS,
                TIMELINE_MPS,
                GENERAL_RESOURCES_MPS,
                RESOURCES_FP32_MEM_MPS,
                FRAGMENTATION_FP32_MEM_MPS)
    
    comparation_metrics()