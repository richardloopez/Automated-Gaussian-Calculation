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

#########################################################################################################################################################################################
# User configuration
memory = "16GB"   
num_processors = "16"
steps_to_execute = [1, 2, 3, 4, 5, 6]
max_concurrent_molecules = 10

# Default charge and multiplicity
default_charge = "0"
default_multiplicity = "1"

# Specific commands for each step
step_commands = {
    1: "# Opt Freq B3LYP/6-31+G(d,p) SCRF=(Solvent=Ethanol) Geom=Connectivity",
    2: "# B3LYP/6-31+G(d,p) TD=NStates=6 SCRF=(Solvent=Ethanol) Geom=Check Guess=Read",
    3: "# B3LYP/6-31+G(d,p) TD=(NStates=6,Root=1) Geom=Check Guess=Read SCRF=(Solvent=Ethanol,CorrectedLR)",
    4: "# B3LYP/6-31+G(d,p) TD=(NStates=6,Root=1) SCRF=(Solvent=Ethanol) Geom=Check Guess=Read Opt=CalcFC Freq NoSymm",
    5: "# B3LYP/6-31+G(d,p) TD=(Read,NStates=6,Root=1) Geom=Check Guess=Read SCRF=(Solvent=Ethanol,CorrectedLR,NonEquilibrium=Save) NoSymm",
    6: "# B3LYP/6-31+G(d,p) SCRF=(Solvent=Ethanol,NonEquilibrium=Read) Geom=Check Guess=Read NoSymm",
}
#########################################################################################################################################################################################

def wait_for_log_completion(log_file):
    while True:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.read()
                if "Normal termination" in content:
                    print(f"{log_file} completed successfully.")
                    return True
                elif "Leave Link" in content:
                    print(f"Error detected in {log_file}. Stopping execution.")
                    return False
        
        print(f"Waiting for {log_file} to complete...")
        time.sleep(60)  # Increased wait time to reduce log spam

def create_cmxyz(input_path, base_folder):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    os.makedirs(os.path.join(base_folder, "bases"), exist_ok=True)
    cmxyz_path = os.path.join(base_folder, "bases", f"{base_name}.cmxyz")
    
    if input_path.endswith(".chk"):
        shutil.copy(input_path, os.path.join(base_folder, "bases", f"{base_name}.chk"))
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
        f.write("\n")
    
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

    print(f"Launching Gaussian for: {com_file}")
    print(f"Expected log file path: {log_file}")
    original_dir = os.getcwd()

    try:
        os.chdir(directory)
        subprocess.run(f"launch_g16 {file_name}", shell=True, check=True)
        os.chdir(original_dir)
        time.sleep(2)  
        return wait_for_log_completion(log_file)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Gaussian: {e}")
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
    input_files = glob.glob("*.xyz") + glob.glob("*.com") + glob.glob("*.chk")
    if not input_files:
        print("No valid input files found.")
        return
    
    print(f"Found input files: {input_files}") 
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_file = {}
        for input_file in input_files:
            future = executor.submit(process_file, input_file)
            future_to_file[future] = input_file
            time.sleep(5)  # Espera 5 segundos antes de lanzar el siguiente trabajo
        
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

