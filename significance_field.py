#!/usr/bin/env python3
# inagler 12/04/24

import os                   # to interact with the operating system
import glob

import numpy as np
import pandas as pd
import xarray as xr

import pop_tools            # to mask region of interest
import gsw                  # compute potential density

# set up regional mask
grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6, 7, 9]}, 'bounds': {'TLAT': [20., 78.]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}]} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')

# set time range to historical period
hist_period = (2014-1850)*12
time = slice(0, hist_period)

variables = ['temp','salt','vvel','shf','ssh','hmxl'] #,'aice','n_heat'

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/'

for var in variables:
    
    print('')
    print(var+ ' started')
    print('')
    
    files = sorted(glob.glob(path + var + '/*.nc'))

    ds_collect = []
    uppercase_var = var.upper()

    # open file
    for i in range(len(files)):
        try:
            ds = xr.open_dataset(files[i]).isel(time=time)
            ds = ds[uppercase_var].where(mask3d == 1)
            
            if var == 'hmxl':
                ds = ds.isel(time=(ds['time.month'] == 3))
            
            # compute mean per location over time
            ds = ds.mean('time')

            # store
            ds_collect.append(ds)
        except Exception as e:
            print(f"Error processing file '{files[i]}': {str(e)}")
            continue  # Skip to the next file if an error occurs

    if not ds_collect:  # Check if no valid datasets were collected
        print(f"No valid datasets found for '{var}'. Skipping.")
        continue  # Skip to the next variable if no valid datasets were collected

    stacked_fields = xr.concat(ds_collect, dim='fields')    

    # compute mean between all members per location
    mean_values = stacked_fields.mean(dim='fields')

    # compute standard deviation between all members per location
    std_values = stacked_fields.std(dim='fields')

    # save field
    # Create a new dataset to store the mean and standard deviation values together
    combined_dataset = xr.Dataset({'mean_values': mean_values, 'std_values': std_values})

    # Save the dataset to a NetCDF file
    combined_dataset.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/composites/'+var+'_mean_std.nc')
    
    print(var + ' completed')
    
print('')
print('simple variables done!')
print('')
print('now lets start with the beautiful potential density')


var = 'temp'
ds_collect = []
files = sorted(glob.glob(path + var + '/*.nc'))
# open file
for i in range(len(files)):
    try:
        ds = xr.open_dataset(files[i]).isel(time=time)
        ds = ds.where(mask3d == 1)
        ds = ds.mean('time')
        ds_collect.append(ds)
    except Exception as e:
        print(f"Error processing file '{files[i]}': {str(e)}")
        continue  # Skip to the next file if an error occurs

if not ds_collect:  # Check if no valid datasets were collected
    print(f"No valid datasets found for '{var}'. Skipping.")
else:
    stacked_temp = xr.concat(ds_collect, dim='fields')    

var = 'salt'
ds_collect = []
files = sorted(glob.glob(path + var + '/*.nc'))
# open file
for i in range(len(files)):
    try:
        ds = xr.open_dataset(files[i]).isel(time=time)
        ds = ds.where(mask3d == 1)
        ds = ds.mean('time')
        ds_collect.append(ds)
    except Exception as e:
        print(f"Error processing file '{files[i]}': {str(e)}")
        continue  # Skip to the next file if an error occurs

if not ds_collect:  # Check if no valid datasets were collected
    print(f"No valid datasets found for '{var}'. Skipping.")
else:
    stacked_salt = xr.concat(ds_collect, dim='fields')   

# Compute potential density
stacked_temp = stacked_temp.update(stacked_salt[["SALT"]])
CT = gsw.conversions.CT_from_pt(stacked_temp.SALT, stacked_temp.TEMP)
stacked_temp['SIGMA_2'] = gsw.density.sigma2(stacked_temp.SALT, CT)

# compute mean between all members per location
mean_values = stacked_temp['SIGMA_2'].mean(dim='fields')

# compute standard deviation between all members per location
std_values = stacked_temp['SIGMA_2'].std(dim='fields')

# save field
# Create a new dataset to store the mean and standard deviation values together
combined_dataset = xr.Dataset({'mean_values': mean_values, 'std_values': std_values})

# Save the dataset to a NetCDF file
combined_dataset.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/composites/sigma_2_mean_std.nc')

print('')
print('potential density complete!!')
print('')
print('and now onto the lovely sea level pressure')


var = 'psl'
    
print('')
print(var+ ' started')
print('')

files = sorted(glob.glob(path + var + '/*.nc'))

ds_collect = []
uppercase_var = var.upper()

# open file
for i in range(len(files)):
    try:
        ds = xr.open_dataset(files[i]).isel(time=time)
        ds = ds.PSL.mean('time')

        ds_collect.append(ds)
    except Exception as e:
        print(f"Error processing file '{files[i]}': {str(e)}")
        continue  # Skip to the next file if an error occurs

if not ds_collect:  # Check if no valid datasets were collected
    print(f"No valid datasets found for '{var}'. Skipping.")
else:
    stacked_fields = xr.concat(ds_collect, dim='fields')    

    # compute mean between all members per location
    mean_values = stacked_fields.mean(dim='fields')

    # compute standard deviation between all members per location
    std_values = stacked_fields.std(dim='fields')

    # save field
    # Create a new dataset to store the mean and standard deviation values together
    combined_dataset = xr.Dataset({'mean_values': mean_values, 'std_values': std_values})

    print(var + ' completed')
    print('-->')
    print('adventure accomplished!')
