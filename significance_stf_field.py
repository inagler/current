#!/usr/bin/env python3
# inagler 12/04/24

import os                   
import glob

import numpy as np
import pandas as pd
import xarray as xr

import pop_tools            
import gsw                  

# Define regional mask
grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic': [{'match': {'REGION_MASK': [6, 7]}, 'bounds': {'TLAT': [20., 66.]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}]} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')


# Set time range to historical period
hist_period = (2014-1850)*12
time = slice(0, hist_period)

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/'

# Define stream functions
def BSF(ds, ds_parameters):
    bsf_ds = (ds.VVEL * ds_parameters.dz * ds_parameters.DXU).sum(dim='z_t').cumsum(dim='nlon')
    return bsf_ds*1e-12

def depth_MOC(ds, ds_parameters):
    dmoc_ds = (ds.VVEL * ds_parameters.dz * ds_parameters.DXU).sum(dim='nlon').cumsum(dim='z_t')
    return dmoc_ds*1e-12

def density_MOC(ds_vvel, ds_sigma, ds_parameters):
    sigma_level = [12., 16., 20., 24., 28., 28.5, 29.2, 29.4, 29.6, 29.8, 30., 30.2, 30.4, 30.6, 30.8, 31., 31.2, 31.4, 31.6, 31.8, 32., 32.2, 32.4, 32.6, 32.8, 33., 33.2, 33.4,
                   33.6, 33.8, 34., 34.2, 34.4, 34.6, 34.8, 35., 35.1, 35.2, 35.3, 35.4, 35.5, 35.6, 35.7, 35.8, 35.9, 36, 36.1, 36.15, 36.2, 36.25, 36.3, 36.35, 
                   36.4, 36.42, 36.44, 36.46, 36.48, 36.5, 36.52, 36.54, 36.56, 36.57, 
                   36.58, 36.59, 36.6, 36.61, 36.62, 36.63, 36.64, 36.65, 36.66, 36.67, 36.68, 36.69, 36.7, 36.71, 36.72, 36.73, 36.74, 36.75, 36.76, 
                   36.78, 36.8, 36.82, 36.84, 36.86, 36.88, 36.9, 36.92, 36.94, 36.96, 36.98, 37., 37.02, 37.04, 37.06, 37.08, 37.1, 37.12, 
                   37.14, 37.16, 37.18, 37.2, 37.25, 37.3, 37.35, 37.4, 37.45, 37.6, 37.7, 37.8, 37.9, 38., 39., 40., 41., 42.]
    min_lat = 250
    max_lat = 365
    overturning = np.zeros([len(sigma_level), (max_lat - min_lat)])
    for j in range(min_lat, max_lat):
        sigma_transport = np.zeros(len(sigma_level))
        v_transport = (ds_vvel.isel(nlat=j) * ds_parameters.dz.isel(nlat=j) * ds_parameters.DXU.isel(nlat=j)).values
        sigma_crossection = ds_sigma.isel(nlat=j).values
        for i in range(len(sigma_level) - 1):
            ind = np.where((sigma_crossection >= sigma_level[i]) & (sigma_crossection < sigma_level[i + 1]))
            sigma_transport[i] = np.nansum(v_transport[ind])
        overturning[:, j - min_lat] = np.cumsum(sigma_transport)[::-1]
        overturning[:, j - min_lat] = overturning[:, j - min_lat][::-1]
    overturning_ds = xr.Dataset({'densMOC': (['sigma', 'nlat'], overturning)})
    overturning_ds['densMOC'] = overturning_ds.densMOC*1e-12
    overturning_ds['sigma'] = sigma_level
    overturning_ds['nlat'] = ds_parameters.nlat.isel(nlat=slice(min_lat, max_lat))
    return overturning_ds.densMOC

# Prepare parameter ds
dens_file = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/composite_1231.001.nc'
ds = xr.open_dataset(dens_file).isel(time=0)

files = sorted(glob.glob(path + 'vvel/*.nc'))

bsf_collect = []
dmoc_collect = []
smoc_collect = []

# Open and process each file
for i, file in enumerate(files):
    print('Processing file', i)
    try:
        # Load vvel file
        ds_vvel = xr.open_dataset(file).isel(time=time)
        ds_vvel = ds_vvel.where(mask3d == 1).mean('time')
        
        # Load temp and salt data
        ds_temp = xr.open_dataset(path+'temp/temp_'+file[-11:]).isel(time=time)
        ds_temp = ds_temp.where(mask3d == 1).mean('time')
        
        ds_salt = xr.open_dataset(path+'salt/salt_'+file[-11:]).isel(time=time)
        ds_salt = ds_salt.where(mask3d == 1).mean('time')
        
        # Compute sigma ds
        CT = gsw.conversions.CT_from_pt(ds_salt.SALT, ds_temp.TEMP)
        ds_vvel['SIGMA_2'] = gsw.density.sigma2(ds_salt.SALT, CT)
        
        # Compute bsf, dmoc, and smoc
        bsf_ds = BSF(ds_vvel, ds)
        dmoc_ds = depth_MOC(ds_vvel, ds)
        smoc_ds = density_MOC(ds_vvel.VVEL, ds_vvel.SIGMA_2, ds)
        
        # Store computed values
        bsf_collect.append(bsf_ds)
        dmoc_collect.append(dmoc_ds)
        smoc_collect.append(smoc_ds)
        
        print('File', i, 'processed successfully')
    except Exception as e:
        print('Error processing file', i, ':', e)
        continue

# Concatenate collected data
bsf_fields = xr.concat(bsf_collect, dim='fields')
dmoc_fields = xr.concat(dmoc_collect, dim='fields')    
smoc_fields = xr.concat(smoc_collect, dim='fields')  

print('Fields concatenated')

# Compute mean and standard deviation, and save data
variables = [bsf_fields, dmoc_fields, smoc_fields]
var_names = ['bsf', 'dmoc', 'smoc']
for i, stacked_fields in enumerate(variables):
    try:
        # Compute mean between all members per location
        mean_values = stacked_fields.mean(dim='fields')

        # Compute standard deviation between all members per location
        std_values = stacked_fields.std(dim='fields')

        # Create a new dataset to store the mean and standard deviation values together
        combined_dataset = xr.Dataset({'mean_values': mean_values, 'std_values': std_values})

        # Save the dataset to a NetCDF file
        combined_dataset.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/composites/'+var_names[i]+'_mean_std.nc')
        print(var_names[i], 'saving completed')
    except Exception as e:
        print('Error saving', var_names[i], ':', e)

print('Adventure complete')