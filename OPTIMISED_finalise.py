#!/usr/bin/env python3
# inagler 29/05/24

import xarray as xr
import os
import gsw  

def process_files(file_pattern, output_filename):
    directory = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/'
    file_list = [os.path.join(directory, f) for f in os.listdir(directory) if file_pattern in f]
    datasets = [xr.open_dataset(f, chunks={'time': 1}) for f in file_list]
    print(f'{file_pattern} datasets loaded')

    combined = xr.concat(datasets, dim='file')
    print(f'{file_pattern} datasets combined')

    average = combined.mean(dim='file')
    print(f'{file_pattern} datasets averaged')

    average.to_netcdf(os.path.join(directory, output_filename))
    print(f'{file_pattern} dataset saved')
    
def compute_and_save_sigma(temp_file, salt_file, output_filename):
    path = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/'
    print('computation ',  output_filename, 'started')
    ds_temp = xr.open_dataset(os.path.join(path, temp_file))
    ds_salt = xr.open_dataset(os.path.join(path, salt_file))
    
    CT = gsw.conversions.CT_from_pt(ds_salt.SALT, ds_temp.TEMP)
    ds_sigma = xr.Dataset()
    ds_sigma['SIGMA'] = gsw.density.sigma2(ds_salt.SALT, CT)
    ds_sigma.to_netcdf(os.path.join(path, output_filename))

#process_files('1_std_temp_above', '1_std_TEMP_above.nc')
#process_files('1_std_temp_below', '1_std_TEMP_below.nc')

#process_files('1_std_salt_above', '1_std_SALT_above.nc')
#process_files('1_std_salt_below', '1_std_SALT_below.nc')

compute_and_save_sigma('1_std_TEMP_above.nc', '1_std_SALT_above.nc', '1_std_SIGMA_above.nc')
compute_and_save_sigma('1_std_TEMP_below.nc', '1_std_SALT_below.nc', '1_std_SIGMA_below.nc')

print('density check')

#process_files('1_std_taux_above', '1_std_TAUX_above.nc')
#process_files('1_std_tuax_below', '1_std_TAUX_below.nc')

#process_files('1_std_tauy_above', '1_std_TAUY_above.nc')
#process_files('1_std_tauy_below', '1_std_TAUY_below.nc')

#process_files('1_std_shf_above', '1_std_SHF_above.nc')
#process_files('1_std_shf_below', '1_std_SHF_below.nc')

