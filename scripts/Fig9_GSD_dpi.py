from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from matplotlib.ticker import MultipleLocator
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import MultipleLocator
import tools


# ===========================================
# Read the  the Excel file and prepare the data
datasets, = tools.load_dataset(subset=['datasets']).values()

# make sure to remove terrestrial datasets
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# =============================
# Prepare the data for plotting
columns = ['PubKey', 'Type', 'Dataset Number', 'Acquisition Start Year', 'GSD [m]',
           'Scanner resolution', 'Scanner resolution units']
datasets.drop(columns=[c for c in datasets.columns if c not in columns], inplace=True)

datasets.rename(columns={'Dataset Number': 'dataset_number',
                         'Acquisition Start Year': 'start_year',
                         'GSD [m]': 'gsd',
                         'Scanner resolution': 'scanner_res',
                         'Scanner resolution units': 'units'},
                inplace=True)

# remove rows where gsd isn't specified
datasets.dropna(subset='gsd', inplace=True)

# convert µm to dpi
is_micro = datasets['units'] != 'dpi' # for some reason, can't get µm recognized
datasets.loc[is_micro, 'scanner_res'] = datasets.loc[is_micro, 'scanner_res'].apply(tools.microns_to_dpi)

# Round the values to 2 decimal places
datasets['scanner_res'] = datasets['scanner_res'].round(0)

# ===================================================================================================================
#               new FIGURE --> RESULT PLOT ONLY USING DPI
# Define the μm categories (8 edges create 7 bins) and corresponding colors (7 colors)
dpi_categories = [0, 300, 600, 1200, 2400, 3630]
dpi_colors = ['#d4b9da', '#c994c7', '#df65b0', '#e7298a', '#ce1256']
nan_color = '#FFFFFF'  # Color to assign if scanner_res_microns is NaN

# --- Create a new column for categorizing 'scanner_res_microns' based on μm_categories
datasets['dpi_color'] = pd.cut(datasets['scanner_res'],
                               bins=dpi_categories, labels=dpi_colors,
                               include_lowest=True, ordered=False).astype(str)
datasets['dpi_color'] = datasets['dpi_color'].replace('nan', nan_color)

# --- Separate the Aerial with the satellite records based on the 'Type' column
aerial = datasets[datasets['Type'] == 'Aerial']
satellite = datasets[datasets['Type'] == 'Satellite']

# --- Filter rows where 'GSD [m]' is greater than 2.5
aerial_coarse = aerial[aerial['gsd'] > 2.5]

marker_size = 60
alpha_values = 0.8

# --- Plot
# Create the scatter plot
sns.set_theme(font_scale=1.7, style="white")
sns.set_style('ticks')

fig, ax = plt.subplots(1, 1, figsize=(15, 6))

# Set the subplots
gs = fig.add_gridspec(3, 3)
# ax1.set_title('Aerial images')
ax1 = fig.add_subplot(gs[0, 0:2])
ax3 = fig.add_subplot(gs[1:, 0:2], sharex=ax1)
# ax2.set_title('Spy satellite images')
ax2 = fig.add_subplot(gs[0:, -1])

# Scatter plot where color is based on the 'microns_color' column
# -- Plot ax3 (aerial range 0 -2.8)
ax3.scatter(
    aerial['start_year'],
    aerial['gsd'],
    c=aerial['dpi_color'],
    s=marker_size,
    alpha=alpha_values,
    edgecolor='k') # Add a black edge to points for better visibility

# -- Plot ax1 (aerial range from 3 to 60)
ax1.scatter(
    aerial_coarse['start_year'],
    aerial_coarse['gsd'],
    c=aerial_coarse['dpi_color'],
    s=marker_size,
    alpha=alpha_values,
    edgecolor='k')

# -- Plot ax2 satellite
ax2.scatter(
    satellite['start_year'],
    satellite['gsd'],
    c=satellite['dpi_color'],
    s=marker_size,
    alpha=alpha_values,
    edgecolor='k')


# Create a colormap for dpi categories
dpi_categories_legend = [0, 300, 600, 1200, 2400, 3600]
dpi_cmap = ListedColormap(dpi_colors)

# Use BoundaryNorm to map colors correctly to the categories
norm = BoundaryNorm(boundaries=dpi_categories_legend, ncolors=len(dpi_colors), clip=True)

# Create a ScalarMappable object for the colorbar
dpi_sm = ScalarMappable(norm=norm, cmap=dpi_cmap)
dpi_sm.set_array([])  # Only necessary for older versions of Matplotlib

# Create colorbar
cbar_dpi = fig.colorbar(dpi_sm, ax=ax2, orientation='vertical')

# Set colorbar ticks and labels
cbar_dpi.set_ticks(dpi_categories_legend)           # Set the ticks to match dpi_categories
cbar_dpi.set_ticklabels(dpi_categories_legend)      # Set the labels to match dpi_categories
cbar_dpi.set_label('Scanner resolution (dpi)')

# Set axis labels and properties

# ax1.set_title('GSD vs Acquisition Year colored by scanner resolution microns')
ax1.set_xlim([1930, 2015])
ax3.set_xlim([1930, 2015])
ax2.set_xlim([1960, 1983])

ax1.set_ylim([2, 65])
ax3.set_ylim([-0.2, 2.8])
ax2.set_ylim([0.2, 12])

# Set x-ticks to white
ax1.tick_params(axis='x', colors='white')  # Set x-tick colors

# Change y-ticks to have an interval of 10 meters
ax1.yaxis.set_major_locator(MultipleLocator(20))  # Set y-tick interval
ax1.tick_params(axis='y', colors='black')

# Display the plot with  axis separated
sns.despine(offset=5, trim=False)

# remove bottom spine from ax1
ax1.spines[['bottom']].set_visible(False)

# turn off the left, bottom spines for the colorbar axis
cbar_dpi.ax.spines[['left', 'bottom']].set_visible(False)

# plot the lines to indicate break in axes
# kwargs = dict(transform=ax.transAxes, color='k', clip_on=False)
kwargs = dict(color='k', clip_on=False)
ax1.plot([1927, 1932], [-3, 5], **kwargs)
ax1.plot([1927, 1932], [-14, -6], **kwargs)

# set subtitles
# ax1.set_title('Aerial')
# ax2.set_title('Satellite')
ax1.annotate('a)', (0, 1.07), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.02), xycoords='axes fraction')

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

# set common x, y labels
ax.set_xlabel('Acquisition Year', labelpad=35)
ax.set_ylabel('GSD (m)', labelpad=35, color='black')

# Save the figure
fig.savefig(Path('figures', 'Fig9_GSD_vs_ScanRes.png'), dpi=600, bbox_inches='tight')
