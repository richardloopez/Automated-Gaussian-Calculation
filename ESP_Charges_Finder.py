#!/usr/bin/env python3

# Author: Richard Lopez Corbalan
# GitHub: github.com/richardloopez
# Citation: If you use this code, please cite Lopez-Corbalan, R.

import os
import csv
import statistics

def search_esp_charges(folder, base_dir):
    """
    Searches for 'ESP charges:' from the beginning of the .log file and extracts the following 73 lines. (one more than the desired atoms is needed)
    
    Args:
    folder (str): The folder to search in
    base_dir (str): The base directory from where the script was launched
    
    Returns:
    dict: A dictionary with the relative path of the file as key and the charges as value
    """
    print(f"Searching in: {folder}")
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
                            results[relative_path].append(0.0)  # Use 0.0 for numerical calculations
        except Exception as e:
            print(f"Error processing {log_file}: {str(e)}")
    
    os.chdir(base_dir)
    return results

def explore_directory(base_folder, max_depth):
    """
    Explores directories recursively up to a specified depth.
    
    Args:
    base_folder (str): The initial folder for exploration
    max_depth (int): The maximum depth to explore
    
    Returns:
    dict: A dictionary with all the results
    """
    all_results = {}
    
    def explore(current_folder, current_depth):
        if current_depth > max_depth:
            return
        
        for folder in sorted(os.listdir(current_folder)):
            folder_path = os.path.join(current_folder, folder)
            
            if os.path.isdir(folder_path):
                print(f"Exploring: {folder_path}")
                results = search_esp_charges(folder_path, base_folder)
                all_results.update(results)
                explore(folder_path, current_depth + 1)
    
    explore(base_folder, 0)
    return all_results

# Get user input
depth_degree = int(input("What is the depth degree of the subfolders? [1 - infinity) [folder containing this code = 0] [0 is allowed] : "))

# Start exploration from the current working directory
base_dir = os.getcwd()
all_results = explore_directory(base_dir, depth_degree)

# Calculate mean and standard deviation
means = []
std_devs = []
for charges in zip(*all_results.values()):
    charges = [c for c in charges if c != 0.0]  # Exclude 0.0 values for calculations
    if charges:
        means.append(statistics.mean(charges))
        std_devs.append(statistics.stdev(charges) if len(charges) > 1 else 0.0)
    else:
        means.append(0.0)
        std_devs.append(0.0)

# Write results to a CSV file
with open(os.path.join(base_dir, "ESP_Charges.csv"), "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    # Write headers
    headers = ["Atom Number"] + list(all_results.keys()) + ["Mean", "Std Dev"]
    writer.writerow(headers)
    
    # Write data     ########ATOM RANGE
    for i in range(73):
        row = [i+1] + [results[i] if i < len(results) else '' for results in all_results.values()]
        row.append(means[i])
        row.append(std_devs[i])
        writer.writerow(row)

print("The results have been written to ESP_Charges.csv in the base directory.")
