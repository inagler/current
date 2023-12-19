#!/usr/bin/env python3
# inagler 19/12/23

import sys
import random

def generate_random_numbers():
    # Generate 4 random numbers
    random_numbers = [random.uniform(0, 1) for _ in range(4)]
    return random_numbers

if __name__ == "__main__":
    # Check if the script is provided with the correct command-line arguments
    if len(sys.argv) != 4 or sys.argv[2] != "-t":
        print("Usage: python file1.py <input_file> -t <time_step_index>")
        sys.exit(1)

    input_file = sys.argv[1]
    time_step_index = int(sys.argv[3])

    # Perform any necessary processing based on the input file or time step index
    # For simplicity, in this example, we generate random numbers
    result = generate_random_numbers()

    # Print the result to stdout (this will be captured by the calling script)
    print(",".join(map(str, result)))
