#!/usr/bin/env python3
# inagler 12/09/23

import numpy as np
import xarray as xr
import glob
import pop_tools
import dask.distributed

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
files = glob.glob(path + '*.nc')

grid_name = 'POP_gx1v7'

region_defs = {
    'NorthAtlantic':[{'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [-20.0, 66.0]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}],
    'MediterraneanSea': [{'match': {'REGION_MASK': [7]}}]
}
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic')
mask3d = mask3d.sum('region')

len_time = 3012
dept_time_series_maxi = np.zeros((len_time, len(files)))
dept_time_series_rapi = np.zeros((len_time, len(files)))
dept_time_series_spgy = np.zeros((len_time, len(files)))

print('initialization complete')

def depth_MOC(ds):
    overturning_depth = (ds.VVEL * ds.dz * ds.DXU).sum(dim='nlon').cumsum(dim='z_t') * 1e-6
    maxi = overturning_depth.isel(z_t=slice(27, 51)).max(dim=['nlat','z_t']).values
    rapi = overturning_depth.isel(nlat=274, z_t=slice(27, 51)).max(dim='z_t').values
    spgy = overturning_depth.isel(nlat=345, z_t=slice(27, 51)).max(dim='z_t').values
    return maxi, rapi, spgy

@dask.delayed
def process_file(file):
    ds = xr.open_dataset(file).where(mask3d == 1)
    
    # Update units to SI units
    ds['VVEL'] *= 1e-2
    ds['dz'] *= 1e-2
    ds['z_t'] *= 1e-2
    ds['z_w_top'] *= 1e-2
    ds['z_w_bot'] *= 1e-2
    ds['DXU'] *= 1e-2
    ds['VVEL'].attrs['units'] = 'm/s'
    ds['dz'].attrs['units'] = 'm'
    ds['z_t'].attrs['units'] = 'm'
    ds['z_w_top'].attrs['units'] = 'm'
    ds['z_w_bot'].attrs['units'] = 'm'
    ds['DXU'].attrs['units'] = 'm'
    
    return depth_MOC(ds)

# Use concurrent.futures to parallelize file processing
with dask.distributed.Client() as client:
    results = dask.compute(*[process_file(file) for file in files], scheduler='threads')

# Unpack results
for i, result in enumerate(results):
    dept_time_series_maxi[:, i], dept_time_series_rapi[:, i], dept_time_series_spgy[:, i] = result
    print('file', i+1, '/', len(files), 'executed')

print('computation finished')

# Save time series to a single file
np.save("timeseries/maxi_dens_time_series.npy", dept_time_series_maxi)
np.save("timeseries/rapi_dens_time_series.npy", dept_time_series_rapi)
np.save("timeseries/spgy_dens_time_series.npy", dept_time_series_spgy)

print('saving successful')
