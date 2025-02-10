#!/usr/bin/env python3

"""
XYZ to PDB Converter

This script extracts molecular geometries from an XYZ file and inserts them into a base PDB file.
Each geometry is saved as a separate PDB file with a numbered suffix.

Usage:
    python multixyz_to_pdb.py input.xyz base.pdb output_prefix

# Author: Richard Lopez Corbalan
# GitHub: github.com/richardloopez
# Citation: If you use this code, please cite Lopez-Corbalan, R
"""
import sys
import os

def read_xyz(file_path):
    """Reads an XYZ file and extracts molecular geometries."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    geometries = []
    i = 0
    while i < len(lines):
        try:
            num_atoms = int(lines[i].strip())
            geom = lines[i+2 : i+2+num_atoms]  # Skip comment line
            geometries.append(geom)
            i += num_atoms + 2
        except ValueError:
            print(f"Warning: Skipping invalid line {i} in {file_path}")
            i += 1
    
    return geometries

def insert_geometry(base_pdb, geometry):
    """Inserts extracted geometry into the base PDB structure."""
    with open(base_pdb, 'r') as f:
        pdb_lines = f.readlines()
    
    atom_lines = [line for line in pdb_lines if line.startswith("ATOM") or line.startswith("HETATM")]
    if len(atom_lines) != len(geometry):
        raise ValueError("Mismatch between PDB atom count and XYZ geometry atom count.")
    
    new_pdb = []
    xyz_coords = [line.split()[1:] for line in geometry]
    
    atom_idx = 0
    for line in pdb_lines:
        if line.startswith("ATOM") or line.startswith("HETATM"):
            parts = list(line)
            x, y, z = xyz_coords[atom_idx]
            parts[30:54] = f"{float(x):8.3f}{float(y):8.3f}{float(z):8.3f}".rjust(24)
            new_pdb.append("".join(parts))
            atom_idx += 1
        else:
            new_pdb.append(line)
    
    return new_pdb

def write_pdb(output_path, pdb_lines):
    """Writes the modified PDB structure to a file."""
    with open(output_path, 'w') as f:
        f.writelines(pdb_lines)

def main():
    if len(sys.argv) != 4:
        print("Usage: python multixyz_to_pdb.py input.xyz base.pdb output_prefix")
        sys.exit(1)
    
    xyz_file = sys.argv[1]
    base_pdb = sys.argv[2]
    output_prefix = sys.argv[3]
    
    if not os.path.isfile(xyz_file) or not os.path.isfile(base_pdb):
        print("Error: One or more input files do not exist.")
        sys.exit(1)
    
    geometries = read_xyz(xyz_file)
    for idx, geometry in enumerate(geometries, start=1):
        try:
            new_pdb = insert_geometry(base_pdb, geometry)
            output_pdb = f"{output_prefix}_{idx}.pdb"
            write_pdb(output_pdb, new_pdb)
            print(f"Generated: {output_pdb}")
        except ValueError as e:
            print(f"Skipping frame {idx} due to error: {e}")

if __name__ == "__main__":
    main()



