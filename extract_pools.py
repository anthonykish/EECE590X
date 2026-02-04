import os
import re
import sys
import shutil

"""
Takes all the pools out of the specified folders and places them in
one place (temp_pools)

For example, "python3 extract_pools.py 8-10 22" takes all the csvs
from sections 8, 9, 10, and 22
"""

destination_directory = "temp_pools"

# Quit if no arguments
if len(sys.argv) <= 1:
    print("Must pass in arguments")
    exit
args = sys.argv[1:]

numbers = []
for arg in args:
    # If there is a dash in the argument, add all the numbers to the list
    # So 8-12 adds 8, 9, 10, 11, and 12 to the list
    dash_index = arg.find("-")
    if dash_index > 0:
        start = int(arg[0:dash_index])
        end = int(arg[dash_index+1:])
        numbers += [str(i) for i in range(start, end+1)]
    # Otherwise just add the number
    else:
        numbers.append(arg)

# Get a list of folders to walk through
base_folders = []
for number in numbers:
    base_folders += [i for i in os.listdir() if os.path.isdir(i) and re.match(rf"^0?{number}_", i)]

# Make a new directory (remove it if it already exists)
if os.path.exists(destination_directory) and os.path.isdir(destination_directory):
    shutil.rmtree(destination_directory)
os.mkdir(destination_directory)

for folder in base_folders:
    # Walk through every folder and copy all PNGs into the destination directory
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith("csv"):
                # Go from the start to the first underscore
                set_num = str(int(folder[0:folder.find("_")]))
                # Go from the first / to the next underscore after that
                q_num = (root.split('\\')[1]).split('_')[0]
                new_name = f"q{set_num}_{q_num}.csv"
                # Example: 16_Synchronous_Circuits\5_dff_advantages\pool.csv
                #           -> q16_5.csv

                source = os.path.join(root, file)
                dest = os.path.join(destination_directory, new_name)

                # Put a _ before .csv if the file already exists
                while os.path.exists(dest):
                    dest = dest[:-4] + "_" + dest[-4:]

                # print(dest)
                shutil.copy(source, dest)
    print(f"Copied pools from {folder} into {destination_directory}")