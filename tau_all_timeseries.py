#!/usr/bin/env python3
# inagler 22/06/24

import xarray as xr
import pop_tools
import os
import re

# Define configurations and paths
taux_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/taux'
tauy_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/tauy'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

grid_name = 'POP_gx1v7'
region_defs = {
    'LabradorSea': [
        {'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}        
    ]}
mask_lab_sea = pop_tools.region_mask_3d(grid_name, 
                                  region_defs=region_defs, 
                                  mask_name='Labrador Sea')
mask_lab_sea = mask_lab_sea.sum('region')  


# Function to extract member ID from filename
def extract_member_id(filename):
    match = re.search(r'taux_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

# Process each member
for file in os.listdir(taux_dir):
    
    member_id = extract_member_id(file)
    #print(f'Filename: {file}, Member ID: {member_id}')
    
    taux_path = os.path.join(taux_dir, file)
    tauy_path = os.path.join(tauy_dir, f'tauy_{member_id}.nc')

    ds_taux = xr.open_dataset(taux_path).where(mask_lab_sea).mean(dim=['nlat','nlon'])
    ds_tauy = xr.open_dataset(tauy_path).where(mask_lab_sea).mean(dim=['nlat','nlon'])
    
    da_mag = ((ds_taux.TAUX*1e-1)**2 + (ds_tauy.TAUY*1e-1)**2)**0.5

    output_path = os.path.join(output_dir, f'monthly_tau_member_{member_id}.nc')
    da_mag.to_netcdf(output_path)

    print('member', member_id, 'saved')
    
print('computation complete')