#!/usr/bin/env python3
# inagler 07/11/23

### INITIALISATION ###

import xarray as xr
import pop_tools
import numpy as np
import matplotlib.pyplot as plt
import cartopy
import cmocean.cm as cmo
import os                   

# setting up of regional mask
grid_name = 'POP_gx1v7'
#setting up of regional mask
region_defs = {
    'NorthAtlantic':[{'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [20.0, 66.0]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}],
    'MediterraneanSea': [{'match': {'REGION_MASK': [7]}}]} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic')
mask3d = mask3d.sum('region')

event_files = ['1281.012.nc', '1301.001.nc', '1281.017.nc', '1231.020.nc', '1281.020.nc', '1281.001.nc']
events = np.array([68,67,44,59,80,154])

temp_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp/temp_'
salt_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt/salt_'

### COMPUTATION ###

for i in range(len(event_files)):
    
    before = 40*12
    after = 20*12
    event = (events[i]*12)
    tp= 3*12 # transition_period 

    # load file
    ds_sst = xr.open_dataset(temp_path+event_files[i]).isel(z_t=0).where(mask3d == 1).roll(nlon=-80)
    ds_sss = xr.open_dataset(salt_path+event_files[i]).isel(z_t=0).where(mask3d == 1).roll(nlon=-80)
    
    t_min, t_max = ds_sst.TEMP.min().values, ds_sst.TEMP.max().values
    s_min, s_max = ds_sss.SALT.min().values, ds_sss.SALT.max().values
    
    # Temperature
    
    period1_avg = ds_sst.TEMP.isel(time=slice(event-before, event-tp)).mean(dim='time')
    period2_avg = ds_sst.TEMP.isel(time=slice(event+tp, event+after)).mean(dim='time')
    difference = period2_avg - period1_avg

    # Plotting
    plt.figure(figsize=(15, 4))

    # Plot Period 1 Average
    plt.subplot(131)
    period1_avg.plot(cmap=cmo.thermal)
    plt.title('Period 1 Average')
    plt.xlim([180, 310])
    plt.ylim([250, 370])

    # Plot Period 2 Average
    plt.subplot(132)
    period2_avg.plot(cmap=cmo.thermal)
    plt.title('Period 2 Average')
    plt.xlim([180, 310])
    plt.ylim([250, 370])

    # Plot the Difference
    plt.subplot(133)
    difference.plot(cmap=cmo.diff)
    plt.title('Difference between Period 2 and Period 1')
    plt.xlim([180, 310])
    plt.ylim([250, 370])

    plt.tight_layout()
    plt.savefig(os.path.expanduser('~/phase1_CONDA/results/')+'anomaly_sst'+event_files[i][:-3]+'.png', bbox_inches='tight')
    
    # Salinity
    
    period1_avg = ds_sss.SALT.isel(time=slice(event-before, event-tp)).mean(dim='time')
    period2_avg = ds_sss.SALT.isel(time=slice(event+tp, event+after)).mean(dim='time')
    difference = period2_avg - period1_avg

    # Plotting
    plt.figure(figsize=(15, 4))

    # Plot Period 1 Average
    plt.subplot(131)
    period1_avg.plot(cmap=cmo.haline)
    plt.title('Period 1 Average')
    plt.xlim([180, 310])
    plt.ylim([250, 370])

    # Plot Period 2 Average
    plt.subplot(132)
    period2_avg.plot(cmap=cmo.haline)
    plt.title('Period 2 Average')
    plt.xlim([180, 310])
    plt.ylim([250, 370])

    # Plot the Difference
    plt.subplot(133)
    difference.plot(cmap=cmo.diff)
    plt.title('Difference between Period 2 and Period 1')
    plt.xlim([180, 310])
    plt.ylim([250, 370])

    plt.tight_layout()
    plt.savefig(os.path.expanduser('~/phase1_CONDA/results/')+'anomaly_sss'+event_files[i][:-3]+'.png', bbox_inches='tight')


