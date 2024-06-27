#!/usr/bin/env python3
# inagler 25/06/24

import os
import re
import xarray as xr
import pop_tools  
import gsw
import numpy as np

# choose latitude
sel_nlat = 345

vvel_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel'
temp_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp'
salt_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt'

output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'
missing_files_report = os.path.join(output_dir, 'missing_files.txt')

# this is not the most elegant way, it would be better to just give the nlon range
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

def extract_member_id(filename):
    match = re.search(r'vvel_([^.]+(?:\.\d+)?)\.nc', filename)
    
    return match.group(1) if match else None

def calculate_sigma2(temp_ds, salt_ds, nlat=345):
    CT = gsw.conversions.CT_from_pt(salt_ds['SALT'].isel(nlat=nlat), temp_ds['TEMP'].isel(nlat=nlat))
    sigma2_at_latitude = gsw.density.sigma2(salt_ds['SALT'].isel(nlat=nlat), CT)
    return sigma2_at_latitude

def density_MOC(vvel_ds, sigma_ds, nlat):
    sigma_levels =[12., 16., 20., 24., 28., 28.5, 29.2, 29.4, 29.6, 29.8, 30., 30.2, 30.4, 30.6, 30.8, 31., 31.2, 31.4, 31.6, 31.8, 32., 32.2, 32.4, 32.6, 32.8, 33., 33.2, 33.4,
                   33.6, 33.8, 34., 34.2, 34.4, 34.6, 34.8, 35., 35.1, 35.2, 35.3, 35.4, 35.5, 35.6, 35.7, 35.8, 35.9, 36, 36.1, 36.15, 36.2, 36.25, 36.3, 36.35, 
                   36.4, 36.42, 36.44, 36.46, 36.48, 36.5, 36.52, 36.54, 36.56, 36.57, 
                   36.58, 36.59, 36.6, 36.61, 36.62, 36.63, 36.64, 36.65, 36.66, 36.67, 36.68, 36.69, 36.7, 36.71, 36.72, 36.73, 36.74, 36.75, 36.76, 
                   36.78, 36.8, 36.82, 36.84, 36.86, 36.88, 36.9, 36.92, 36.94, 36.96, 36.98, 37., 37.02, 37.04, 37.06, 37.08, 37.1, 37.12, 
                   37.14, 37.16, 37.18, 37.2, 37.25, 37.3, 37.35, 37.4, 37.45, 37.6, 37.7, 37.8, 37.9, 38., 39., 40., 41., 42.]
    max_overturning_timeseries = []
    # Iterate over each time step
    for t in range(len(vvel_ds.time)):
        # Extract data for the current time step and the given latitude
        v_transport = vvel_ds['VVEL'].isel(time=t, nlat=nlat) * vvel_ds['dz'].isel(time=t, nlat=nlat) * vvel_ds['DXU'].isel(time=t, nlat=nlat)
        sigma_crossection = sigma_ds.isel(time=t)
        sigma_transport = np.zeros(len(sigma_levels))
        # Integrate volume transport over each density bin
        for i in range(len(sigma_levels) - 1):
            ind = (sigma_crossection >= sigma_levels[i]) & (sigma_crossection < sigma_levels[i + 1])
            sigma_transport[i] = v_transport.where(ind).sum()
        overturning = np.cumsum(sigma_transport)[::-1]  # Integratively sum and invert for MOC calculation
        max_overturning = np.max(overturning)  # Take the maximum overturning at this time step
        max_overturning_timeseries.append(max_overturning)
    # Convert the list to a DataArray to return a proper Xarray structure
    return xr.DataArray(max_overturning_timeseries, dims=["time"], coords={"time": vvel_ds['time']}) * 1e-12

with open(missing_files_report, 'w') as f:
    f.write("Missing temperature or salinity files for members:\n")

total_members = len(os.listdir(temp_dir))
processed_count = 0

for file in os.listdir(vvel_dir):
    if file.endswith('.nc'):
        member_id = extract_member_id(file)
        vvel_path = os.path.join(vvel_dir, file)
        temp_path = os.path.join(temp_dir, f'temp_{member_id}.nc')
        salt_path = os.path.join(salt_dir, f'salt_{member_id}.nc')
        
        print(f'Processing member {member_id}...')
        
        # Check file existence and log accordingly
        missing_files = []
        if not os.path.exists(temp_path):
            missing_files.append("temp")
        if not os.path.exists(salt_path):
            missing_files.append("salt")

        if missing_files:
            missing_data_msg = f"Missing {' and '.join(missing_files)} data file(s) for member {member_id}. Skipping..."
            print(missing_data_msg)
            with open(missing_files_report, 'a') as f:
                f.write(f"{member_id}: Missing {' and '.join(missing_files)} file(s).\n")
            continue
            
        try:
            temp_ds = xr.open_dataset(temp_path).resample(time='AS').mean().where(maskBSF)
            salt_ds = xr.open_dataset(salt_path).resample(time='AS').mean().where(maskBSF)
            
            sigma_ds = calculate_sigma2(temp_ds, salt_ds)

            vvel_ds = xr.open_dataset(vvel_path).resample(time='AS').mean().where(maskBSF)
            max_overturning_series = density_MOC(vvel_ds, sigma_ds, sel_nlat)
            max_overturning_series.to_netcdf(os.path.join(output_dir, f'annual_smoc55_member_{member_id}.nc'))
            
            processed_count += 1
            print(f'{member_id} saved')
        except Exception as e:
            print(f"Error processing member {member_id}: {str(e)}")

print(f'All computations complete. Processed {processed_count} out of {total_members} total members.')