#!/usr/bin/env python3
# inagler 06/08/24

import os
import re
import gc

import numpy as np
import pandas as pd
import xarray as xr

import cftime
import pop_tools  

# Define configurations and paths
data_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/psl'
output_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/all_member_timeseries'

def compute_NAO(ds):

    data = ds['PSL'].values
    weights = ds.gw.values
    weights = weights[np.newaxis, :,  np.newaxis]

    weighted_data = data * weights
    shape = weighted_data.shape
    data_2d = weighted_data.reshape(shape[0], -1)

    mean_per_time_step = np.nanmean(data_2d, axis=1)
    nan_indices = np.isnan(data_2d)
    data_2d[nan_indices] = np.take(mean_per_time_step, np.where(nan_indices)[0])

    mean = np.mean(data_2d, axis=0)
    centered_data = data_2d - mean

    cov_matrix = np.cov(centered_data, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, sorted_indices]

    first_principal_component = np.dot(centered_data, eigenvectors[:, 0])
    first_principal_component = first_principal_component[:-1]
    second_principal_component = np.dot(centered_data, eigenvectors[:, 1])
    second_principal_component = second_principal_component[:-1]

    row_start1, row_end1 = 35, 45
    col_start1, col_end1 = 40, 55
    eof1 = eigenvectors[:, 0].reshape(ds.dims['lat'], ds.dims['lon'])
    if np.mean(eof1[row_start1:row_end1+1, col_start1:col_end1+1]) < 0:
        first_principal_component = -first_principal_component
    eof2 = eigenvectors[:, 1].reshape(ds.dims['lat'], ds.dims['lon'])
    if np.mean(eof2[row_start1:row_end1+1, col_start1:col_end1+1]) < 0:
        second_principal_component = -second_principal_component

    return first_principal_component, second_principal_component

def calculate_moving_average(standardised_pcs, window_size):
    moving_averages = []
    pad_width = (window_size - 1) // 2
    for pcs in standardised_pcs:
        moving_avg = np.convolve(pcs, np.ones(window_size) / window_size, mode='valid')
        pad_valid = len(pcs) - len(moving_avg)
        pad_before = pad_width
        pad_after = pad_valid - pad_before
        padded_moving_avg = np.pad(moving_avg, (pad_before, pad_after), mode='constant', constant_values=np.nan)
        moving_averages.append(padded_moving_avg)
    return moving_averages

def extract_member_id(filename):
    match = re.search(r'psl_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

def pad_with_nan(array, target_length):
    if len(array) < target_length:
        padding = np.full(target_length - len(array), np.nan)
        return np.concatenate([array, padding])
    return array

all_first_pcs = []
all_second_pcs = []

# computing NAO and EAP
for file in sorted(os.listdir(data_dir)):
    
    member_id = extract_member_id(file)
    file_path = os.path.join(data_dir, file)
    
    ds = xr.open_dataset(file_path).roll(lon=-30).isel(lat=slice(120, 180), lon=slice(215-30, 288))
    first_pc, second_pc = compute_NAO(ds)
    
    all_first_pcs.append(first_pc)
    all_second_pcs.append(second_pc)
    ds.close()

# computing statistics
combined_first_pcs = np.concatenate(all_first_pcs)
mean_nao = np.mean(combined_first_pcs)
std_nao = np.std(combined_first_pcs)

combined_second_pcs = np.concatenate(all_second_pcs)
mean_eap = np.mean(combined_second_pcs)
std_eap = np.std(combined_second_pcs)

normalised_first_pcs = []
normalised_second_pcs = []

for nao, eap in zip(all_first_pcs, all_second_pcs):
    normalised_nao = (nao - mean_nao) / std_nao
    normalised_eap = (eap - mean_eap) / std_eap

    normalised_first_pcs.append(normalised_nao)
    normalised_second_pcs.append(normalised_eap)

# integrate patterns
window_size = 10 * 12
nao_int = calculate_moving_average(normalised_first_pcs, window_size)
eap_int = calculate_moving_average(normalised_second_pcs, window_size)

for idx, (file, norm_nao, norm_eap, avg_nao, avg_eap) in enumerate(zip(sorted(os.listdir(data_dir)), normalised_first_pcs, normalised_second_pcs, nao_int, eap_int)):
    
    member_id = extract_member_id(file)
    file_path = os.path.join(data_dir, file)

    ds = xr.open_dataset(file_path, decode_times=False)
    if isinstance(ds.time.values[0], cftime._cftime.DatetimeNoLeap):
        ds['time'] = xr.DataArray(np.array([pd.Timestamp(str(dt)).to_datetime64() for dt in ds.time.values]),
                                  dims='time')
    time_coord = ds.coords['time']
    ds.close()

    # Pad norm_nao and norm_eap to match the length of time_coord
    norm_nao_padded = pad_with_nan(norm_nao, len(time_coord))
    norm_eap_padded = pad_with_nan(norm_eap, len(time_coord))
    avg_nao_padded = pad_with_nan(avg_nao, len(time_coord))
    avg_eap_padded = pad_with_nan(avg_eap, len(time_coord))

    normalized_dataset = xr.Dataset({
        'normalized_nao': (['time'], norm_nao_padded),
        'normalized_eap': (['time'], norm_eap_padded)
    }, coords={'time': time_coord})
    normalized_dataset.to_netcdf(os.path.join(output_dir, f'norm_monthly_psl_pattern_{member_id}.nc'))

    integrated_dataset = xr.Dataset({
        'integrated_nao': (['time'], avg_nao_padded),
        'integrated_eap': (['time'], avg_eap_padded)
    }, coords={'time': time_coord})
    integrated_dataset.to_netcdf(os.path.join(output_dir, f'int_monthly_psl_pattern_{member_id}.nc'))

    print(f'{member_id} saved')

print('')
print('computation complete')
print('')