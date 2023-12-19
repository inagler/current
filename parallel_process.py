#!/usr/bin/env python3
# inagler 19/12/23

import os
import glob
import csv
import time
import multiprocessing
import subprocess
from netCDF4 import Dataset
import numpy as np

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

input_directory='/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
output_directory=os.path.expanduser('~/phase1_CONDA/')+'timeseries/updated_metrics'
working_directory=os.path.expanduser('~/phase1_CONDA/')+'current/'
python_files = ["file1.py", "file1.py", "file1.py", "file1.py"]
num_cores = 4

# Define column names
column_names = ["Column1", "Column2", "Column3", "Column4", "Column5", "Column6", "Column7", "Column8", "Column9", "Column10", "Column11", "Column12", "Column13", "Column14", "Column15", "Column16"]


### FUNCTIONS ###

# Function to perform the process for the time step passed
def process_time_step(file_path, time_step_index):
    output_values = []

    for python_file in python_files:
        try:
            result = subprocess.run(["python", python_file, file_path, "-t", str(time_step_index)], capture_output=True, text=True)

            # Check if subprocess had an error
            result.check_returncode()

            # Extract and append the output value
            output_values.append(result.stdout.strip())

        except subprocess.CalledProcessError as e:
            print(f"Error occurred during subprocess execution: {e}")
            # Set NaN value for the output if an error occurs
            output_values.append(str(np.nan))

    return ",".join(output_values)

# Function to check the number of running processes
def get_running_processes_count():
    return sum(1 for process in multiprocessing.active_children() if process.is_alive())

# Function to delete CSV files in the output directory
def delete_csv_files(output_directory):
    csv_files = glob.glob(os.path.join(output_directory, "*.csv"))
    for csv_file in csv_files:
        os.remove(csv_file)
        print(f"Deleted: {csv_file}")
        

### OUTPUT ###

if __name__ == "__main__":
    files = [os.path.join(input_directory, file) for file in os.listdir(input_directory) if file.endswith('.nc')]
    
    # Delete existing CSV files in the output directory
    delete_csv_files(output_directory)

    for current_file in files:
        # Open the NetCDF file
        with Dataset(current_file, 'r') as nc_file:

            # Prepare the CSV file for writing
            csv_filename = f"{output_directory}/{os.path.basename(current_file)}.csv"
            with open(csv_filename, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(column_names)

                # Iterate over each time step
                for time_step_index in range(len(nc_file.dimensions['time'])):
                    # Check the number of running processes
                    running_processes_count = get_running_processes_count()

                    # Print debugging information
                    print(f"Processing time step {time_step_index}. Running processes: {running_processes_count}")

                    # Perform the action only if the number of running processes is less than the specified limit
                    if running_processes_count < num_cores:
                        output_values = process_time_step(current_file, time_step_index)

                        print(f"output values: {output_values}")

                        # Split the output_values into a list of individual values
                        values_list = [float(val.strip()) for val in output_values.split(',')]

                        # Write each value as a separate column
                        csv_writer.writerow(values_list)

                    else:
                        print(f"Waiting for 1 minute. Current running processes: {running_processes_count}")
                        time.sleep(60)  # Wait for 1 minute before checking again

                    # Break after processing the first time step
                    break

            # Break after processing the first file
            #break

print("")
print("The process has been completed")
print("")