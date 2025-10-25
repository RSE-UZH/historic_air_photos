# Import necessary packages
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import tools


datasets, outputs, scientific = tools.load_dataset(subset=['datasets', 'outputs', 'scientific']).values()

# remove terrestrial datasets
terrestrial = datasets.loc[datasets['Type'] == 'Terrestrial', 'Key'].to_list()

datasets.drop(datasets[datasets['Key'].isin(terrestrial)].index, inplace=True)
outputs.drop(outputs[outputs['Key'].isin(terrestrial)].index, inplace=True)

# *****************************
# Prepare the data for plotting
# --- Select only relevant columns and create anew dataframe
datasets = datasets[['Key', 'Type']].set_index('Key')

outputs = outputs[['Key', 'PubKey', 'Orthophoto resolution [m]', 'DEM resolution [m]']].set_index('Key')
outputs.rename(columns={'Orthophoto resolution [m]': 'ortho',
                        'DEM resolution [m]': 'dem'}, inplace=True)

scientific = scientific[['PubKey', 'Category']].copy()

merged = datasets.join(outputs).merge(scientific, on='PubKey', how='left')

# Define bins and labels
bins_ortho = [0, 0.5, 1, 2, 4, 6, 10.1]
bin_ortho_labels = ['<0.5', '0.5-1', '1-2', '2-4', '4-6', '6-10']
bins_dem = [0, 1, 2, 4, 6, 10, 20, 40, 500.1]
bin_dem_labels = ['<1', '1-2', '2-4', '4-6', '6-10', '10-20', '20-40', '>40']

# Add a new column for the binned data of ortho and dem
merged['ortho_bins'] = pd.cut(merged['ortho'], bins=bins_ortho, labels=bin_ortho_labels, right=False)
merged['dem_bins'] = pd.cut(merged['dem'], bins=bins_dem, labels=bin_dem_labels, right=False)

# --- Separate the Aerial with the satellite records based on the 'Type' column
(_, aerial), (_, satellite) = merged.groupby('Type')

# ***************************************************************************************************************
# Plot using horizontal stack bar

# --- Setting
width_bar_ortho = 0.55
width_bar_dem = 0.65
lineW = 0.6
fontText = 18

colours = {'Glaciology': '#77AADD',
           'Geomorphology': '#fe9929',
           'Volcanology': '#ef6548',
           'Forestry': '#41ae76',
           'Ecology': '#99d8c9', # AAAA00
           'Archeology': '#fed976',
           'Landuse/Landcover': '#c994c7',  #c05780
           'Urban Change': '#FFAABB',
           'Methodology': '#969696'}

# --------------------------------- PLOT AERIAL ORTHOIMAGES & DEM resolution
aerial_ortho = aerial.groupby(['ortho_bins', 'Category'], observed=False).size().unstack(fill_value=0)
aerial_ordered_ortho = [c for c in colours.keys() if c in aerial_ortho.columns]

aerial_ortho = aerial_ortho[aerial_ordered_ortho]

aerial_dem = aerial.groupby(['dem_bins', 'Category'], observed=False).size().unstack(fill_value=0)
aerial_ordered_dem = [c for c in colours.keys() if c in aerial_dem.columns]

aerial_dem = aerial_dem[aerial_ordered_dem]

# satellite
satellite_ortho = satellite.groupby(['ortho_bins', 'Category'], observed=False).size().unstack(fill_value=0)
satellite_ordered_ortho = [c for c in colours.keys() if c in satellite_ortho.columns]

satellite_ortho = satellite_ortho[satellite_ordered_ortho]

satellite_dem = satellite.groupby(['dem_bins', 'Category'], observed=False).size().unstack(fill_value=0)
satellite_ordered_dem = [c for c in colours.keys() if c in satellite_dem.columns]

satellite_dem = satellite_dem[satellite_ordered_dem]

# --- Plotting
# Set seaborn style
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, ax = plt.subplots(1, 1, figsize=(16, 8))
axs = fig.subplots(2, 2)
ax1, ax2, ax3, ax4 = axs.flatten()

bottom_aerial_ortho = pd.Series([0] * len(aerial_ortho), index=aerial_ortho.index)
bottom_aerial_dem = pd.Series([0] * len(aerial_dem), index=aerial_dem.index)

for counts, _ax, width in zip([aerial_ortho, aerial_dem, satellite_ortho, satellite_dem],
                             axs.flatten(),
                             [width_bar_ortho, width_bar_dem, width_bar_ortho, width_bar_dem]):
    bottoms = pd.Series([0] * len(counts), index=counts.index)
    for category in counts.columns:
        values = counts[category]
        _ax.bar(counts.index, values, label=category, bottom=bottoms, color=colours[category],
                edgecolor='w', linewidth=lineW, width=width)
        bottoms += values

ax3.set_xlabel('Orthoimage resolution (m)')
ax4.set_xlabel('DEM resolution (m)')

ax.set_ylabel('No. of datasets', labelpad=35)

# add panel labels
ax1.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.05), xycoords='axes fraction')
ax3.annotate('c)', (0, 1.05), xycoords='axes fraction')
ax4.annotate('d)', (0, 1.05), xycoords='axes fraction')

ax1.set_ylim([0, 120])
ax1.set_yticks(range(0, 121, 20))

ax2.set_ylim([0, 120])
ax2.set_yticks(range(0, 121, 20))

ax3.set_ylim([0, 40])
ax4.set_ylim([0, 40])

sns.despine(offset=10, trim=False)      # To make the axis separated
plt.subplots_adjust(hspace=0.5)         # add some space between subplots

plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

ax2.legend(fontsize='x-small', bbox_to_anchor=(0.6, 0.3), loc='lower left')

fig.tight_layout()

# save the figure
fig.savefig(Path('figures', 'Fig11_OutputResolution.png'), dpi=600, bbox_inches='tight')
