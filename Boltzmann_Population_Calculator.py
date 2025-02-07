#!/usr/bin/env python3

# Author: Richard Lopez Corbalan
# GitHub: github.com/richardloopez
# Citation: If you use this code, please cite Lopez-Corbalan, R.

import math
import readlines

# Constants
R = 0.008314  # Gas constant in kJ/(mol·K)
T = 298.15  # Temperature in Kelvin (25°C)
HARTREE_TO_KJ_MOL = 2625.5  # Conversion factor from Hartree to kJ/mol

def calculate_boltzmann_population(energies, temperature):
    """
    Calculate the Boltzmann population distribution for a set of energies.

    Args:
        energies (dict): A dictionary of molecule names and their energies in Hartree.
        temperature (float): The temperature in Kelvin.

    Returns:
        dict: A dictionary of molecule names and their relative populations.
    """
    min_energy = min(energies.values())
    relative_energies = {k: (v - min_energy) * HARTREE_TO_KJ_MOL for k, v in energies.items()}
    partition_function = sum(math.exp(-e / (R * temperature)) for e in relative_energies.values())
    populations = {k: math.exp(-e / (R * temperature)) / partition_function for k, e in relative_energies.items()}
    return populations

def read_energy_file(filename):
    """
    Read energies from a file.

    Args:
        filename (str): The name of the file containing molecule names and energies.

    Returns:
        dict: A dictionary of molecule names and their energies.
    """
    energies = {}
    with open(filename, 'r') as file:
        for line in file:
            name, energy = line.strip().split(',')
            energies[name] = float(energy)
    return energies

def main():
    """
    Main function to calculate and display Boltzmann populations.
    """
    filename = input("Enter the name of the file containing the energies: ")
    energies = read_energy_file(filename)
    populations = calculate_boltzmann_population(energies, T)

    print("Molecule\tEnergy (Hartree)\tRelative Population (%)")
    for name, pop in sorted(populations.items(), key=lambda x: x[1], reverse=True):
        print(f"{name}\t{energies[name]:.6f}\t\t{pop*100:.2f}")

if __name__ == "__main__":
    main()

