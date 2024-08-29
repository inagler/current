#!/usr/bin/env python3
# inagler 31/07/24

import xarray as xr
import os
import re
import pop_tools

# choose latitude
sel_nlat = 345

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

# this is not the most elegant way, it would be better to just give the nlon range
grid_name = 'POP_gx1v7'
region_defs = {
    'SubpolarAtlantic':[
        {'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [45.0, 66.0], 'TLONG': [260.0, 360.0]}}
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
    match = re.search(r'vvel_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

def calculate_dmoc(ds, mask, nlat):
    depth_range = slice(27, 51)
    ds = ds.roll(nlon=-100)
    dmoc = (ds.VVEL * ds.dz * ds.DXU).sum(dim='nlon').cumsum(dim='z_t')
    dmoc = dmoc.isel(z_t=depth_range, nlat=nlat)
    return dmoc * 1e-12  # Convert to Sverdrup

for file in os.listdir(data_dir):
    member_id = extract_member_id(file)
    file_path = os.path.join(data_dir, file)

    ds = xr.open_dataset(file_path).resample(time='AS').mean()
    max_dmoc = calculate_dmoc(ds, maskBSF, sel_nlat)

    output_path = os.path.join(output_dir, f'max_dmoc_member_{member_id}.nc')
    max_dmoc.to_netcdf(output_path)

    ds.close()
    max_dmoc.close()

    print(f'{member_id} saved')