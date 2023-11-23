#!/usr/bin/env python3
# inagler 12/09/23


### INITIALISATION ###

import numpy as np          # fundamental package for scientific computing
import xarray as xr         # data handling
import pop_tools            # to mask region of interest
import gsw                  # compute potential density
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PIL import Image

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
salt_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt/'
temp_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp/'

file = path + 'vvel_1281.012.nc'

grid_name = 'POP_gx1v7'

#setting up of regional mask
region_defs = {
    'NorthAtlantic':[{'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [-20.0, 66.0]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}],
    'MediterraneanSea': [{'match': {'REGION_MASK': [7]}}]} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic')
mask3d = mask3d.sum('region')

# prepare arrays and dictionaries to store files
start = (68 - 30)*12
end = (90 - 20)*12
len_time = end-start # length of time series

# target sigam levels
sigma_level = [12. , 16. , 20. , 24. , 28. , 28.5 , 29.2 , 29.4 , 29.6 , 29.8 , 30. , 30.2 , 30.4 , 30.6 , 
               30.8 , 31. , 31.2 , 31.4 , 31.6 , 31.8 , 32. , 32.2 , 32.4 , 32.6 , 32.8 , 33. , 33.2 , 33.4 , 
               33.6 , 33.8 , 34. , 34.2 , 34.4 , 34.6 , 34.8 , 35. , 35.2 , 35.4 , 35.6 , 35.8 , 36.1 , 36.2 , 
               36.3 , 36.4 , 36.55, 36.6 , 36.65, 36.7 , 36.72, 36.74, 36.76, 36.78, 36.8 , 36.82, 36.84, 
               36.86, 36.88, 36.9 , 36.92, 36.94, 36.96, 36.98, 37. , 37.02, 37.04, 37.06, 37.08, 37.1 , 
               37.12, 37.14, 37.16, 37.18, 37.2 , 37.25, 37.3 , 37.35, 37.4 , 37.45, 37.6 , 37.7, 37.8 , 
               37.9 , 38. , 39. , 40. , 41. , 42.]



print('initialisation complete')


### PREPARATION

def density_MOC(ds):

    # define range on pop-grid
    min_lat=110
    max_lat=370
    
    overturning = np.zeros([len(sigma_level), (max_lat-min_lat), len_time])
    
    for t in range(len_time):
        
        # select relevant time step of dataset
        ds_t = ds.isel(time=t)
        # prepare array

        for j in range(min_lat,max_lat):
            # prepare transport array
            sigma_transport = np.zeros(len(sigma_level))

            ### compute velocity transport
            v_transport = (ds_t.VVEL.isel(nlat=j) * ds_t.dz.isel(nlat=j) * ds_t.DXU.isel(nlat=j)).values

            ### get sigma vlaues for selected cross section
            sigma_crossection = ds_t.SIGMA.isel(nlat=j).values

            ### sum over longitudes per sigm bin
            for i in range(len(sigma_level)-1):
                ind = np.where((sigma_crossection >= sigma_level[i]) & (sigma_crossection < sigma_level[i+1]))
                sigma_transport[i] = np.nansum(v_transport[ind])

            ## compute overturning
            overturning[:,j-min_lat, t] = np.cumsum(sigma_transport)[::-1] #* 1e-6
            #overturning[:,j-min_lat, t] = overturning[:,j-min_lat, t][::-1]
        
    return overturning



### COMPUTATION ###

salt = salt_path + 'salt_' + file[-11:]
temp = temp_path + 'temp_' + file[-11:]

# read in file abnd apply mask
ds = xr.open_dataset(file).isel(time=slice(start,end)).where(mask3d == 1)
# load salt data set
ds_salt = xr.open_dataset(salt).isel(time=slice(start,end)).where(mask3d == 1)
# load temp data set
ds_temp = xr.open_dataset(temp).isel(time=slice(start,end)).where(mask3d == 1)
    
# add salt and temp to ds
ds.update(ds_salt[["SALT"]])
ds.update(ds_temp[["TEMP"]])

### compute potential density
# Conservative Temperature
CT = gsw.conversions.CT_from_pt(ds.SALT, ds.TEMP)
# Potential density
ds['SIGMA'] = gsw.density.sigma2(ds.SALT, CT)

data = overturning

fig, ax = plt.subplots()
img = ax.imshow(data[:, :, 0], cmap='viridis')  # Display the first frame

def update(frame):
    img.set_array(data[:, :, frame])  # Update the displayed frame
    return img,

ani = FuncAnimation(fig, update, frames=range(len_time), blit=True)

# Save the animation as a file (e.g., animation.gif)
ani.save('animation.gif', writer='pillow', fps=10)  # Change the filename and format as needed