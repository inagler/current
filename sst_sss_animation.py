#!/usr/bin/env python3
# inagler 07/11/23

# Animate SST and SSS changes for 3 sigma event composites in CESM2 LENS2
# - Define regional mask and data paths
# - Extract and process temperature and salinity for specified periods
# - Create and save animations for each event showing spatial changes

### INITIALISATION ###

import xarray as xr
import pop_tools
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy
import cmocean.cm as cmo
import os                   # to interact with the operating system
import matplotlib.animation as animation
from IPython.display import HTML

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

before = 10
after = 10
period = (before+after)*12

### FUNCTIONS ###

# Define data and plotting functions
def plot_salt_frame(time_step):
    data = ds_sss.SALT.isel(time=start+time_step).roll(nlon=-80)
    plt.subplot(1, 2, 1)
    plt.cla()
    data.plot(cmap=cmo.haline, vmin=s_min, vmax=s_max)
    contour = data.plot.contour(colors='k')
    plt.clabel(contour, inline=False, fontsize=8)
    plt.xlim([180, 310])
    plt.ylim([250, 370])
    
    # create title
    time_values = ds_sss.time.isel(time=start+time_step).values
    time_objects = np.array(time_values, dtype='datetime64[ns]')
    date = np.datetime_as_string(time_objects, unit='M')
    plt.title(f'SSS - {date}')

def plot_temp_frame(time_step):
    data = ds_sst.TEMP.isel(time=start+time_step).roll(nlon=-80)
    plt.subplot(1, 2, 2)
    plt.cla()
    data.plot(cmap=cmo.thermal, vmin=t_min, vmax=t_max)
    contour = data.plot.contour(colors='k')
    plt.clabel(contour, inline=True, fontsize=8)
    plt.xlim([180, 310])
    plt.ylim([250, 370])
    plt.title(f'TEMP - Time Step {time_step}')
    
    # create title
    time_values = ds_sst.time.isel(time=start+time_step).values
    time_objects = np.array(time_values, dtype='datetime64[ns]')
    date = np.datetime_as_string(time_objects, unit='M')
    plt.title(f'SST - {date}')
    
### COMPUTATION ###

for i in range(len(event_files)):
    # set beginning of period
    start  = (events[i]*12)-(before*12)
    
    # load file
    ds_sst = xr.open_dataset(temp_path+event_files[i]).isel(z_t=0).where(mask3d == 1)
    ds_sss = xr.open_dataset(salt_path+event_files[i]).isel(z_t=0).where(mask3d == 1)
    
    t_min, t_max = ds_sst.TEMP.min().values, ds_sst.TEMP.max().values
    s_min, s_max = ds_sss.SALT.min().values, ds_sss.SALT.max().values

    # create animation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    num_time_steps = period  
    ani = animation.FuncAnimation(fig, lambda x: (plot_salt_frame(x), plot_temp_frame(x)),
                                  frames=num_time_steps, interval=800)
    ani.save(os.path.expanduser('~/phase1_CONDA/results/')+'sst_sss_'+event_files[i][:-3]+'.gif', writer='pillow', fps=3)