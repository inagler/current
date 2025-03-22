import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import animation, gridspec
import numpy as np
import xarray as xr
import cmocean.cm as cmo
import os

# Animate Barotropic Streamfunction (BSF), Depth-Integrated Meridional Overturning Circulation (dMOC),
# and Density Overturning Circulation (sMOC) for CESM2 LENS2 data
# - Compute anomalies and visualize time-dependent composites
# - Create and save animations

print('start BSF')

cmap = cmo.balance

time_dependent_fields = xr.open_dataarray('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/BSFcomposite.nc')

def plot_var_frame(time_step):
    data = ds.isel(time=start + time_step)
    ax1.cla()
    im = ax1.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax) 
    contour = ax1.contour(data, colors='k')
    ax1.clabel(contour, inline=True, fontsize=8)

    ax1.set_xlim([170, 310])
    ax1.set_ylim([250, 382])
        
    ax1.set_title(f'BSF composite - year:{time_step}')

#ds = time_dependent_fields
ds = time_dependent_fields - time_dependent_fields.isel(time=0)

vmin, vmax = -abs(ds).max(), abs(ds).max()
start = 0

# create figure and set up layout of subplots
fig = plt.figure(figsize=(12, 6))
gs = gridspec.GridSpec(1, 2, width_ratios=[13, 1])

# main subplot for animation
ax1 = plt.subplot(gs[0])

# colorbar subplot 
cax = plt.subplot(gs[1])
num_time_steps = len(ds.time)
ani = animation.FuncAnimation(fig, plot_var_frame, frames=num_time_steps, interval=800)

# set colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = plt.colorbar(sm, cax=cax)
cbar.set_label('Horizontal Transport $BSF$ [Sverdrup]')

# Save animation
#ani.save(os.path.expanduser('~/phase1_CONDA/results/') + 'annual_BSF.gif', writer='pillow', fps=3)
ani.save(os.path.expanduser('~/phase1_CONDA/results/') + 'annual_anomaly_BSF.gif', writer='pillow', fps=3)

print('BSF completed')
print('')
print('start dMOC')

time_dependent_fields = xr.open_dataarray('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/dMOCcomposite.nc')

def plot_var_frame(time_step):
    data = ds.isel(time=start + time_step)
    ax1.cla()
    im = data.plot(ax=ax1, cmap=cmap, yincrease = False, add_colorbar=False, vmin=vmin, vmax=vmax)
    contour = data.plot.contour(ax=ax1, colors='k', yincrease = False, levels=19, add_colorbar=False) 
    ax1.clabel(contour, inline=True, fontsize=10)
    ax1.set_xlim([260, 360])
    ax1.set_ylim([350000, 0])

    current_y_ticks = ax1.get_yticks()
    new_y_ticks = np.array(current_y_ticks)[::2] 
    new_y_tick_labels = ['{:g}'.format(float(tick) * 1e-2) for tick in new_y_ticks]
    ax1.set_yticks(new_y_ticks)
    ax1.set_yticklabels(new_y_tick_labels)
    
    ax1.set_ylabel(r'Depth $d$ [$m$]')
    ax1.set_xlabel('POP2 Latitudes')
    
    ax1.set_title(f'dMOC composite - year:{time_step}')
    
#ds = time_dependent_fields
ds = time_dependent_fields - time_dependent_fields.isel(time=0)

vmin, vmax = -abs(ds).max(), abs(ds).max()
start = 0

# create figure and set up layout of subplots
fig = plt.figure(figsize=(10, 10))
gs = gridspec.GridSpec(1, 2, width_ratios=[13, 1])

# create figure and set up layout of subplots
fig = plt.figure(figsize=(12, 8))

# main subplot for animation
ax1 = plt.subplot(gs[0])

# colorbar subplot 
cax = plt.subplot(gs[1])
num_time_steps = len(ds.time)
ani = animation.FuncAnimation(fig, plot_var_frame, frames=num_time_steps, interval=800)

# set colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = plt.colorbar(sm, cax=cax)
cbar.set_label(r'Depth Streamfunction $dMOC$ [Sverdrup]', )

# Save animation
#ani.save(os.path.expanduser('~/phase1_CONDA/results/') + 'annual_dMOC.gif', writer='pillow', fps=3)
ani.save(os.path.expanduser('~/phase1_CONDA/results/') + 'annual_anomaly_dMOC.gif', writer='pillow', fps=3)

print('dMOC completed')
print('')
print('start sMOC')

time_dependent_fields = xr.open_dataarray('/Data/gfi/share/ModData/CESM2_LENS2/ocean/monthly/comp/sMOCcomposite.nc')

def plot_var_frame(time_step):
    data = ds.isel(time=start + time_step)
    ax1.cla()
    im = data.plot(ax=ax1, cmap=cmap, yincrease = False, add_colorbar=False, vmin=vmin, vmax=vmax)
    contour = data.plot.contour(ax=ax1, colors='k', yincrease = False, levels=19, add_colorbar=False) 
    ax1.clabel(contour, inline=True, fontsize=14)

    ax1.set_xlim([260, 360])
    ax1.set_ylim([37, 35])
    
    ax1.set_ylabel(r'Potential Density $\sigma_2$ [g/kg - 1000]')
    ax1.set_xlabel('POP2 Latitudes')
    
    ax1.set_title(f'sMOC composite- year:{time_step}')
    
#ds = time_dependent_fields
ds = time_dependent_fields - time_dependent_fields.isel(time=0)

vmin, vmax = -abs(ds).max(), abs(ds).max()
start = 0

# create figure and set up layout of subplots
fig = plt.figure(figsize=(10, 10))
gs = gridspec.GridSpec(1, 2, width_ratios=[13, 1])

# create figure and set up layout of subplots
fig = plt.figure(figsize=(12, 8))

# main subplot for animation
ax1 = plt.subplot(gs[0])

# colorbar subplot 
cax = plt.subplot(gs[1])
num_time_steps = len(ds.time)
ani = animation.FuncAnimation(fig, plot_var_frame, frames=num_time_steps, interval=800)

# set colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
sm.set_array([])
cbar = plt.colorbar(sm, cax=cax)
cbar.set_label(r'Density Streamfunction $\Delta \sigma_2 MOC$ [Sverdrup]')

# Save animation
#ani.save(os.path.expanduser('~/phase1_CONDA/results/') + 'annual_sMOC.gif', writer='pillow', fps=3)
ani.save(os.path.expanduser('~/phase1_CONDA/results/') + 'annual_anomaly_sMOC.gif', writer='pillow', fps=3)

print('sMOC completed')