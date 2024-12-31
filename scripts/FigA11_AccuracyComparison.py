# import packages
import pandas as pd
from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import tools


def map_to_group(value):
    for group, items in source_groups.items():
        if value in items:
            return group
    return np.nan  # If no match, return NaN


# ..........................
# load the tables
datasets, accuracy = tools.load_dataset(subset=['datasets', 'accuracy']).values()

accuracy.dropna(subset=['Accuracy comparison data [m] Z'], inplace=True)

accuracy = accuracy[['DatasetKey', 'Comparison data simplified',
                     'Comparison source group', 'Accuracy comparison data [m] Z']].copy()
datasets = datasets[['Key', 'Type']].copy()

# merge on dataset names
merged = accuracy.merge(datasets, left_on='DatasetKey', right_on='Key').drop(columns=['Key'])
merged.rename(columns={'DatasetKey': 'Key', 'Comparison data simplified': 'comparison',
                       'Comparison source group': 'source_group',
                       'Accuracy comparison data [m] Z': 'accuracy'}, inplace=True)

# remove terrestrial datasets
merged.drop(merged.loc[merged['Type'] == 'Terrestrial'].index, inplace=True)

# map comparison data to a category
source_groups = {
    'very_high_resolution_terrestrial': ['TLS-DEM', 'CPs-dGPS', 'GCPs-dGPS'],
    'very_high_resolution_airborne': ['ALS-DEM', 'Aerial orthoimage, ALS-DEM', 'UAV-DEM', 'Aerial orthoimage',
                                      'Aerial images-DEM', 'TLS-DEM', 'ALS-points'],
    'very_high_resolution_satellite': ['SatelliteDEM-WorldView', 'SatelliteDEM-Pleiades'],
    'high_resolution_satellite': ['SatelliteDEM-SPOT6', 'SatelliteDEM-SPOT5', 'GCPs-Cartosat'],
    'medium_resolution_satellite': ['SatelliteDEM-ASTER', 'SatelliteDEM-REMA', 'SatelliteDEM-Cartosat',
                                    'SatelliteDEM-HMA', 'SatelliteDEM-ALOS', 'SatelliteDEM-TanDEM-X',
                                    'SatelliteDEM-SRTM, ICESat', 'SatelliteDEM-AW3D30', 'SatelliteDEM-SRTM, ARTICDEM',
                                    'SatelliteDEM-SRTM', 'Landsat, SatelliteDEM-SRTM'],
    'altimetry': ['ICESat'],
    'historical_images': ['Historical images-point cloud', 'Historical images-DEM'],
    'topographic_maps': ['GCPs-Topographic maps', 'Topographic maps', 'CPs-Topographic maps'],
    'generic_GCPs_CPs': ['GCPs, CPs', 'GCPs', 'CPs'],
    'generic_DEM_orthophoto': ['DEM', 'Orthophoto']
}

# map source data to groups
merged['group'] = merged['comparison'].apply(map_to_group)

# define the order of the groups
order = [
    'very_high_resolution_terrestrial',
    'very_high_resolution_airborne',
    'very_high_resolution_satellite',
    'high_resolution_satellite',
    'medium_resolution_satellite',
    'altimetry',
    'historical_images',
    'topographic_maps',
    'generic_GCPs_CPs',
    'generic_DEM_orthophoto']

merged['group'] = pd.Categorical(merged['group'], categories=order, ordered=True)

# split into aerial, satellite
(_, aerial), (_, satellite) = merged.groupby('Type')

# ======================================================================================================================
#                           PLOT THE ACCURACY OF THE COMPARISON DATA
# Define the order of the 'Comparison_data_group' categories
bins = {}
bins['aerial'] = np.arange(0, aerial['accuracy'].max() + 0.2, 0.2)
bins['satellite'] = np.arange(0, satellite['accuracy'].max() + 1, 1)

# --- Create subplots
# Define the color mapping for each 'Comparison_data_group' category
color_mapping_source = {
    'very_high_resolution_terrestrial': '#9e0142',
    'very_high_resolution_airborne': '#d53e4f',
    'very_high_resolution_satellite': '#f46d43',
    'high_resolution_satellite': '#fdae61',
    'medium_resolution_satellite': '#fee08b',
    'altimetry': '#e6f598',
    'historical_images': '#abdda4',
    'topographic_maps': '#66c2a5',
    'generic_GCPs_CPs': '#3288bd',
    'generic_DEM_orthophoto': '#5e4fa2'
}

alpha_value = 0.8

# Set seaborn style
sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, ax = plt.subplots(1, 1, figsize=(15, 10))
axs = fig.subplots(2, 2)

widths = dict(zip(['aerial', 'aerial', 'satellite', 'satellite'], [0.2, 0.2, 1, 1]))

for (data, key, ctype, _ax) in zip([aerial, aerial, satellite, satellite],
                                   ['aerial', 'aerial', 'satellite', 'satellite'],
                                   ['point-based', 'area-based', 'point-based', 'area-based'],
                                   axs.flatten()):
    tools.plot_stacked_histogram(data[data['source_group'] == ctype],
                                 _ax, bins[key],
                                 'group',
                                 'accuracy',
                                 color_mapping_source,
                                 width_value=widths[key])

ax1, ax2, ax3, ax4 = axs.flatten()
ax2.legend(loc='upper right')

ax1.set_ylim(0, 40)
ax2.set_ylim(0, 40)
ax3.set_ylim(0, 5)
ax4.set_ylim(0, 5)

# set the xticks to be every 1 for the aerial panels
ax1.set_xticks(range(0, 7))
ax2.set_xticks(range(0, 7))

# add panel labels
ax1.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.05), xycoords='axes fraction')
ax3.annotate('c)', (0, 1.05), xycoords='axes fraction')
ax4.annotate('d)', (0, 1.05), xycoords='axes fraction')

# set common axis labels
ax.set_ylabel('No. of datasets', labelpad=40)
ax.set_xlabel('Vertical accuracy (m)', labelpad=35)

# get the "nice" version of the source names
sources = list(color_mapping_source.keys())
sources = [' '.join(s.split('_')).title() for s in sources]

sources[-2] = 'Generic GCPs/CPs'
sources[-1] = 'Generic DEM/Orthophoto'

# generate patches for each color
handles = []
for key, color in color_mapping_source.items():
    handles.append(mpatches.Rectangle((0, 0), 1, 1,
                   facecolor=color, edgecolor='k'))

# add a legend in the upper right-hand axis
ax2.legend(handles, sources, fontsize='x-small', bbox_to_anchor=(0.4, 0.15), loc='lower left')

# Show plot
plt.tight_layout()
sns.despine(offset=5, trim=False)      # To make the axis separated
plt.subplots_adjust(hspace=0.5)         # add some space between subplots

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

# save the figure
fig.savefig(Path('figures', 'FigA11_AccuracyComparison.png'), dpi=600, bbox_inches='tight')
