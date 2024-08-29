#!/usr/bin/env python3
# inagler 31/07/24

import os
import re
import xarray as xr
import pop_tools  
import gsw
import numpy as np

# choose latitude
sel_nlat = 345

vvel_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/vvel'
temp_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/temp'
salt_dir = '/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/salt'

def extract_member_id(filename):
    match = re.search(r'vvel_([^.]+(?:\.\d+)?)\.nc', filename)
    return match.group(1) if match else None

t = 0
s = 1

for file in os.listdir(vvel_dir):
    if file.endswith('.nc'):
        member_id = extract_member_id(file)
        vvel_path = os.path.join(vvel_dir, file)
        temp_path = os.path.join(temp_dir, f'temp_{member_id}.nc')
        salt_path = os.path.join(salt_dir, f'salt_{member_id}.nc')
        
        # Check file existence and log accordingly
        missing_files = []
        if not os.path.exists(temp_path):
            t =+ 1
            print(f'temp {member_id} is missing')
        if not os.path.exists(salt_path):
            s =+ 1
            print(f'temp {member_id} is missing')

print('')
print(t, ' temp files missing')
print(s, ' salt files missing')