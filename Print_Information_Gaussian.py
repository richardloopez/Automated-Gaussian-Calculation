#!/usr/bin/env python3

# Import necessary modules
import os
import shutil
import subprocess
import readline

# Author: Richard Lopez Corbalan
# GitHub: github.com/richardloopez
# Citation: If you use this code, please cite Lopez-Corbalan, R

def search_string(folder, search_text, search_from_end):
    """
    Search for a specific text in log files within a given folder.
    
    Args:
    folder (str): The folder to search in
    search_text (str): The text to search for
    search_from_end (bool): Whether to search from the end of the file
    
    Returns:
    list: A list of tuples containing the log file name and the found value (or None if not found)
    """
    print(f"Searching in: {folder}")
    os.chdir(folder)
    
    # Get all .log files in the current directory
    log_files = [f for f in os.listdir() if f.endswith(".log")]
    
    results = []
    if not log_files:
        print(f"    {folder} does not contain log files")
    else:
        for log_file in log_files:
            found_value = None
            with open(log_file, "r") as log_file_handle:
                lines = log_file_handle.readlines()
                if search_from_end:
                    lines = reversed(lines)
                
                for line in lines:
                    if search_text in line:
                        found_value = line.split(search_text)[1].strip()
                        break
            
            results.append((log_file, found_value))

    os.chdir("../../..")
    return results

# Print instructions and warnings
print("Warning: This script processes subdirectories to apply the Seminario method.")
print("You can have as many folders and subfolder as you want.") 
print("\nHave in mind: in the subfolder you want to perform the Seminario method you need to have:"
      "\n         -Only one .chk file"
      "\n         -Only one .log file"
      "\n         *Presence of other files is not a problem"
      "\n         *This code has to be launched in the folder [0] (along with the other folders, not subfolders)")

# Get user inputs
depth_degree = int(input("What is the depth degree of the subfolders? [1 - infinite) [folder containing this code = 0] [0 is allowed] : "))
search_text = input("What text would you like to search for in the .log files? : ")
search_direction = input("Do you want to search from the beginning or from the end of the file? (Type 'beginning' or 'end'): ").strip().lower()

search_from_end = True if search_direction == 'end' else False

print("Exploring directories...")
visited_dirs = set()
all_results = []

def explore_directory(base_folder, current_depth, max_depth):
    """
    Recursively explore directories up to a specified depth.
    
    Args:
    base_folder (str): The starting folder for exploration
    current_depth (int): The current depth of exploration
    max_depth (int): The maximum depth to explore
    """
    if current_depth > max_depth:
        return
    
    for folder in sorted(os.listdir(base_folder)):
        folder_path = os.path.join(base_folder, folder)
        
        if os.path.isdir(folder_path) and folder_path not in visited_dirs:
            visited_dirs.add(folder_path)
            print(f"Exploring: {folder_path}")
            results = search_string(folder_path, search_text, search_from_end)
            all_results.extend(results)
            explore_directory(folder_path, current_depth + 1, max_depth)

# Start the exploration from the current working directory
base_dir = os.getcwd()
explore_directory(base_dir, 0, depth_degree)

# Write results to a file
with open(os.path.join(base_dir, "Search_Results.txt"), "w") as output_file:
    for log_file, found_value in all_results:
        if found_value:
            output_file.write(f"{log_file},{found_value}\n")
        else:
            output_file.write(f"{log_file} , {search_text} not found\n")

print("Results have been written to Search_Results.txt in the base directory.")
