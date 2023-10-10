#!/usr/bin/env python3
# inagler 05/09/23

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import pop_tools
import xgcm
from xgcm import Grid

# file name meridional velocity
vvel_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel/vvel_'
# file name salt
salt_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt/salt_'
# file name temp
temp_path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp/temp_'

members = ['1001.001.nc','1231.001.nc','1231.002.nc','1231.003.nc','1231.004.nc','1231.005.nc','1231.006.nc','1231.007.nc','1231.008.nc','1231.009.nc','1231.010.nc',
           '1231.011.nc','1231.012.nc','1231.013.nc','1231.014.nc','1231.015.nc','1231.016.nc','1231.017.nc','1231.018.nc','1231.019.nc','1231.020.nc'] 

period = [slice(0, 11), slice(100, 111), slice(0,100)]

## setting up of regional mask
grid_name = 'POP_gx1v7'
region_defs = {
    'NorthAtlantic':[
        {'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [-20.0, 66.0]}}   
    ],
    'LabradorSea': [
        {'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}        
    ],
    'MediterraneanSea': [
        {'match': {'REGION_MASK': [7]}} 
    ]} 
mask3d = pop_tools.region_mask_3d(grid_name, 
                                  region_defs=region_defs, 
                                  mask_name='North Atlantic')
mask3d = mask3d.sum('region')  
 
    
for i in range(len(members)):
    for j in range(len(period)):
    
        # load density data set
        ds = xr.open_dataset(vvel_path+members[i])
        # load salt data set
        ds_salt = xr.open_dataset(salt_path+members[i])
        # load temp data set
        ds_temp = xr.open_dataset(temp_path+members[i])

        # add salt and temp to ds
        ds.update(ds_salt[["SALT"]])
        ds.update(ds_temp[["TEMP"]])

        # select one time step and apply mask shift data 
        # by 80 longitudinal degrees (POP-units)
        ds = ds.isel(time=period[j]).mean(dim='time').where(mask3d == 1).roll(nlon=-80)

        # conput in situ density
        ds["RHO"] = pop_tools.eos(ds.SALT, ds.TEMP, depth=ds.z_t * 1e-2)

        ### Update units to SI units
        # Convert the units and update the data variable 'RHO' and 'VVEL'
        ds['RHO'] = ds.RHO - 1000
        ds['VVEL'] = ds.VVEL *1e-2
        ds['dz'] = ds.dz *1e-2
        ds['z_t'] = ds.z_t *1e-2
        ds['z_w_top'] = ds.z_w_top *1e-2
        ds['z_w_bot'] = ds.z_w_bot *1e-2
        ds['DXU'] = ds.DXU *1e-2

        # Update the attribute for the new units
        ds['RHO'].attrs['units'] = 'kg/m^3 - 1000'
        ds['VVEL'].attrs['units'] = 'm/s'
        ds['dz'].attrs['units'] = 'm'
        ds['z_t'].attrs['units'] = 'm'
        ds['z_w_top'].attrs['units'] = 'm'
        ds['z_w_bot'].attrs['units'] = 'm'
        ds['DXU'].attrs['units'] = 'm'


        ## Computation

        ## transform velocity
        # Construct an outer grid coordinate from z bounds
        z_t_outer = np.hstack([ds.z_w_top.values, ds.z_w_bot.values[-1]])
        ds['z_t_outer'] = (('z_t_outer',), z_t_outer)
        # make the POP dataset xgcm compatible
        ini_grid, xds = pop_tools.to_xgcm_grid_dataset(ds, periodic=False)
        # create grid containing z_t_outer
        grid = Grid(xds, coords={'Z': {'center': 'z_t', 'outer': 'z_t_outer'},
                                 'X': {'center': 'nlon_t', 'right': 'nlon_u'},
                                 'Y': {'center': 'nlat_t', 'right': 'nlat_u'},
                                },
                    periodic=False,)
        # define specific sigma levels onto which we want to interpolate the data
        target_sigma_levels = np.arange(20, 42, 0.01)
        # perform transform
        vvel_sigma = grid.transform(ds.VVEL, 'Z', target_sigma_levels, target_data=ds.RHO)

        ### manually transform dz
        # expand z_t to 3D grid and creaet xr array
        z_t_3D = np.moveaxis(np.tile(ds.z_t,[384,320,1]),2,0)
        ds['z_t_3D'] = xr.DataArray(z_t_3D, dims=['z_t', 'nlat', 'nlon'])
        ## transform z_t to density coordinates
        z_t_sigma = grid.transform(ds.z_t_3D, 'Z', target_sigma_levels, target_data=ds.RHO)
        ## compute dz(rho) from transfomed z_t by substracting layers
        z_sigma = z_t_sigma.values
        dz_sigma_manual = np.empty_like(z_sigma)
        dz_sigma_manual[:,:,0:-1] = z_sigma[:,:,1:]-z_sigma[:,:,0:-1]
        dz_sigma_manual[:,:,-1] = dz_sigma_manual[:,:,-1]
        # create xr array from dz(rho)
        dz_sigma_manual = xr.DataArray(dz_sigma_manual, dims=['nlat', 'nlon','RHO'])
        # Combine the original DataArray and the new variable into a dataset
        ds_sigma = xr.Dataset({'vvel': vvel_sigma, 'dz_manual':dz_sigma_manual})

        ### OVERTURNING
        ### set X spacing
        dx = ds.DXU ### only works when taken from `ds` Dataset

        ### compute overturning in density space
        overturning = (ds_sigma.vvel * ds_sigma.dz_manual * dx).sum(dim='nlon').cumsum(dim='RHO') * 1e-6
        overturning = overturning.transpose('RHO', 'nlat')

        ### compute overturning in depth space
        overturning_depth = (xds.VVEL * xds.dz * dx).sum(dim='nlon').cumsum(dim='z_t') * 1e-6


        ## Output

        fig = plt.figure(figsize=(20,8))
        contourf_plot = overturning.plot.contourf(levels=31, cmap='RdBu_r', yincrease=False)#, vmax=30, vmin=-30)
        plt.xlim(240, 370)  
        contour_plot = plt.contour(overturning.nlat, overturning.RHO,
                                   overturning, levels=31, colors='black', linewidths=0.5)
        plt.title('Density space MOC period '+str(period[j])+'\n member: '+members[i])
        plt.grid()
        plt.savefig('results/density_transform_'+members[i]+str(period[j])+'.png', bbox_inches='tight')
        plt.close()