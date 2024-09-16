#!/usr/bin/env python3
# inagler 11/09/24

import xarray as xr
import numpy as np
import os
import glob

variables = ['salt']
input_base_directory = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/'
output_directory = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/ensemble_mean/'
chunk_size = 5

def process_variable(var):
    input_directory = os.path.join(input_base_directory, var)
    file_pattern = os.path.join(input_directory, f'{var}_*.nc')
    files = glob.glob(file_pattern)

    sum_ds = None
    count = 0

    for i in range(0, len(files), chunk_size):
        subset_files = files[i:i+chunk_size]

        # Initialize a subset sum for the current batch of files
        subset_sum = None

        for file in subset_files:
            ds = xr.open_dataset(file)
            numeric_ds = ds[[var for var in ds.data_vars if np.issubdtype(ds[var].dtype, np.number)]]

            if subset_sum is None:
                subset_sum = numeric_ds
            else:
                subset_sum = subset_sum + numeric_ds

            ds.close()

        # Sum the subsets
        if sum_ds is None:
            sum_ds = subset_sum
        else:
            sum_ds = sum_ds + subset_sum

        count += len(subset_files)

    ensemble_mean = sum_ds / count
    output_file = os.path.join(output_directory, f'ensemble_mean_{var}.nc')
    ensemble_mean.to_netcdf(output_file)
    print(f"Ensemble mean for {var} saved")

for var in variables:
    process_variable(var)