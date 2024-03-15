import os                   # to interact with the operating system
import glob

import numpy as np
import pandas as pd
import xarray as xr

import pop_tools
import gsw                  # compute potential density

import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy
import cmocean.cm as cmo
import matplotlib.ticker as ticker

from matplotlib import animation, gridspec

print('packages check')

### INITIALISATION

vvel_file = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/VVELcomposite.nc'
sigma_file = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/SIGMA_2composite.nc'

labels = [r'Barotropic Streamfunction Anomaly $\Delta BSF$ [Sverdrup]', 
          r'Depth Streamfunction Anomaly $Delta dMOC$ [Sverdrup]', 
          r'Desnity Streamfunction Anomaly $\Delta \sigma MOC$ [Sverdrup]']
cmap = cmo.balance

print('initialisation complete')

### COMPUTATION

vvel_ds = xr.open_dataset(vvel_file)
sigma_ds = xr.open_dataset(sigma_file)
dens_file = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/composite_1231.001.nc'
ds = xr.open_dataset(dens_file).isel(time=0)

print('composite nc files have been opened')

## stream functions
def BSF(ds, ds_parameters):
    bsf = []
    for time_idx in range(len(ds.time)):
        ds_time_step = ds.isel(time=time_idx)
        bsf_time_step = (ds_time_step.VVEL * ds_parameters.dz * ds_parameters.DXU).sum(dim='z_t').cumsum(dim='nlon')
        bsf.append(bsf_time_step)
    bsf_ds = xr.concat(bsf, dim='time')
    return bsf_ds*1e-12

def depth_MOC(ds, ds_parameters):
    dmoc = []
    for time_idx in range(len(ds.time)):
        ds_time_step = ds.isel(time=time_idx)
        dmoc_time_step = (ds_time_step.VVEL * ds_parameters.dz * ds_parameters.DXU).sum(dim='nlon').cumsum(dim='z_t')
        dmoc.append(dmoc_time_step)
    dmoc_ds = xr.concat(dmoc, dim='time')
    return dmoc_ds*1e-12

def density_MOC(ds_vvel, ds_sigma, ds_parameters):
    sigma_level = [12., 16., 20., 24., 28., 28.5, 29.2, 29.4, 29.6, 29.8, 30., 30.2, 30.4, 30.6,
                   30.8, 31., 31.2, 31.4, 31.6, 31.8, 32., 32.2, 32.4, 32.6, 32.8, 33., 33.2, 33.4,
                   33.6, 33.8, 34., 34.2, 34.4, 34.6, 34.8, 35., 35.2, 35.4, 35.6, 35.8, 36.1, 36.2,
                   36.3, 36.4, 36.55, 36.6, 36.65, 36.7, 36.72, 36.74, 36.76, 36.78, 36.8, 36.82,
                   36.84, 36.86, 36.88, 36.9, 36.92, 36.94, 36.96, 36.98, 37., 37.02, 37.04, 37.06,
                   37.08, 37.1, 37.12, 37.14, 37.16, 37.18, 37.2, 37.25, 37.3, 37.35, 37.4, 37.45,
                   37.6, 37.7, 37.8, 37.9, 38., 39., 40., 41., 42.]
    min_lat = 250
    max_lat = 360
    smoc = []
    for time_idx in range(len(ds_vvel.time)):
        ds_vvel_time_step = ds_vvel.isel(time=time_idx)
        ds_sigma_time_step = ds_sigma.isel(time=time_idx)
        overturning = np.zeros([len(sigma_level), (max_lat - min_lat)])
        for j in range(min_lat, max_lat):
            sigma_transport = np.zeros(len(sigma_level))
            v_transport = (ds_vvel_time_step.VVEL.isel(nlat=j) * ds_parameters.dz.isel(nlat=j) * ds_parameters.DXU.isel(nlat=j)).values
            sigma_crossection = ds_sigma_time_step.SIGMA_2.isel(nlat=j).values
            for i in range(len(sigma_level) - 1):
                ind = np.where((sigma_crossection >= sigma_level[i]) & (sigma_crossection < sigma_level[i + 1]))
                sigma_transport[i] = np.nansum(v_transport[ind])
            overturning[:, j - min_lat] = np.cumsum(sigma_transport)[::-1]
            overturning[:, j - min_lat] = overturning[:, j - min_lat][::-1]
            
        overturning_ds = xr.Dataset({'densMOC': (['sigma', 'nlat'], overturning)})
        overturning_ds['densMOC'] = overturning_ds.densMOC*1e-12
        overturning_ds['sigma'] = sigma_level
        overturning_ds['nlat'] = ds_parameters.nlat.isel(nlat=slice(min_lat, max_lat))
        
        smoc.append(overturning_ds)
    smoc_ds = xr.concat(smoc, dim='time')
    return smoc_ds

bsf_ds = BSF(vvel_ds, ds)
print('BSF composite computed')
bsf_ds.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/BSFcomposite.nc')
print('BSF composite nc file has been saved')
print('')
dmoc_ds = depth_MOC(vvel_ds, ds)
print('dMOC composite computed')
dmoc_ds.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/dMOCcomposite.nc')
print('dMOC composite nc file has been saved')
print('')
smoc_ds = density_MOC(vvel_ds, sigma_ds, ds)
print('sMOC composite computed')
smoc_ds.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/sMOCcomposite.nc')
print('sMOC composite nc file has been saved')
print('')