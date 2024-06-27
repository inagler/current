#!/usr/bin/env python3
# inagler 22/06/24

import xarray as xr
import pop_tools
import glob
import cftime

# Define paths
base_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/'
output_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/'

print("Processing start")
print("")

# Function to compute anomalies
def compute_anomalies(var_name):
    # Obtain list of files for the variable
    files_list = sorted(glob.glob(f'{base_path}{var_name}/{var_name}_*.nc'))
    
    # Process files individually
    period1_averages = []
    period2_averages = []

    for f in files_list:
        ds = xr.open_dataset(f, use_cftime=True)
        
        # Select periods and apply the mask from 1 file
        ds_p1 = ds.sel(time=slice('1850-01', '1875-12'))
        ds_p2 = ds.sel(time=slice('1975-01', '2000-12'))
        
        # Load and apply regional mask
        grid_name = 'POP_gx1v7'
        region_defs = {
        'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6, 7, 9]}, 'bounds': {'TLAT': [20., 78.]}}],
        'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}]}
        mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
        mask3d = mask3d.sum('region')

        ds_p1_masked = ds_p1.where(mask3d == 1)
        ds_p2_masked = ds_p2.where(mask3d == 1)
        
        # Calculate means for each period
        period1_mean = ds_p1_masked.mean(['time'])
        period2_mean = ds_p2_masked.mean(['time'])
        
        # Store results
        period1_averages.append(period1_mean)
        period2_averages.append(period2_mean)
    
    # Concatenate and average results across all files
    final_p1_avg = xr.concat(period1_averages, dim='file').mean('file')
    final_p2_avg = xr.concat(period2_averages, dim='file').mean('file')
    
    # Compute anomaly
    anomaly = final_p2_avg - final_p1_avg
    
    # Save the results
    output_file = f'{output_path}{var_name}_historical_anomaly.nc'
    anomaly.to_netcdf(output_file)
    print(f"Composite anomaly for {var_name} saved to {output_file}")

compute_anomalies('temp')
print("TEMP done")
#print("testing complete")
compute_anomalies('salt')
print("SALT done")
compute_anomalies('shf')
print("SHF done")
print("")
print("Processing complete")