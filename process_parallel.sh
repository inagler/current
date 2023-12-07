#!/bin/bash

# Prepare file names and paths
python_script='test_bash.py'
input_directory='/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
output_directory="${HOME}/phase1_CONDA/timeseries/updated_metrics"

# Set the number of cores to use in parallel
num_cores=4

# Cleanup: Remove existing result CSV files
find "${output_directory}" -type f -name "*_result.csv" -exec rm -f {} +

# Get the number of time steps in the NetCDF file
num_time_steps=3012

# Function to process a single file
process_file() {
    local file="$1"
    local filename_noext=$(basename -- "$file" .nc)
    local result_csv="${output_directory}/${filename_noext}_result.csv"

    echo "Processing ${filename_noext}"

    for ((i=0; i<num_time_steps; i++)); do
        # Print information for debugging
        echo "DEBUG: i=${i}, num_time_steps=${num_time_steps}"

        result=$(python "${python_script}" "${file}" -t "${i}")
        echo "${result}" >> "${result_csv}"

        if [ $? -ne 0 ]; then
            echo "Error: Python script encountered an error at Time Step ${i}"
            # ADD NANs FOR THE VALUES IN THIS ROW
        fi
    done
}

export -f process_file  # Export the function for use with parallel

# Iterate through each file in the input directory and process in parallel
find "${input_directory}" -type f -name "*.nc" | \
    parallel -j "${num_cores}" process_file


