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

# Prepare file names
event_files = ['1281.012.nc', '1301.001.nc', '1281.017.nc', '1231.020.nc', '1281.020.nc', '1281.001.nc']
temp_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp/temp_'
salt_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt/salt_'

# Regional mask
grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6, 7, 9]}, 
                             'bounds': {'TLAT': [20., 78.]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}]} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')

# Set parameters
events = np.array([68,67,44,59,80,154])
before = 40*12
after = 20*12
tp = 3*12  

# Set fixed colorbar limits
vmin_temp, vmax_temp = -4.0, 4.0 
vmin_salt, vmax_salt = -1.0, 1.0  

### COMPUTATION ###

for i in range(len(event_files)):
    
    # Load files
    event = (events[i]*12)
    ds_sst = xr.open_dataset(temp_path+event_files[i]).isel(z_t=0).where(mask3d == 1).roll(nlon=-100)
    ds_sss = xr.open_dataset(salt_path+event_files[i]).isel(z_t=0).where(mask3d == 1).roll(nlon=-100)
    
    # Calculate averages for temperature
    period1_avg_temp = ds_sst.TEMP.isel(time=slice(event-before, event-tp)).mean(dim='time')
    period2_avg_temp = ds_sst.TEMP.isel(time=slice(event+tp, event+after)).mean(dim='time')
    difference_temp = period2_avg_temp - period1_avg_temp

    # Calculate averages for salinity
    period1_avg_salt = ds_sss.SALT.isel(time=slice(event-before, event-tp)).mean(dim='time')
    period2_avg_salt = ds_sss.SALT.isel(time=slice(event+tp, event+after)).mean(dim='time')
    difference_salt = period2_avg_salt - period1_avg_salt


    # Plotting
    plt.figure(figsize=(12, 6))

    # Plot the Difference for Temperature
    plt.subplot(121)
    difference_temp_plot = difference_temp.plot(cmap=cmo.diff, vmin=vmin_temp, vmax=vmax_temp)
    plt.title('Temperature Difference')
    plt.xlim([160, 315])
    plt.ylim([250, 384])
    contour_temp = difference_temp.plot.contour(colors='k') 
    plt.clabel(contour_temp, inline=False, fontsize=8)

    # Plot the Difference for Salinity
    plt.subplot(122)
    difference_salt_plot = difference_salt.plot(cmap=cmo.diff, vmin=vmin_salt, vmax=vmax_salt)
    plt.title('Salinity Difference')
    plt.xlim([160, 315])
    plt.ylim([250, 384])
    contour_salt = difference_salt.plot.contour(colors='k') 
    plt.clabel(contour_salt, inline=False, fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.expanduser('~/phase1_CONDA/results/')+'anomaly_sst_sss_'+event_files[i][:-3]+'.png', bbox_inches='tight')
    
    print('saved file: '+event_files[i][:-3])