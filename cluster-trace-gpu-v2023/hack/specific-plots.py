import matplotlib.pyplot as plt

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