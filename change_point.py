#!/usr/bin/env python3
# inagler 16/09/23

### Description
# Detect change points in time series data using ruptures
# - Load and initialize time series files
# - Detect change points for each file using ruptures' Window model
# - Store results in a dictionary
# - Save all results to a compressed file

### INITIALISATION ###

import numpy as np          # fundamental package for scientific computing
import glob                 # return all file paths that match a specific pattern
import ruptures as rpt      # for off-line change point detection

path = 'timeseries/'
files = glob.glob(path + '*demeaned_series.npy')

# length of time series
len_time = 3012

arrays_dict = {} # Create a dictionary to store the arrays

print('initialisation complete')

### COMPUTATION ###

# loop through list of files
for i in range(len(files)):
    
    signal = np.load(files[i])
        
    # compute change points
    algo_window = rpt.Window(model="rbf").fit(signal) 
    result = algo_window.fit_predict(signal, pen=40)

    # Add the arra to the dictionary with a unique key
    key = f"array_{i}"
    arrays_dict[key] = result
    
    print('file ', str(i), '/', str(len(files)), ' executed')
    
print('execution finished')
    
### OUTPUT ###
# Save all change point arrays containing to a single file
np.savez(files[i][11:-19]+"_change_points.npz", **arrays_dict)
    
print('saving successful')