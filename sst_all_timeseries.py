#!/usr/bin/env python3
# inagler 22/06/24

import os
import re
import gc

import numpy as np
import pandas as pd
import xarray as xr

import cftime
import pop_tools

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [45., 66.]}}],
    'LabradorSea': [
        {'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}
    ]
}
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')

# Function to extract member ID from filename
def extract_member_id(filename):
    match = re.search(r'temp_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

# Process each member
for file in sorted(os.listdir(data_dir)):
    
    member_id = extract_member_id(file)
    file_path = os.path.join(data_dir, file)

    ds = xr.open_dataset(file_path, decode_times=False)
    ds['time'] = xr.decode_cf(ds, use_cftime=True).time
    if isinstance(ds.time.values[0], cftime._cftime.DatetimeNoLeap):
        ds['time'] = xr.DataArray(np.array([pd.Timestamp(str(dt)).to_datetime64() for dt in ds.time.values]),
                              dims='time')
    try:
        annual_sst = ds['TEMP'].isel(z_t=0).where(mask3d).resample(time='AS').mean(dim=['nlat', 'nlon'])
    except Exception as e:
        print(f"computation failed for {member_id}, using fallback: {str(e)}")
        
        total_time_steps = ds.dims['time']
        last_valid_data = None
        for t in range(total_time_steps):
            try:
                current_data = ds['TEMP'].isel(z_t=0, time=t)
                current_data.load()
                last_valid_data = current_data
            except RuntimeError as e:
                if last_valid_data is not None:
                    print(f"Error at timestep {t}")
                    current_data = last_valid_data
                else:
                    raise ValueError(f"no valid data at timestep {t}")
                    break
            if t == 0:
                combined_data = current_data
            else:
                combined_data = xr.concat([combined_data, current_data], dim='time')
        combined_data['time'] = np.arange(total_time_steps)
        ds['combined_TEMP'] = combined_data
        annual_sst = ds['combined_TEMP'].where(mask3d).mean(dim=['nlat', 'nlon'])

    output_path = os.path.join(output_dir, f'monthly_spg_sst_member_{member_id}.nc')
    annual_sst.to_netcdf(output_path)
    
    ds.close()
    annual_sst.close()
    
    del ds, annual_sst
    gc.collect()

    print(f'{member_id} saved')
    
print('')
print('computation complete')
print('')