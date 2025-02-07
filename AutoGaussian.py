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

# Set the memory allocation for Gaussian calculations
memory = "16GB"

# Set the number of processors to use for each calculation
num_processors = "16"

# Define which steps of the calculation process to execute
steps_to_execute = [1, 2, 3, 4, 5, 6]

# Set the maximum number of molecules to process concurrently
max_concurrent_molecules = 2

# Default charge and multiplicity for molecules
default_charge = "0"
default_multiplicity = "1"

# Specific Gaussian commands for each step of the calculation process
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
    """
    Monitor the Gaussian log file for completion or errors.
    
    Args:
    log_file (str): Path to the Gaussian log file.
    
    Returns:
    bool: True if the calculation completed successfully, False if an error was detected.
    """
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
        time.sleep(60)  # Wait for 60 seconds before checking again

def create_cmxyz(input_path, base_folder):
    """
    Create a .cmxyz file from various input formats (.chk, .xyz, .com).
    
    Args:
    input_path (str): Path to the input file.
    base_folder (str): Base directory for output files.
    
    Returns:
    tuple: Path to the created .cmxyz file and the local charge and multiplicity (if applicable).
    """
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
        raise ValueError("Unsupported file format.")
    
    # Write the .cmxyz file
    with open(cmxyz_path, 'w') as f:
        f.write(f"{local_charge} {local_multiplicity}\n")
        f.write(geometry)
    
    return cmxyz_path, (local_charge, local_multiplicity)

def run_gaussian(input_file, output_file):
    """
    Execute a Gaussian calculation.
    
    Args:
    input_file (str): Path to the Gaussian input file.
    output_file (str): Path to save the Gaussian output file.
    
    Returns:
    int: Return code of the Gaussian process.
    """
    command = f"g16 < {input_file} > {output_file}"
    process = subprocess.Popen(command, shell=True)
    return process.wait()

def process_molecule(molecule_path, base_folder):
    """
    Process a single molecule through all specified calculation steps.
    
    Args:
    molecule_path (str): Path to the molecule input file.
    base_folder (str): Base directory for output files.
    
    Returns:
    bool: True if all steps completed successfully, False otherwise.
    """
    cmxyz_path, charge_mult = create_cmxyz(molecule_path, base_folder)
    base_name = os.path.splitext(os.path.basename(cmxyz_path))[0]
    
    for step in steps_to_execute:
        step_folder = os.path.join(base_folder, f"step{step}")
        os.makedirs(step_folder, exist_ok=True)
        
        input_file = os.path.join(step_folder, f"{base_name}.com")
        chk_file = os.path.join(step_folder, f"{base_name}.chk")
        log_file = os.path.join(step_folder, f"{base_name}.log")
        
        # Create Gaussian input file
        with open(input_file, 'w') as f:
            f.write(f"%Chk={chk_file}\n")
            f.write(f"%Mem={memory}\n")
            f.write(f"%NProcShared={num_processors}\n")
            f.write(f"{step_commands[step]}\n\n")
            f.write(f"Title Card Required\n\n")
            
            if charge_mult:
                f.write(f"{charge_mult[0]} {charge_mult[1]}\n")
            
            if step == 1:
                with open(cmxyz_path, 'r') as cmxyz:
                    f.write(cmxyz.read())
            else:
                f.write("\n")
        
        # Run Gaussian calculation
        run_gaussian(input_file, log_file)
        
        # Wait for log file completion and check for errors
        if not wait_for_log_completion(log_file):
            return False
    
    return True

def main():
    """
    Main function to process all molecules in the input folder.
    """
    input_folder = "input"
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    
    input_files = glob.glob(os.path.join(input_folder, "*.*"))
    
    with ThreadPoolExecutor(max_workers=max_concurrent_molecules) as executor:
        futures = []
        for input_file in input_files:
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            molecule_folder = os.path.join(output_folder, base_name)
            os.makedirs(molecule_folder, exist_ok=True)
            futures.append(executor.submit(process_molecule, input_file, molecule_folder))
        
        for future in as_completed(futures):
            result = future.result()
            if not result:
                print("Error occurred during molecule processing.")

if __name__ == "__main__":
    main()
