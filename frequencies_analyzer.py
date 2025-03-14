#!/usr/bin/env python3

# Author: Richard Lopez Corbalan
# GitHub: github.com/richardloopez
# Citation: If you use this code, please cite Lopez-Corbalan, R.

import os
import glob
import csv

def process_log_files():
    frequency_results = []
    processed_files = set()

    # Get the current directory
    base_directory = os.getcwd()
    print(f"Current directory: {base_directory}")

    # Open the results file
    with open('frequency_results.csv', 'w', newline='') as result_file:
        csv_writer = csv.writer(result_file)
        csv_writer.writerow(["Filename", "Frequencies", "Negatives?"])

        for file_path in glob.iglob(f"{base_directory}/**/*.log", recursive=True):
            if file_path in processed_files:
                continue

            print(f"Processing file: {file_path}")
            processed_files.add(file_path)

            with open(file_path, "r") as log:
                lines = log.readlines()

                patterns = ["Diagonal vibrational", None, "Harmonic", None, None, None, None, None, "Frequencies --"]
                pattern_index = 0
                low_freq_line = None
                frequencies = []

                # Search for "Low frequencies" from the end of the file
                for line_num, line in enumerate(reversed(lines)):
                    if "Low frequencies" in line:
                        print(f"Found 'Low frequencies' on line {len(lines) - line_num}: {line.strip()}")
                        low_freq_line = len(lines) - line_num
                        break

                if low_freq_line is not None:
                    for line in lines[low_freq_line:]:
                        if patterns[pattern_index] is None:
                            pattern_index += 1
                            continue
                        elif patterns[pattern_index] in line:
                            print(f"Pattern found: {patterns[pattern_index]} in line: {line.strip()}")
                            pattern_index += 1
                            if pattern_index == len(patterns):
                                break
                        else:
                            print(f"'{patterns[pattern_index]}' not found in line: '{line.strip()}'")

                    if "Frequencies --" in line:
                        frequency_data = line.split("Frequencies --")[1].strip()
                        frequencies = frequency_data.split()

                        first_frequency = float(frequencies[0]) if frequencies else 0.0
                        negatives = "YES" if first_frequency < 0 else "NO"

                        filename = os.path.basename(file_path)
                        csv_writer.writerow([filename, frequency_data, negatives])
                        print(f"Frequency found in file {filename}: {frequency_data} -> Negatives? {negatives}")
                        frequency_results.append(f"Frequency found in file {filename}")

    return frequency_results

if __name__ == "__main__":
    results = process_log_files()

    if results:
        print("Frequencies found:", results)
    else:
        print("No complete sequence found.")
