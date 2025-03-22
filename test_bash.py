#!/usr/bin/env python3
# inagler 07/12/23

# - Extract filename and time step from command-line arguments
# - Validate number of arguments
# - Print the filename and time step

import sys

# Check if the correct number of command-line arguments is provided
if len(sys.argv) != 4:
    print("Usage: python test_bash.py <filename> -t <time_step>")
    sys.exit(1)

# Extract filename and time step from command-line arguments
filename = sys.argv[1]
time_step = sys.argv[3]

# Print the filename and time step
print(f"Filename: {filename}, Time Step: {time_step}")
