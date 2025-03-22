#!/usr/bin/env python3
# inagler 16/09/23

# Process LENS2 ocean monthly 3sigma event data:
# 'TEMP', 'SALT', 'VVEL', 'SIGMA_2', 'HMXL', 'SHF', 'SSH'
# - Calculate annual composites
# - Generate animations for annual anomalies
# - Create flip book plots for 5-year anomalies

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

files = sorted(glob.glob('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/composite*.nc'))

#variables = ['TEMP', 'SALT', 'VVEL', 'SIGMA_2', 'HMXL', 'SHF', 'SSH']
variables = ['SIGMA_2', 'HMXL', 'SHF', 'SSH']
#labels = [r'Temperature Anomaly $\Delta T$ [$^{\circ} C$]', r'Haline Anomaly $Delta S$ [$\frac{g}{kg}$]', r'Meridional Velocity Anomaly $Delta v$ [$\frac{g}{kg}$]', r'Potential Density Anomaly $\Delta\sigma_2$ [$\frac{kg}{m^3} -1000$]', r'March Mixed Layer Depth Anomaly $\Delta h$ [$m$]',r'Total Surface Heat Flux Anomaly $\Delta Q_s$ [$\frac{W}{m^2}$]', r'Sea Surface Height Anomaly $\Delta \eta$ [$m$]']
labels = [r'Potential Density Anomaly $\Delta\sigma_2$ [$\frac{kg}{m^3} -1000$]', r'March Mixed Layer Depth Anomaly $\Delta h$ [$m$]',r'Total Surface Heat Flux Anomaly $\Delta Q_s$ [$\frac{W}{m^2}$]', r'Sea Surface Height Anomaly $\Delta \eta$ [$m$]']
#cmaps = [cmo.balance, cmo.delta, cmo.balance, cmo.tarn, cmo.diff, cmo.curl, cmo.diff]
cmaps = [cmo.tarn, cmo.diff, cmo.curl, cmo.diff]

print('initialisation complete')

### COMPUTATION

## create data

for v in range(len(variables)):
    
    var = variables[v]
    
    print('starting with '+var)

    var_years = []
    for t in range(60):
        var_year = []
        for i in range(len(files)):
            try:
                ds = xr.open_dataset(files[i])
            except ValueError as e:
                continue

            ds_file = ds[var].isel(time=t)
            var_year.append(ds_file)

        ds_comp = xr.concat(var_year, dim='file').mean(dim='file')
        var_years.append(ds_comp)

    ds_var_annual = xr.concat(var_years, dim='time')
    
    ds_var_annual.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/' + var + 'composite.nc')
    
    print(var+' composite nc file has been created')
     
## make animation
    
    def plot_var_frame(time_step):
        data = ds.isel(time=start + time_step)
        ax1.cla()
        im = ax1.imshow(data, cmap=cmaps[v], vmin=vmin, vmax=vmax) 
        contour = ax1.contour(data, colors='k')
        ax1.clabel(contour, inline=True, fontsize=8)
        ax1.set_xlim([170, 310])
        ax1.set_ylim([250, 382])
        ax1.set_title(var+f' - year:{1+time_step}')

    # Set up initial data
    start = 1
    
    if var == 'TEMP' or var == 'SALT' or var == 'VVEL' or var == 'SIGMA_2':
        ds = ds_var_annual.sel(z_t=slice(5.0000000e+02, 8.7882523e+04)).mean('z_t') - ds_var_annual.isel(time=0).sel(z_t=slice(5.0000000e+02, 8.7882523e+04)).mean('z_t')
    else:
        ds = ds_var_annual - ds_var_annual.isel(time=0)
        
    vmin, vmax = -abs(ds).max(), abs(ds).max()

    # create figure and set up layout of subplots
    fig = plt.figure(figsize=(8, 5))
    gs = gridspec.GridSpec(1, 2, width_ratios=[13, 1])

    # main subplot for animation
    ax1 = plt.subplot(gs[0])

    # Acolorbar subplot 
    cax = plt.subplot(gs[1])
    num_time_steps = 59
    ani = animation.FuncAnimation(fig, plot_var_frame, frames=num_time_steps, interval=800)

    # set colorbar
    sm = plt.cm.ScalarMappable(cmap=cmaps[v], norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm.set_array([])
    cbar = plt.colorbar(sm, cax=cax)
    cbar.set_label(labels[v])

    # Save animation
    ani.save(os.path.expanduser('~/phase1_CONDA/results/') + var + 'annual_anomaly.gif', writer='pillow', fps=3)
    
    print(var+' animation has been created')
    
    fig, axes = plt.subplots(nrows=4, ncols=3, figsize=(15, 10))

    # Set common xlim and ylim for all plots
    common_xlim = (180, 310)
    common_ylim = (250, 380)

    # Loop through the subplots and plot the data
    for i, ax in enumerate(axes.flatten()):
        # Plot data without colorbar
        plot = ds.isel(time=range(i * 5, i * 5 + 5)).mean('time').plot(ax=ax, add_colorbar=False, vmin=vmin, vmax=vmax, cmap=cmaps[v])
        ax.set_axis_off()

        # Set xlim and ylim
        ax.set_xlim(common_xlim)
        ax.set_ylim(common_ylim)

        ax.set_title(f" {i+1}")

    # Add a single colorbar for all plots outside the loop
    cbar = fig.colorbar(plot, ax=axes, orientation='vertical', label=labels[v])

    fig.suptitle(var+' -  5 year Anomalies', fontsize=16)

    plt.savefig(os.path.expanduser('~/phase1_CONDA/results/')+var+'_5year_anomalies.png', bbox_inches='tight', dpi=300)
    
    
    print(var+' figure has been created')
    
    
print('this adventure is completed!')



