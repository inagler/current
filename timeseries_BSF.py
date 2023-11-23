#!/usr/bin/env python3
# inagler 11/09/23

### INITIALISATION ###

import numpy as np          # fundamental package for scientific computing
import xarray as xr         # data handling
import glob                 # return all file paths that match a specific pattern
import pop_tools            # to mask region of interest

path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/bsf/'
files = sorted(glob.glob(path + '*.nc'))

#setting up of regional mask
grid_name = 'POP_gx1v7'
region_defs = {
    'SubpolarAtlantic':[{'match':{'REGION_MASK':[6]}, 'bounds':{'TLAT':[35.0, 80.0],'TLONG':[280.0, 360.0]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [35.0, 66.0]}}]}
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='Subpolar Gyre')
mask3d = mask3d.sum('region')  

# prepare arrays and dictionaries to store files
len_time = 3012 # length of time series
time_series_min = np.zeros((len_time, len(files)))  # array for min bsf
time_series_east = np.zeros((len_time, len(files))) # array for osnap east
time_series_west = np.zeros((len_time, len(files))) # array for osnap west

# define start and end points of array 
point_OSNAP_west = (-55, 53)
point_OSNAP_center = (-44, 60)
point_OSNAP_east = (-7, 56)

print('initialisation complete')

def calculate_points_on_line(point1,point2,num):
    x1, y1 = point1
    x2, y2 = point2
    m = (y2 - y1)/(x2 - x1)
    b = y1 - (m * x1)
    x = np.linspace(x1, x2, num=num)
    y = m * x + b
    return x, y

def cross_section(ds, start_point, end_point, number_of_points):

    # Compute array of points on the line
    x, y = calculate_points_on_line(start_point, end_point, num=number_of_points)
    # prepare empty arra‚
    i_nlats = np.zeros(len(y))
    i_nlons = np.zeros(len(y))
    # retrieve numpy arrays from ds U coordinates
    ULAT = ds.ULAT.values
    ULONG = ds.ULONG.values
    for i in range(len(y)):
        target_ulat = y[i]
        target_ulong = (x[i] + 360) % 360
        # Calculate the absolute differences between the target values and ULAT, ULONG
        ulat_diff = np.abs(ULAT - target_ulat)
        ulong_diff = np.abs(ULONG - target_ulong)
        # Calculate the total difference
        total_diff = ulat_diff + ulong_diff
        # Find the indices of the minimum total difference
        min_index = np.unravel_index(np.nanargmin(total_diff), total_diff.shape)
        i_nlats[i] = min_index[0]
        i_nlons[i] = min_index[1]
    # Combine nlat and nlon arrays into a single array of tuples
    tuples = np.column_stack((i_nlats, i_nlons))
    # Find the unique tuples
    unique_tuples = np.unique(tuples, axis=0)
    # Separate the unique tuples back into nlat and nlon arrays
    unique_nlat = unique_tuples[:, 0]
    unique_nlon = unique_tuples[:, 1]
    # convert indices to integers (don't know why they aren't)
    nlats = unique_nlat.astype(int)
    nlons = unique_nlon.astype(int)
    return nlats, nlons

def create_BSF_index(ds, nlats, nlons):
    # compute crossection within BSF ds
    crossection_ds = ds.isel(nlon=nlons, nlat=nlats)
    # compute minimum of BSF on this index 
    index = crossection_ds.min(('nlon','nlat')).values
    return index

### COMPUTATION ###

# compute location cross section
ds = xr.open_dataset(files[0]).isel(time=0)
east_nlats, east_nlons = cross_section(ds, point_OSNAP_center, point_OSNAP_east, 60)
west_nlats, west_nlons = cross_section(ds, point_OSNAP_west, point_OSNAP_center, 40)

# loop through list of files
for i in range(len(files)):
    # read in files and apply mask
    ds = xr.open_dataset(files[i]).where(mask3d == 1)

    # find minimum of BSF in region per time step
    time_series_min[:,i] = ds.BSF.min(('nlon','nlat')).values # fi
    
    # compute min BSF at OSNAP for east and west section
    time_series_east[:,i] = create_BSF_index(ds.BSF, east_nlats, east_nlons)
    time_series_west[:,i] = create_BSF_index(ds.BSF, west_nlats, west_nlons)
    
    print('file ', str(i), '/', str(len(files)), ' executed')
    
print('computation finished')

### OUTPUT ###

# Save time series to a single file
np.save("timeseries/bsfu_mini_time_series.npy", time_series_min)
np.save("timeseries/osnp_east_time_series.npy", time_series_east)
np.save("timeseries/osnp_west_time_series.npy", time_series_west)

print('saving successful')