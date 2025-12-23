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

    with open("objects/10nodes.yaml", "r") as archivo:
        SchedulingDuration1 = yaml.safe_load(archivo)

    with open("objects/100nodes.yaml", "r") as archivo:
        SchedulingDuration2 = yaml.safe_load(archivo)

    SchedulingDuration1.sort()
    SchedulingDuration2.sort()

    y_1 = np.linspace(0, 1, len(SchedulingDuration1))
    y_2 = np.linspace(0, 1, len(SchedulingDuration2))

    plt.figure(figsize=(10, 6))

    # Dibujar las líneas de la CDF (usando drawstyle='steps-post' para que sea escalonado)
    plt.step(SchedulingDuration1, y_1, label='10 nodos', where='post', linewidth=2, linestyle='-')
    plt.step(SchedulingDuration2, y_2, label='100 nodos', where='post', linewidth=2, color='orange', linestyle='--')

    # Personalización estética (Sin líneas que crucen las barras/curvas)
    plt.title('CDF: Comparativa de Tiempos de scheduling con clusters de diferentes tamaños', fontsize=14)
    plt.xlabel('Tiempo (milisegundos)', fontsize=12)
    plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

    # Mostrar el 50% (mediana)
    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    plt.text(max(SchedulingDuration2)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

    plt.legend()
    plt.tight_layout()
    plt.savefig("plots/scheduling_times_cluster_sizes.png")

def theory_real_durations():

    with open(THEORY_DURATION_PODS_PATH, "r") as archivo:
            theoryDurationPods = yaml.safe_load(archivo)

    with open(REAL_DURATION_PODS_PATH, "r") as archivo:
            realDurationPods = yaml.safe_load(archivo)

    theoryDurationPods.sort()
    realDurationPods.sort()

    y_teorica = np.linspace(0, 1, len(theoryDurationPods))
    y_real = np.linspace(0, 1, len(realDurationPods))
    
    plt.figure(figsize=(10, 6))

    # Dibujar las líneas de la CDF (usando drawstyle='steps-post' para que sea escalonado)
    plt.step(theoryDurationPods, y_teorica, label='Tiempo Teórico', where='post', linewidth=2, linestyle='-')
    plt.step(realDurationPods, y_real, label='Tiempo Real', where='post', linewidth=2, color='orange', linestyle='--')

    # Personalización estética (Sin líneas que crucen las barras/curvas)
    plt.title('CDF: Comparativa de Tiempos Teóricos vs Reales', fontsize=14)
    plt.xlabel('Tiempo de Ejecución (segundos)', fontsize=12)
    plt.ylabel('Probabilidad Acumulada (F(x))', fontsize=12)

    # Mostrar el 50% (mediana)
    plt.axhline(0.5, color='gray', linestyle='--', alpha=0.3)
    plt.text(max(realDurationPods)*0.05, 0.52, 'Mediana (50%)', color='gray', fontsize=10)

    plt.legend()
    plt.tight_layout()
    plt.savefig("plots/MPS/duration_pods.png")

def utilization():

    with open(GPU_OCCUPATION_PATH, "r") as archivo:
            gpuOccupation = yaml.safe_load(archivo)
    with open(GPU_UTILIZATION_PATH, "r") as archivo:
            gpuUtilization = np.array(yaml.safe_load(archivo))
    with open(GPU_ALLOCATED_PATH, "r") as archivo:
            gpuAllocated = np.array(yaml.safe_load(archivo))
    with open(GPU_UTILIZATION_FP32_PATH, "r") as archivo:
            gpuUtilizationFp32 = np.array(yaml.safe_load(archivo))
    with open(GPU_ALLOCATED_FP32_PATH, "r") as archivo:
            gpuAllocatedFp32 = np.array(yaml.safe_load(archivo))
    with open(GPU_UTILIZATION_MEM_PATH, "r") as archivo:
            gpuUtilizationMem = np.array(yaml.safe_load(archivo))
    with open(GPU_ALLOCATED_MEM_PATH, "r") as archivo:
            gpuAllocatedMem = np.array(yaml.safe_load(archivo))
    with open(TIMELINE, "r") as archivo:
            timeline = yaml.safe_load(archivo)

    gpuFragmented = gpuAllocated - gpuUtilization
    fp32Fragmented = gpuAllocatedFp32 - gpuUtilizationFp32
    memFragmented = gpuAllocatedMem - gpuUtilizationMem

    plt.figure(figsize=(10, 6))
    plt.plot(timeline, gpuOccupation, label='Ocupación', color='blue', linestyle='-')
    plt.plot(timeline, gpuUtilization, label='Utilización', color='red', linestyle='--')
    plt.plot(timeline, gpuAllocated, label='Asignación', color='green', linestyle='-.')
    plt.plot(timeline, gpuFragmented, label='Fragmentación', color='orange', linestyle=':')
    plt.ylim(0, 100)

    plt.title('Uso de recursos GPU', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de recursos', fontsize=12)
    plt.legend()
    plt.savefig("plots/MPS/general_resources.png")


    plt.figure(figsize=(10, 6))
    plt.plot(timeline, gpuUtilizationFp32, label='Utilización fp32', color='darkred', linestyle=':')
    plt.plot(timeline, gpuUtilizationMem, label='Utilización mem', color='darkgreen', linestyle='--')
    plt.plot(timeline, gpuAllocatedFp32, label='Asignación fp32', color='lightcoral', linestyle='-.')
    plt.plot(timeline, gpuAllocatedMem, label='Asignación mem', color='lightgreen', linestyle='-')
    plt.ylim(0, 100)

    plt.title('Uso de recursos GPU (fp32 y memória)', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de recursos', fontsize=12)
    plt.legend()
    plt.savefig("plots/MPS/resources_fp32_mem.png")

    plt.figure(figsize=(10, 6))
    plt.plot(timeline, fp32Fragmented, label='Fragmentación fp32', color='darkred', linestyle=':')
    plt.plot(timeline, memFragmented, label='Fragmentación mem', color='darkgreen', linestyle='--')
    plt.ylim(0, 100)

    plt.title('Fragmentación de fp32 y memória GPU', fontsize=14)
    plt.xlabel('Tiempo transcurrido (segundos)', fontsize=12)
    plt.ylabel('Porcentaje de fragmentación', fontsize=12)
    plt.legend()
    plt.savefig("plots/MPS/fragmentation_fp32_mem.png")


if __name__ == "__main__":
    load_dotenv()

    THEORY_DURATION_PODS_PATH=os.getenv('THEORY_DURATION_PODS_PATH')
    REAL_DURATION_PODS_PATH=os.getenv('REAL_DURATION_PODS_PATH')
    GPU_OCCUPATION_PATH=os.getenv('GPU_OCCUPATION_PATH')
    GPU_UTILIZATION_PATH=os.getenv('GPU_UTILIZATION_PATH')
    GPU_ALLOCATED_PATH=os.getenv('GPU_ALLOCATED_PATH')
    GPU_UTILIZATION_FP32_PATH=os.getenv('GPU_UTILIZATION_FP32_PATH')
    GPU_ALLOCATED_FP32_PATH=os.getenv('GPU_ALLOCATED_FP32_PATH')
    GPU_UTILIZATION_MEM_PATH=os.getenv('GPU_UTILIZATION_MEM_PATH')
    GPU_ALLOCATED_MEM_PATH=os.getenv('GPU_ALLOCATED_MEM_PATH')
    TIMELINE=os.getenv('TIMELINE')

    # workload_duration_policies()
    # clusters_sizes()
    theory_real_durations()
    utilization()