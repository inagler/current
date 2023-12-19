#!/bin/bash

export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE="en_US.UTF-8"
export LANG=en_US.UTF-8

### INTIALISATION

# Prepare file names and paths
python_script='test_bash.py'
input_directory='/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
output_directory='${HOME}/phase1_CONDA/timeseries/updated_metrics'
# set parameters
num_cores=4
num_time_steps=3012

### FUNCTIONS

# Function to process a single file
process_file() {
    # Capture the file path passed as the first argument to the function
    local file="$1"
    # Extract the filename without the ".nc" extension using the 'basename' command
    local filename_noext=$(basename -- "$file" .nc)
    # Create the path for the output CSV file using the specified output directory
    # and the extracted filename without extension, followed by "_result.csv"
    local result_csv="${output_directory}/${filename_noext}_result.csv"

    echo "Processing ${filename_noext}"

    for ((i=0; i<num_time_steps; i++)); do

        result=$(python "${python_script}" "${file}" -t "${i}")
        echo "${result}" >> "${result_csv}"

        if [ $? -ne 0 ]; then
            echo "Error: Python script encountered an error at Time Step ${i}"
            # ADD NANs FOR THE VALUES IN THIS ROW
        fi
    done
}

### COMPUTATION

# Cleanup: Remove existing result CSV files to not append
find "${output_directory}" -type f -name "*_result.csv" -exec rm -f {} +

# Get the sorted list of .nc files
file_list=$(find "$directory" -type f -name "*.nc" | sort --version-sort)

# Read in file names and process them
for file in $file_list; do






    # Check if all cores are occupied
    while [ $(pgrep -c -f process_file "$file" & || true) -ge "${num_cores}" ]; 
    # while [ $(ps -C $1 | grep $1 | wc -l) -ge $2 ]; do
        sleep 600  # Wait for a second before checking again
    done
    # Start function `process_file()` with file as input
done

# Wait for all background processes to finish
wait

echo "Process is finished!"