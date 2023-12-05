#!/bin/bash

# Prepare file names and pathes
python_script='your_python_script.py'
input_directory='/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
output_directory='/phase1_CONDA/timeseries/updated_metrics'

# Iterate through each file in the input directory
for file in "${input_directory}"/*; do
    # Extract filename without extension
    filename=$(basename -- "$file")
    filename_noext="${filename%.*}"

    # Get the number of time steps in the NetCDF file
    num_time_steps=3012

    # Iterate through each time step
    for ((i=0; i<num_time_steps; i++)); do
        # Print information about the file and current time step
        echo "Processing ${filename_noext}, Time Step: ${i}"
        
        #python "${python_script}" "${file}" -t "${i}" > "${output_directory}/${filename_noext}_time${i}_result.txt"

        # Optionally, add a delay or any other logic between processing time steps
        # sleep 1
    done
done