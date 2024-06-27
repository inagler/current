#!/usr/bin/env python3
# inagler 25/06/24

import xarray as xr
import os
import re
import pop_tools

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

grid_name = 'POP_gx1v7'
region_defs = {
    'SubpolarAtlantic':[
        {'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [15.0, 66.0], 'TLONG': [260.0, 360.0]}}
    ],
    'LabradorSea': [
        {'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}
    ]
}
maskBSF = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='Subpolar Gyre')
maskBSF = maskBSF.sum('region')
maskBSF = maskBSF.roll(nlon=-100)

print('Computation started')

def extract_member_id(filename):
    """
    Extracts the member ID from the filename of a dataset.

    Parameters:
        filename (str): The filename from which the member ID will be extracted.

    Returns:
        str: The extracted member ID if found; otherwise, None.
    """
    match = re.search(r'vvel_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None


def calculate_bsf(ds, mask):
    """
    Computes Barotropic Streamfunction (BSF) for the entire dataset applying mask.

    Parameters:
        ds (xarray.Dataset): The dataset containing VVEL, dz, and DXU variables.
        mask (xarray.DataArray): Mask to apply to the dataset.
    
    Returns:
        xarray.DataArray: The computed BSF across the dataset post mask application
    """
    ds = ds.roll(nlon=-100)
    bsf = (ds.VVEL * ds.dz * ds.DXU).where(mask).sum(dim='z_t').cumsum(dim='nlon') 
    bsf = bsf.min(dim=['nlon', 'nlat'])
    return bsf * 1e-12  # Convert to Sverdrup


# Process each member
for file in os.listdir(data_dir):
    if file.endswith('.nc'):
        member_id = extract_member_id(file)
        file_path = os.path.join(data_dir, file)

        ds = xr.open_dataset(file_path).resample(time='AS').mean()
        min_bsf = calculate_bsf(ds, maskBSF)

        output_path = os.path.join(output_dir, f'min_BSF_member_{member_id}.nc')
        min_bsf.to_netcdf(output_path)
        
        ds.close()
        min_bsf.close()
        

        print(f'{member_id} saved')

print('All computations complete')