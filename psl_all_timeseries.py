#!/usr/bin/env python3
# inagler 22/06/24

import xarray as xr
import pop_tools
import os
import re

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/psl'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'


# Function to extract member ID from filename
def extract_member_id(filename):
    match = re.search(r'psl_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

# Process each member
for file in os.listdir(data_dir):
    
    member_id = extract_member_id(file)
    file_path = os.path.join(data_dir, file)

    ds = xr.open_dataset(file_path).isel(lat=slice(147, 167), lon=slice(237, 255))
    monthly_psl = ds['PSL'].mean(dim=['lat', 'lon'])

    output_path = os.path.join(output_dir, f'monthly_psl_member_{member_id}.nc')
    monthly_psl.to_netcdf(output_path)
    
    ds.close()
    monthly_psl.close()

    print(f'{member_id} saved')
    
print('')
print('computation complete')
print('')