#!/usr/bin/env python3
# inagler 14/05/24

import pandas as pd
import xarray as xr
import pop_tools

# Define functions and variables
# load data
df = pd.read_csv('1_std_events_dens_spg.csv')
grouped = df.groupby('Index')
path = '/home/innag3580/phase1_CONDA/'

# set periods
before = 40*12
after = 20*12

# find file names 
def find_corresponding_file_name(vvel_number_to_find):
    with open(path+'timeseries/order.txt', 'r') as file:
        vvel_list = file.readlines()
    vvel_dict = {filename.split()[1]: int(filename.split()[0]) for filename in vvel_list}
    vvel_filename = None
    for filename in vvel_list:
        if vvel_dict[filename.split()[1]] == vvel_number_to_find:
            vvel_filename = filename.split()[1]  
            break
    return vvel_filename

# set up regional mask
grid_name = 'POP_gx1v7'
region_defs = {
    'North Atlantic and Nordic Seas': [{'match': {'REGION_MASK': [6, 7, 9]}, 
                             'bounds': {'TLAT': [20., 78.]}}],
    'LabradorSea': [{'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}]
} 
mask3d = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='North Atlantic and Nordic Seas')
mask3d = mask3d.sum('region')

var_path = ['temp/temp_', 'salt/salt_', 'vvel/vvel_']
save_name = ['1_std_temp','1_std_salt','1_std_vvel']

# Process data in chunks
def compute_composite_timeseries(datasets):
    var_years = []
    for t in range(60):
        var_year = []
        for ds_file in datasets:
            var_year.append(ds_file.isel(time=t))
        ds_comp = xr.concat(var_year, dim='file').mean(dim='file')
        var_years.append(ds_comp)
    composite_dataset = xr.concat(var_years, dim='time')
    return composite_dataset

for i in range(len(var_path)):
    
    iteration_count_below = 0
    iteration_count_above = 0
    datasets_below = []
    datasets_above = []
    print('')
    print('started: ', var_path[i][5:-1])
    
    for index, group_data in grouped:
        
        member = find_corresponding_file_name(index)[5:]
        file = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/' + var_path[i] + member
        ds_member = xr.open_dataset(file).where(mask3d == 1).roll(nlon=-100)
        print(member, ' started')
        
        for event, condition in zip(group_data['Values'], group_data['Condition']):
            
            event_time = event * 12
            period_start = event_time - before
            period_end = event_time + after
            time_slice = slice(period_start, period_end)
            
            try:
                ds_chunk = ds_member.isel(time=time_slice).resample(time='A').mean(dim='time')
                if condition == "Above":
                    datasets_above.append(ds_chunk)
                elif condition == "Below":
                    datasets_below.append(ds_chunk)
                ds_chunk.close()
            except ValueError as e:
                continue
            
            if len(datasets_below) >= 5:
                composite_dataset_below = compute_composite_timeseries(datasets_below)
                iteration_count_below += 1
                composite_dataset_below.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/' + save_name[i] + '_below_' + str(iteration_count_below) + '.nc')
                composite_dataset_below.close()
                datasets_below = []
                print('saved below chunk: ', iteration_count_below)
            if len(datasets_above) >= 5:
                composite_dataset_above = compute_composite_timeseries(datasets_above)
                iteration_count_above += 1
                composite_dataset_above.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/' + save_name[i] + '_above_' + str(iteration_count_above) + '.nc')
                composite_dataset_above.close()
                datasets_above = []
                print('saved above chunk: ', iteration_count_above)
                
        ds_member.close()

    # Process remaining data
    composite_dataset_below = compute_composite_timeseries(datasets_below)
    iteration_count_below += 1
    composite_dataset_below.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/' + save_name[i] + '_below_' + str(iteration_count_below) + '.nc')
    composite_dataset_below.close()
    datasets_below = []
    print('saved last below chunk')

    composite_dataset_above = compute_composite_timeseries(datasets_above)
    iteration_count_below += 1
    composite_dataset_above.to_netcdf('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/'  + save_name[i] + '_above_' + str(iteration_count_above) + '.nc')
    composite_dataset_above.close()
    datasets_above = []
    print('saved last above chunk')

print('process complete')    