#!/bin/bash

# Prepare file names and pathes
python_script='test_bash.py'
input_directory='/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
output_directory="${HOME}/phase1_CONDA/timeseries/updated_metrics"

# Iterate through each file in the input directory
for file in "${input_directory}"/*; do
    # Extract filename without extension
    filename=$(basename -- "$file")
    filename_noext="${filename%.*}"
    
    # Get the number of time steps in the NetCDF file
    num_time_steps=3012

    # Remove existing result CSV file
    rm -f "${result_csv}"

    # Create a separate CSV file for each input file
    result_csv="${output_directory}/${filename_noext}_result.csv"
    
    # Print information about the file
    echo "Processing ${filename_noext}"

    # Iterate through each time step
    for ((i=0; i<num_time_steps; i++)); do
        # Print information about the file and current time step
        echo "Processing ${filename_noext}, Time Step: ${i}"
        
        # Run the Python script and store the result in the CSV file
        result=$(python "${python_script}" "${file}" -t "${i}")
        echo "${result}" >> "${result_csv}"
        
        # Check the exit status of the last command
        if [ $? -ne 0 ]; then
            echo "Error: Python script encountered an error at Time Step ${i}"
            
            ## ADD NANs FOR THE VALUES IN THIS ROW
        fi
    done
    
    break
    
done