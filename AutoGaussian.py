#!/usr/bin/env python3

# Author: Richard Lopez Corbalan
# GitHub: github.com/richardloopez
# Citation: If you use this code, please cite Lopez-Corbalan, R

import os
import time
import glob
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

#########################################################################################################################################################################################
# User configuration
memory = "16GB"   
num_processors = "16"
steps_to_execute = [1, 2, 3, 4, 5, 6]
max_concurrent_molecules = 35  # Reducir para evitar problemas de concurrencia

# Default charge and multiplicity
default_charge = "2"
default_multiplicity = "1"

# Specific commands for each step
step_commands = {
    1: "",
    2: "",
    3: "",
    4: "",
    5: "#p PBE1PBE/6-31+G(d) TD=(Read,NStates=1) SCRF=(Solvent=Water, CorrectedLR, NonEquilibrium=Save) Geom=Check Guess=Read NoSymm",
    6: "#p PBE1PBE/6-31+G(d) SCRF=(Solvent=Water, NonEquilibrium=Read) Geom=Check Guess=Read NoSymm",
}
#########################################################################################################################################################################################

lock = threading.Lock() # Inicializa el Lock

def wait_for_log_completion(log_file):
    while True:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read()
                if "Normal termination" in content:
                    print(f"{log_file} completed successfully.")
                    return True
                elif "Lnk1e" in content:
                    print(f"Error detected in {log_file}. Stopping execution.")
                    return False
        
        print(f"Waiting for {log_file} to complete...")
        time.sleep(60)  # Increased wait time to reduce log spam

def create_cmxyz(input_path, base_folder):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    os.makedirs(os.path.join(base_folder, "bases"), exist_ok=True)
    cmxyz_path = os.path.join(base_folder, "bases", f"{base_name}.cmxyz")
    
    with lock: # Adquiere el Lock para proteger el acceso a los archivos
        if input_path.endswith(".chk"):
            chk_path = os.path.join(base_folder, "bases", f"{base_name}.chk")
            shutil.copy(input_path, chk_path)
            with open(cmxyz_path, 'w') as f:
                f.write(f"{default_charge} {default_multiplicity}\n")
            return cmxyz_path, None
        
        with open(input_path, 'r') as f:
            lines = f.readlines()
        
        if input_path.endswith(".xyz"):
            geometry = ''.join(lines[2:])
            local_charge = default_charge
            local_multiplicity = default_multiplicity
        elif input_path.endswith(".com"):
            local_charge, local_multiplicity = lines[7].split()
            geometry = ''.join(lines[8:])
        else:
            raise ValueError("Unsupported file format. Use .xyz, .com, or .chk")
        
        with open(cmxyz_path, 'w') as f:
            f.write(f"{local_charge} {local_multiplicity}\n")
            if not input_path.endswith(".chk"):
                f.write(geometry)
            f.write("\n") # Libera el Lock
    return cmxyz_path, geometry

def generate_com(com_path, charge, multiplicity, memory, num_processors, step, commands, molecule_name, geometry=None):
    with open(com_path, 'w') as f:
        f.write(f"%mem={memory}\n")
        f.write(f"%nprocshared={num_processors}\n")
        f.write(f"%chk=step{step}.chk\n")
        f.write(f"{commands}\n")
        f.write("\n")
        f.write(f"{molecule_name} Step {step}\n")
        f.write("\n")
        f.write(f"{charge} {multiplicity}\n")
        if geometry:
            f.write(geometry)
        f.write("\n")

def launch_gaussian(com_file):
    directory = os.path.dirname(com_file)
    file_name = os.path.basename(com_file)
    log_file = os.path.join(directory, file_name.replace(".com", ".log"))
    original_dir = os.getcwd()  # Guarda el directorio original

    print(f"Launching Gaussian for: {com_file}")
    print(f"Expected log file path: {log_file}")

    try:
        os.chdir(directory)  # Cambia al directorio del .com
        result = subprocess.run(f"launch_g16 {file_name}", shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)  # Imprime la salida estandar
        print(result.stderr)  # Imprime la salida de error
        os.chdir(original_dir)  # Regresa al directorio original
        return wait_for_log_completion(log_file)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Gaussian: {e}")
        print(e.stderr)  # Imprime el error de Gaussian
        os.chdir(original_dir)  # Asegura regresar al directorio original en caso de error
        return False

def execute_step(base_folder, step, commands, cmxyz_path, is_first_step, geometry):
    base_name = os.path.basename(base_folder)
    step_folder = os.path.join(base_folder, f"step_{step}")
    os.makedirs(step_folder, exist_ok=True)
    
    current_com = os.path.join(step_folder, f"step{step}.com")
    log_file = os.path.join(step_folder, f"step{step}.log")
    charge, multiplicity = default_charge, default_multiplicity
    
    if os.path.exists(cmxyz_path):
        with open(cmxyz_path, 'r') as f:
            charge, multiplicity = f.readline().split()
    
    if is_first_step:
        chk_source = os.path.join(base_folder, "bases", f"{base_name}.chk")
    else:
        previous_step = steps_to_execute[steps_to_execute.index(step) - 1]
        chk_source = os.path.join(base_folder, f"step_{previous_step}", f"step{previous_step}.chk")
    
    chk_destination = os.path.join(step_folder, f"step{step}.chk")

    # Validacion de la existencia del archivo .chk
    if not os.path.exists(chk_source) and not is_first_step:
        print(f"Error: Checkpoint file not found: {chk_source}")
        return False
    
    with lock:  #Protege la copia del archivo
        if os.path.exists(chk_source):
            shutil.copy(chk_source, chk_destination)
    
    generate_com(current_com, charge, multiplicity, memory, num_processors, step, commands, base_name, geometry if is_first_step else None)
    return launch_gaussian(current_com)

def process_file(input_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return False
    
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    base_folder = os.path.join(os.getcwd(), base_name)
    os.makedirs(base_folder, exist_ok=True)
    cmxyz_path, geometry = create_cmxyz(input_path, base_folder)
    
    for i, step in enumerate(steps_to_execute):
        success = execute_step(base_folder, step, step_commands.get(step, ""), cmxyz_path, is_first_step=(i == 0), geometry=geometry)
        if not success:
            print(f"Error in step {step} for {input_path}. Stopping execution for this molecule.")
            return False
    
    print(f"All steps completed for: {input_path}")
    return True

def main():
    input_files = glob.glob("*.chk")  # Solo busca archivos .chk
    if not input_files:
        print("No valid input files found.")
        return
    
    print(f"Found input files: {input_files}") 
    
    with ThreadPoolExecutor(max_workers=max_concurrent_molecules) as executor:
        future_to_file = {executor.submit(process_file, input_file): input_file for input_file in input_files}
        
        for future in as_completed(future_to_file):
            input_file = future_to_file[future]
            try:
                success = future.result()
                if success:
                    print(f"Successfully processed: {input_file}")
                else:
                    print(f"Failed to process: {input_file}")
            except Exception as exc:
                print(f"{input_file} generated an exception: {exc}")

    print("All calculations are completed.")

if __name__ == "__main__":
    main()
