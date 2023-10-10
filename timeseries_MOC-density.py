#!/usr/bin/env python3
# inagler 12/09/23

### INITIALISATION ###

import numpy as np          # fundamental package for scientific computing
import xarray as xr         # data handling
import glob                 # return all file paths that match a specific pattern
import os                   # provide operating system-related functions
import pop_tools            # to mask region of interest
import gsw                  # compute potential density

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/'
salt_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt/'
temp_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp/'
files = glob.glob(path + '*.nc')

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
intervall = 251 # to reduce compation time
dens_time_series_maxi = np.zeros((len_time, len(files)))  # array for min bsf
dens_time_series_rapi = np.zeros((len_time, len(files))) # array for rapid
dens_time_series_spgy = np.zeros((len_time, len(files))) # array for spg

#to prepare for parallel computing
num_parallel = [range(4, 5), range(5, 10), range(11, 15), range(18, 20), range(20, 25), range(25, 30), range(32, 35), range(39, 40),
               range(44, 45), range(45, 50), range(53, 55), range(55, 60), range(64, 65), range(68, 70), range(74, 75), range(79, len(files))]
#selecting run
l=10

# target sigam levels
sigma_level = [12. , 16. , 20. , 24. , 28. , 28.5 , 29.2 , 29.4 , 29.6 , 29.8 , 30. , 30.2 , 30.4 , 30.6 , 
               30.8 , 31. , 31.2 , 31.4 , 31.6 , 31.8 , 32. , 32.2 , 32.4 , 32.6 , 32.8 , 33. , 33.2 , 33.4 , 
               33.6 , 33.8 , 34. , 34.2 , 34.4 , 34.6 , 34.8 , 35. , 35.2 , 35.4 , 35.6 , 35.8 , 36.1 , 36.2 , 
               36.3 , 36.4 , 36.55, 36.6 , 36.65, 36.7 , 36.72, 36.74, 36.76, 36.78, 36.8 , 36.82, 36.84, 
               36.86, 36.88, 36.9 , 36.92, 36.94, 36.96, 36.98, 37. , 37.02, 37.04, 37.06, 37.08, 37.1 , 
               37.12, 37.14, 37.16, 37.18, 37.2 , 37.25, 37.3 , 37.35, 37.4 , 37.45, 37.6 , 37.7 , 37.8 , 
               37.9 , 38. , 39. , 40. , 41. , 42.]

print('initialisation complete')

def density_MOC(ds):

    # define range on pop-grid
    min_lat=110
    max_lat=370
    
    # prepare array
    maxi = np.zeros(intervall)
    rapi = np.zeros(intervall)
    spgy = np.zeros(intervall)
    
    for t in range(intervall):
        
        # select relevant time step of dataset
        ds_t = ds.isel(time=t)
        # prepare array
        overturning = np.zeros([len(sigma_level), (max_lat-min_lat)])

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
            overturning[:,j-min_lat] = np.cumsum(sigma_transport)[::-1] #* 1e-6
            overturning[:,j-min_lat] = overturning[:,j-min_lat][::-1]
        
        # compute maximum time series of time step
        maxi[t] = np.max(overturning)
        # compute RAPID time series of time step
        rapi[t] = np.max(overturning[:,274-min_lat])
        # compute RAPID time series of time step
        spgy[t] = np.max(overturning[:,345-min_lat])
    
    return maxi, rapi, spgy

### COMPUTATION ###

# loop through list of files
for i in num_parallel[l]:

    salt = salt_path + 'salt_' + files[i][-11:]
    temp = temp_path + 'temp_' + files[i][-11:]
    
    print(salt)
    print(temp)
    
    if os.path.exists(salt) and os.path.exists(temp):
        
        print('file ', str(i), '/', str(len(files)), ' exists')
    
        # read in file abnd apply mask
        ds = xr.open_dataset(files[i])
        
        #print('file ', str(i), '/', str(len(files)), ' loaded')


        # load salt data set
        ds_salt = xr.open_dataset(salt)
        #print('salt loaded')
        # load temp data set
        ds_temp = xr.open_dataset(temp)
        #print('temp loaded')

        # add salt and temp to ds
        ds.update(ds_salt[["SALT"]])
        ds.update(ds_temp[["TEMP"]])
        
        #print('salt and temp added')
        
        k=0
        for j in range(12):
            
            time = slice(k,k+intervall)

            ds_int = ds.isel(time=time).where(mask3d == 1)
            
            ### compute potential density
            # Conservative Temperature
            CT = gsw.conversions.CT_from_pt(ds_int.SALT, ds_int.TEMP)
            # Potential density
            ds_int['SIGMA'] = gsw.density.sigma2(ds_int.SALT, CT)
            #ds['SIGMA'].attrs['units'] = 'kg/m^3 - 1000'

            #print('potential density computed')

            maxi, rapi, spgy = density_MOC(ds_int)
            
            dens_time_series_maxi[k:k+intervall,i], dens_time_series_rapi[k:k+intervall,i], dens_time_series_spgy[k:k+intervall,i] = maxi, rapi, spgy
        
            k = k + intervall
        
            print('part ', str(j+1), '/12 computed')
            
            
            np.save("timeseries/save_parts/maxi_dens_time_series_"+str(i)+"_part_"+str(j)+".npy", dens_time_series_maxi[k:k+intervall,i])
            np.save("timeseries/save_parts/rapi_dens_time_series_"+str(i)+"_part_"+str(j)+".npy", dens_time_series_rapi[k:k+intervall,i])
            np.save("timeseries/save_parts/spgy_dens_time_series_"+str(i)+"_part_"+str(j)+".npy", dens_time_series_spgy[k:k+intervall,i])
            
            print('part ', str(j+1), '/12 saved')


        print('file ', str(i), '/', str(len(files)), ' executed')
        
        np.save("timeseries/maxi_dens_time_series_"+str(i)+".npy", dens_time_series_maxi[:,i])
        np.save("timeseries/rapi_dens_time_series_"+str(i)+".npy", dens_time_series_rapi[:,i])
        np.save("timeseries/spgy_dens_time_series_"+str(i)+".npy", dens_time_series_spgy[:,i])
        
        print('------ file ', str(i), '/', str(len(files)), ' saved ------')
        
    else:
        print('------ file ', str(i), '/', str(len(files)), ' does not exist ------')
    
print('computation finished')

### OUTPUT ###

# Save time series to a single file
#np.save("timeseries/maxi_dens_time_series.npy", dens_time_series_maxi)
#np.save("timeseries/rapi_dens_time_series.npy", dens_time_series_rapi)
#np.save("timeseries/spgy_dens_time_series.npy", dens_time_series_spgy)

print('saving successful')
