#!/usr/bin/env python3
# inagler 25/06/24

import xarray as xr
import pop_tools  # Ensure pop_tools is installed

def get_longitude_bounds(mask, nlat):
    """
    Extracts the longitude bounds for a specified latitude from a given mask.
    
    Parameters:
    - mask (xarray.DataArray): The mask data array from which to extract longitude bounds.
    - nlat (int): The latitude index to inspect within the mask.
    
    Returns:
    - tuple: A tuple containing the minimum and maximum longitudes where the mask is active.
    """
    # Check at the specified latitude index where the mask is non-zero (active)
    longitude_indices = mask.isel(nlat=nlat).where(mask.isel(nlat=nlat) != 0, drop=True).nlon

    if longitude_indices.size == 0:
        return (None, None)  # or some indication that no valid range exists at this latitude
    
    min_lon = longitude_indices.min().values.item()
    max_lon = longitude_indices.max().values.item()
    
    return (min_lon, max_lon)

# Example usage:
grid_name = 'POP_gx1v7'
region_defs = {
    'SubpolarAtlantic': [
        {'match': {'REGION_MASK': [6]}, 'bounds': {'TLAT': [15.0, 66.0], 'TLONG': [260.0, 360.0]}}
    ],
    'LabradorSea': [
        {'match': {'REGION_MASK': [8]}, 'bounds': {'TLAT': [45.0, 66.0]}}
    ]
}

# Create the mask using pop_tools
maskBSF = pop_tools.region_mask_3d(grid_name, region_defs=region_defs, mask_name='Subpolar Gyre')
maskBSF = maskBSF.sum('region')
# Take into account NA being at nlon=0
maskBSF = maskBSF.roll(nlon=-100, roll_coords=True)  

# Specify the latitude index (nlat) as needed
nlat_index = 345  # Example index, adjust as necessary

# Get the longitude bounds for the specific latitude index
longitude_bounds = get_longitude_bounds(maskBSF, nlat_index)

print(f"Longitude bounds at latitude index {nlat_index}: {longitude_bounds}")