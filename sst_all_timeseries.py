#!/usr/bin/env python3
# inagler 22/06/24

import xarray as xr
import pop_tools
import os
import re

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6, 7, 9]}, 'bounds': {'TLAT': [20., 70.]}}]
}
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')

# Function to extract member ID from filename
def extract_member_id(filename):
    match = re.search(r'temp_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

# Process each member
for file in os.listdir(data_dir):
    
    member_id = extract_member_id(file)
    #print(f'Filename: {file}, Member ID: {member_id}')
    file_path = os.path.join(data_dir, file)

    ds = xr.open_dataset(file_path)
    annual_sst = ds['TEMP'].isel(z_t=0).where(mask3d).groupby('time.year').mean('time')

    output_path = os.path.join(output_dir, f'annual_sst_member_{member_id}.nc')
    annual_sst.to_netcdf(output_path)

    print('member', member_id, 'saved')
    
print('computation complete')