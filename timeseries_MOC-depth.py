#!/usr/bin/env python3
# inagler 12/09/23

# Compute time series of 
# - maximum dMOC
# - maximum sMOC  
# - dMOC in SPG (nlat=345)
# - sMOC at RAPID (nlat=274)
# for all available VVEL files
#
# Improvement suggestion: save member name with time series

### INITIALISATION ###

import numpy as np          # fundamental package for scientific computing
import xarray as xr         # data handling
import glob                 # return all file paths that match a specific pattern
import pop_tools            # to mask region of interest
#import time                 # to check duration of computation

start_time = time.time()

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
files = sorted(glob.glob(path + '*.nc'))

grid_name = 'POP_gx1v7'

#setting up of regional mask
region_defs = {
    'NorthAtlantic':[{'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [-20.0, 66.0]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}],
    'MediterraneanSea': [{'match': {'REGION_MASK': [7]}}]} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic')
mask3d = mask3d.sum('region')

# prepare arrays and dictionaries to store files
len_time = 3012 # length of time series
intervall = 1004 # to reduce compation time
dept_time_series_maxi = np.zeros((len_time, len(files)))  # array for max moc
dept_loc_maxi = np.zeros((len_time, len(files)))  # array for location of max moc
dept_time_series_rapi = np.zeros((len_time, len(files))) # array for rapid
dept_time_series_spgy = np.zeros((len_time, len(files))) # array for spg

print('initialisation complete')

def depth_MOC(ds):
    
    ### compute overturning in depth space
    overturning_depth = (ds.VVEL * ds.dz * ds.DXU).sum(dim='nlon').cumsum(dim='z_t') * 1e-6
    # compute maximum time series
    maxi_ds = overturning_depth.isel(z_t=slice(27, 51)).max(dim=['nlat', 'z_t'])
    maxi_loc = maxi_ds['nlat'].values
    maxi = maxi.values
    # find location of overturning
    loc = 
    # compute RAPID time series
    rapi = overturning_depth.isel(nlat=274, z_t=slice(27, 51)).max(dim='z_t').values
    # compute SPG time series
    spgy = overturning_depth.isel(nlat=345, z_t=slice(27, 51)).max(dim='z_t').values
    
    return maxi, maxi_loc, rapi, spgy

### COMPUTATION ###

# loop through list of files
for i in range(7, len(files)):

    # read in file abnd apply mask
    ds = xr.open_dataset(files[i])
    
    print('file ', str(i), '/', str(len(files)), ' loaded')
    
    ### Update units to SI units
    # Convert the units and update the data variable 'RHO' and 'VVEL'
    ds['VVEL'] = ds.VVEL *1e-2
    ds['dz'] = ds.dz *1e-2
    ds['z_t'] = ds.z_t *1e-2
    ds['z_w_top'] = ds.z_w_top *1e-2
    ds['z_w_bot'] = ds.z_w_bot *1e-2
    ds['DXU'] = ds.DXU *1e-2
    
    # Update the attribute for new units
    ds['VVEL'].attrs['units'] = 'm/s'
    ds['dz'].attrs['units'] = 'm'
    ds['z_t'].attrs['units'] = 'm'
    ds['z_w_top'].attrs['units'] = 'm'
    ds['z_w_bot'].attrs['units'] = 'm'
    ds['DXU'].attrs['units'] = 'm'
    
    k=0
    for j in range(3):
        
        ds_int = ds.isel(time=slice(k,k+intervall)).where(mask3d == 1)

        maxi, rapi, spgy = depth_MOC(ds_int)

        dept_time_series_maxi[k:k+intervall,i], dept_loc_maxi[k:k+intervall,i], dept_time_series_rapi[k:k+intervall,i], dept_time_series_spgy[k:k+intervall,i] = maxi, rapi, spgy
        
        k = k + intervall
        
        print('part ', str(j+1), '/3 computed')
        
    np.save("timeseries/maxi_dept_time_series_"+str(i)+".npy", dept_time_series_maxi[:,i])
    np.save("timeseries/maxi_dept_loc_"+str(i)+".npy", dept_loc_maxi[:,i])
    np.save("timeseries/rapi_dept_time_series_"+str(i)+".npy", dept_time_series_rapi[:,i])
    np.save("timeseries/spgy_dept_time_series_"+str(i)+".npy", dept_time_series_spgy[:,i])
  
    print('file ', str(i), '/', str(len(files)), ' saved')

print('computation finished')

### OUTPUT ###

# Save time series to a single file
np.save("timeseries/maxi_dept_time_series.npy", dept_time_series_maxi)
np.save("timeseries/maxi_dept_loc.npy", dept_loc_maxi)
np.save("timeseries/rapi_dept_time_series.npy", dept_time_series_rapi)
np.save("timeseries/spgy_dept_time_series.npy", dept_time_series_spgy)

print('saving successful')

print("--- intervall ", str(intervall), " takes %s seconds ---" % (time.time() - start_time))
