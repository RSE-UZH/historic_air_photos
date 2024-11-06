# import packages
import pandas as pd
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tools


# Function to plot a stacked histogram
def plot_stacked_histogram(df, _ax, _bins):
    # Initialize a list to hold the bottom values for stacking
    bottom = np.zeros(len(_bins) - 1)

    # Loop through each category and stack the bars
    for category in df['fiducials'].sort_values().unique():
        subset = df[df['fiducials'] == category]
        counts, _ = np.histogram(subset['residuals'], bins=_bins)
        _ax.bar(_bins[:-1], counts, width=width_value, bottom=bottom,
                label=category,
                color=color_mapping_fiducial.get(category, '#333333'),
                edgecolor='black', alpha=alpha_value)
        bottom += counts  # Update bottom to stack the next bar on top

datasets, processing, accuracy = tools.load_dataset(subset=['datasets', 'processing', 'accuracy']).values()

# remove terrestrial datasets
terrestrial = datasets.loc[datasets['Type'] == 'Terrestrial', 'Key'].to_list()

datasets.drop(datasets[datasets['Key'].isin(terrestrial)].index, inplace=True)
processing.drop(processing[processing['Key'].isin(terrestrial)].index, inplace=True)
accuracy.drop(accuracy[accuracy['DatasetKey'].isin(terrestrial)].index, inplace=True)

# ....................................................
# --- SELECT RELEVANT COLUMNS
datasets = datasets[['Key', 'Type']].set_index('Key')
processing = processing[['Key', 'Fiducial Marks']].set_index('Key')
accuracy = accuracy[['DatasetKey', 'Accuracy Key', 'Comparison source group',
                     'Comparison Metric', 'Residuals to comparison [m] Z']]

merged = datasets.join(processing).reset_index().merge(accuracy, left_on='Key', right_on='DatasetKey', how='right')
merged.drop(columns=['Key', 'DatasetKey'], inplace=True)

merged.rename(columns={'Accuracy Key': 'AccKey', 'Fiducial Marks': 'fiducials',
                       'Comparison source group': 'source_group', 'Comparison Metric': 'metric',
                       'Residuals to comparison [m] Z': 'residuals'}, inplace=True)

# remove nan values
merged.dropna(subset='residuals', inplace=True)

# remove values that aren't RMSE or standard deviation
merged.drop(merged.loc[~merged['metric'].isin(['RMSE', 'Standard Deviation'])].index, inplace=True)

# sort based on fiducial markers
order = ['yes', 'not specified', 'no']
merged['fiducials'] = pd.Categorical(merged['fiducials'], categories=order, ordered=True)
merged.sort_values('fiducials').reset_index(drop=True, inplace=True)

# group into aerial, satellite
(_, aerial), (_, satellite) = merged.groupby('Type')

bins = {}
bins['aerial'] = np.arange(0, aerial['residuals'].max() + 1, 1)
bins['satellite'] = np.arange(0, satellite['residuals'].max() + 1, 1)
# ......................................................................................................................
# --- Plot the ACCURACY as histogram, color by the use of fiducial marks (yes, not , non specified)

# --- Create subplots
# Define the color mapping for each 'Comparison_data_group' category
color_mapping_fiducial = {
    'yes': '#d4b9da',
    'no': '#ce1256',
    'not specified': '#df65b0'}

alpha_value = 0.8
width_value = 1

# Set seaborn style
sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, ax = plt.subplots(1, 1, figsize=(15, 10))
axs = fig.subplots(2, 2)

for (data, key, ctype, _ax) in zip([aerial, aerial, satellite, satellite],
                                   ['aerial', 'aerial', 'satellite', 'satellite'],
                                   ['point-based', 'area-based', 'point-based', 'area-based'],
                                   axs.flatten()):
    plot_stacked_histogram(data[data['source_group'] == ctype], _ax, bins[key])
    _ax.set_xlim(-1, 45)

ax1, ax2, ax3, ax4 = axs.flatten()
ax2.legend(loc='upper right')

# set common axis labels
ax.set_ylabel('No. of datasets', labelpad=30)
ax.set_xlabel('Vertical accuracy (m)', labelpad=30)

ax1.set_ylim(0, 90)
ax2.set_ylim(0, 90)
ax3.set_ylim(0, 5)
ax4.set_ylim(0, 5)

# add panel labels
ax1.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.05), xycoords='axes fraction')
ax3.annotate('c)', (0, 1.05), xycoords='axes fraction')
ax4.annotate('d)', (0, 1.05), xycoords='axes fraction')

# Show plot
plt.tight_layout()
sns.despine(offset=5, trim=False)      # To make the axis separated
plt.subplots_adjust(hspace=0.5)         # add some space between subplots

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

plt.savefig(Path('figures', 'Fig16_AccuracyFiducials.png'), dpi=600, bbox_inches='tight')
