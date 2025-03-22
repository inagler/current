#!/usr/bin/env python3
# inagler 23/11/23

# Compute and visualize density and barotropic stream functions for 3 sigma events
# - Define density and latitude ranges
# - Calculate density overturning and barotropic stream function for selected variables
# - Generate subplots of 10-year averages for analysis
# - Save the resulting visualizations to disk

import numpy as np          # fundamental package for scientific computing
import xarray as xr         # data handling
import pop_tools            # to mask region of interest
import gsw                  # compute potential density
import matplotlib.pyplot as plt
import cmocean.cm as cmo
import os   

### INITIALISATION ###

sigma_level = [12., 16., 20., 24., 28., 28.5, 29.2, 29.4, 29.6, 29.8, 30., 30.2, 30.4, 30.6, 
               30.8, 31., 31.2, 31.4, 31.6, 31.8, 32., 32.2, 32.4, 32.6, 32.8, 33., 33.2, 33.4, 
               33.6, 33.8, 34., 34.2, 34.4, 34.6, 34.8, 35., 35.2, 35.4, 35.6, 35.8, 36.1, 36.2, 
               36.3, 36.4, 36.55, 36.6, 36.65, 36.7, 36.72, 36.74, 36.76, 36.78, 36.8, 36.82, 36.84, 
               36.86, 36.88, 36.9, 36.92, 36.94, 36.96, 36.98, 37., 37.02, 37.04, 37.06, 37.08, 37.1, 
               37.12, 37.14, 37.16, 37.18, 37.2, 37.25, 37.3, 37.35, 37.4, 37.45, 37.6, 37.7, 37.8, 
               37.9, 38., 39., 40., 41., 42.]

min_lat = 110
max_lat = 370

### FUNCTIONS ###

def density_MOC(ds):
    
    overturning = np.zeros([len(sigma_level), (max_lat - min_lat), period])
    
    for t in range(period):
        
        # select relevant time step of dataset
        ds_t = ds.isel(time=t)
        # prepare array

        for j in range(min_lat, max_lat):
            # prepare transport array
            sigma_transport = np.zeros(len(sigma_level))

            ### compute velocity transport
            v_transport = (ds_t.VVEL.isel(nlat=j) * ds_t.dz.isel(nlat=j) * ds_t.DXU.isel(nlat=j)).values

            ### get sigma values for selected cross section
            sigma_cross_section = ds_t.SIGMA.isel(nlat=j).values

            ### sum over longitudes per sigma bin
            for k in range(len(sigma_level) - 1):
                ind = np.where((sigma_cross_section >= sigma_level[k]) & (sigma_cross_section < sigma_level[k + 1]))
                sigma_transport[k] = np.nansum(v_transport[ind])

            ## compute overturning
            overturning[:, j - min_lat, t] = np.cumsum(sigma_transport)[::-1] #* 1e-6
            #overturning[:,j-min_lat, t] = overturning[:,j-min_lat, t][::-1]
        
    return overturning

def depth_MOC(ds):

    depth_range = slice(27, 51)
    
    ### compute overturning in depth space
    overturning_ds = (ds.VVEL * ds.dz * ds.DXU).sum(dim='nlon').cumsum(dim='z_t')
    overturning = overturning_ds.isel(z_t=depth_range, nlat=slice(min_lat,max_lat)).values

    return overturning

def BSF(ds, east_nlons, east_nlats, west_nlons, west_nlats):
    
    ## compute barotropic streamfunction
    bsf_ds = (ds.VVEL * ds.dz * ds.DXU).sum(dim='z_t').cumsum(dim='nlon')
    horz_transport = bsf_ds.values

    return horz_transport


### COMPUTATION ###

#for i in range(len(event_files)):
    # set beginning of period
    start = (events[i] * 12) - (before * 12)
    end = (events[i] * 12) + (after * 12)



    data = density_MOC(ds)
    overturning = np.flipud(data * 1e-12)
    
    levels = np.linspace(-40, 40, 41)
    min_lat, max_lat = 250, 370
    sigma_level = np.arange(30, 39)  

    # Create subplots for 6 periods of 10 years each
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    for i in range(6):
        row, col = divmod(i, 3)
        ax = axes[row, col]

        # Calculate the start and end months for each 10-year period
        start_month = i * 12
        end_month = start_month + 10*12

        # Calculate the 10-year average for the current period
        avg_over_10_years = np.mean(overturning[:, :, start_month:end_month], axis=2)

        # Create contour plot
        contour = ax.contourf(np.arange(min_lat, max_lat), sigma_level, avg_over_10_years, levels=levels, cmap='RdBu_r')

        ax.set_ylim([38, 30])
        ax.set_xlim([min_lat, max_lat])

        ax.set_ylabel(r'Potential Density [$\sigma_2, kg/m^3$]')
        ax.set_xlabel('POP2 Longitude')
        ax.set_title(f'10-Year Average: {(start*12)+start_month}-{(start*12)+end_month} ')

        cbar = plt.colorbar(contour, ax=ax, label='Circulation Strength [Sv]', extend='both')
        cbar.set_ticks([-40, -30, -20, -10, 0, 10, 20, 30, 40])

    # Adjust layout
    plt.tight_layout()

    plt.savefig(os.path.expanduser('~/phase1_CONDA/results/')+'density_streamfunctions_averages_'+event_files[i][:-3]+'.png', bbox_inches='tight')
    
    print('saved file: '+event_files[i][:-3])