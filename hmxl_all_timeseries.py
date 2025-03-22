#!/usr/bin/env python3
# inagler 22/06/24

# Extract and save annual mean HMXL for different members
# - Define paths and region masks using pop_tools
# - Extract member ID from filenames
# - Calculate and save regional annual mean HMXL for each member

import xarray as xr
import pop_tools
import os
import re

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/hmxl'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6, 7, 9]}, 'bounds': {'TLAT': [20., 70.]}}],
    'LabradorSea': [
        {'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}
    ]
}
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')

# Function to extract member ID from filename
def extract_member_id(filename):
    match = re.search(r'hmxl_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

# Process each member
for file in os.listdir(data_dir):
    
    member_id = extract_member_id(file)
    file_path = os.path.join(data_dir, file)

    ds = xr.open_dataset(file_path)
    monthly_hmxl = ds['HMXL'].where(mask3d).mean(dim=['nlat', 'nlon'])

    output_path = os.path.join(output_dir, f'monthly_hmxl_member_{member_id}.nc')
    monthly_hmxl.to_netcdf(output_path)
    
    ds.close()
    monthly_hmxl.close()

    print(f'{member_id} saved')
    
print('')
print('computation complete')
print('')