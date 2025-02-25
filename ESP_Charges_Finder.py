#!/usr/bin/env python3

import os
import csv
import statistics

def search_esp_charges(folder, base_dir):
    """
    Busca 'ESP charges:' desde el principio del archivo .log y extrae las siguientes 73 líneas.
    
    Args:
    folder (str): La carpeta donde buscar
    base_dir (str): El directorio base desde donde se lanzó el script
    
    Returns:
    dict: Un diccionario con la ruta relativa del archivo como clave y las cargas como valor
    """
    print(f"Buscando en: {folder}")
    os.chdir(folder)
    
    log_files = [f for f in os.listdir() if f.endswith(".log")]
    results = {}
    
    for log_file in log_files:
        try:
            relative_path = os.path.relpath(os.path.join(folder, log_file), base_dir)
            
            with open(log_file, "r") as file:
                lines = file.readlines()
                esp_index = None
                
                for i, line in enumerate(lines):
                    if "ESP charges:" in line:
                        esp_index = i
                        break
                
                if esp_index is not None:
                    charges = lines[esp_index + 1:esp_index + 74]
                    results[relative_path] = []
                    for line in charges:
                        parts = line.split()
                        if len(parts) >= 3:
                            results[relative_path].append(float(parts[2]))
                        else:
                            results[relative_path].append(0.0)  # Usar 0.0 para cálculos numéricos
        except Exception as e:
            print(f"Error al procesar {log_file}: {str(e)}")
    
    os.chdir(base_dir)
    return results

def explore_directory(base_folder, max_depth):
    """
    Explora directorios recursivamente hasta una profundidad especificada.
    
    Args:
    base_folder (str): La carpeta inicial para la exploración
    max_depth (int): La profundidad máxima para explorar
    
    Returns:
    dict: Un diccionario con todos los resultados
    """
    all_results = {}
    
    def explore(current_folder, current_depth):
        if current_depth > max_depth:
            return
        
        for folder in sorted(os.listdir(current_folder)):
            folder_path = os.path.join(current_folder, folder)
            
            if os.path.isdir(folder_path):
                print(f"Explorando: {folder_path}")
                results = search_esp_charges(folder_path, base_folder)
                all_results.update(results)
                explore(folder_path, current_depth + 1)
    
    explore(base_folder, 0)
    return all_results

# Obtener entradas del usuario
depth_degree = int(input("¿Cuál es el grado de profundidad de las subcarpetas? [1 - infinito) [carpeta que contiene este código = 0] [0 está permitido] : "))

# Iniciar la exploración desde el directorio de trabajo actual
base_dir = os.getcwd()
all_results = explore_directory(base_dir, depth_degree)

# Calcular media y desviación estándar
means = []
std_devs = []
for charges in zip(*all_results.values()):
    charges = [c for c in charges if c != 0.0]  # Excluir valores 0.0 para cálculos
    if charges:
        means.append(statistics.mean(charges))
        std_devs.append(statistics.stdev(charges) if len(charges) > 1 else 0.0)
    else:
        means.append(0.0)
        std_devs.append(0.0)

# Escribir resultados en un archivo CSV
with open(os.path.join(base_dir, "ESP_Charges.csv"), "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    # Escribir encabezados
    headers = ["Atom Number"] + list(all_results.keys()) + ["Mean", "Std Dev"]
    writer.writerow(headers)
    
    # Escribir datos
    for i in range(73):
        row = [i+1] + [results[i] if i < len(results) else '' for results in all_results.values()]
        row.append(means[i])
        row.append(std_devs[i])
        writer.writerow(row)

print("Los resultados se han escrito en ESP_Charges.csv en el directorio base.")
