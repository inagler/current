#!/usr/bin/env python3
# inagler 11/09/24

import xarray as xr
import numpy as np
import os
import glob

var = 'hmxl'
input_base_directory = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/'
output_directory = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/ensemble_mean/'
chunk_size = 10  # Adjust chunk size based on memory constraints

os.makedirs(output_directory, exist_ok=True)

def process_variable(var):
    input_directory = os.path.join(input_base_directory, var)
    file_pattern = os.path.join(input_directory, f'{var}_*.nc')
    files = glob.glob(file_pattern)

    sum_ds = None
    count = 0

    for i in range(0, len(files), chunk_size):
        subset_files = files[i:i+chunk_size]
        subset_ds = xr.concat([xr.open_dataset(file) for file in subset_files], dim='ensemble')
        
        if sum_ds is None:
            sum_ds = subset_ds.sum(dim='ensemble')
        else:
            sum_ds += subset_ds.sum(dim='ensemble')
        
        count += subset_ds.sizes['ensemble']
        subset_ds.close()

    ensemble_mean = sum_ds / count
    output_file = os.path.join(output_directory, f'ensemble_mean_{var}.nc')
    ensemble_mean.to_netcdf(output_file)
    print(f"Ensemble mean for {var} saved")

process_variable(var)