#!/usr/bin/env python3
# inagler 11/09/23

# This script demeans timeseries data by:
# - Loading time series from .npy files
# - Calculating the ensemble mean for each time point
# - Demeaning the time series by subtracting the ensemble mean from each member
# - Saving the demeaned time series to new .npy files

### INITIALISATION ###

import numpy as np          # fundamental package for scientific computing
import glob                 # return all file paths that match a specific pattern

path = 'timeseries/'
files = glob.glob(path + '*time_series.npy')

### COMPUTATION ###

for i in range(len(files)):
    # open file
    data = np.load(files[i])
    
    # calculate ensemble mean
    ense_mean = np.mean(data, axis=1)
    
    # create storage array with same shape as data
    data_demean = np.zeros_like(data)

    # subtract ensemble mean from each member
    data_demean = data - ense_mean[:, np.newaxis]
    
### OUTPUT ###

    # save demeaned time series
    np.save(files[i][:-15]+'demeaned_series', data_demean)