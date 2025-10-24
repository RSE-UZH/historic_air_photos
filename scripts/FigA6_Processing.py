import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import tools


def get_pre_counts(df):
    counts = df['pre_pro'].value_counts()

    not_specified_count = counts.get('not specified', 0)
    no_count = counts.get('no', 0)
    yes_count = counts.get('yes', 0)

    pre_both_count = df['pre_both_yes'].sum()
    pre_geom_count = df['pre_geom_yes'].sum()
    pre_rad_count = df['pre_rad_yes'].sum()

    preproc_entry = [1, 2, 3, 4, 5, 6]
    count_df = pd.DataFrame(preproc_entry, columns=['preproc_entry'])

    count_df['preproc_label'] = ['Not specified', 'No', 'Yes', 'Geometric', 'Radiometric', 'Both']
    count_df['count_value'] = [not_specified_count,
                               no_count,
                               yes_count,
                               pre_geom_count,
                               pre_rad_count,
                               pre_both_count]

    total_count = counts.values.sum()

    count_df['count_percent'] = count_df['count_value'].apply(
        lambda x: (x / total_count * 100) if pd.notna(x) else pd.NA)

    return count_df


def get_gcp_counts(df):
    counts = df['gcps'].value_counts()

    not_specified_count = counts['not specified']
    no_count = counts['no']
    yes_count = counts['yes']

    gcp_entry = [1, 2, 3]
    count_df = pd.DataFrame(gcp_entry, columns=['gcp_entry'])

    count_df['gcp_label'] = ['Not specified', 'No', 'Yes']
    count_df['count_value'] = [not_specified_count, no_count, yes_count]

    total_count = counts.values.sum()

    count_df['count_percent'] = count_df['count_value'].apply(
        lambda x: (x / total_count * 100) if pd.notna(x) else pd.NA)

    return count_df


def plot_stacks(ax, labels, counts, bottoms, colors, lineW, width_bar):

    bars = ax.barh(labels, counts, left=np.array(bottoms), color=colors, edgecolor='w',
                   linewidth=lineW, height=width_bar)
    # ax.invert_yaxis()

    total = np.sum(counts)

    # add the labels
    pcts = 100 * np.array(counts) / total
    pct_labels = [f"{int(np.round(p, 0)):d}%" for p in pcts]

    for (bar, pct) in zip(bars, pct_labels):
        ax = tools.bar_text(ax, bar, pct)

    return ax


# load the datasets and processing tables from the spreadsheet
datasets, processing = tools.load_dataset(subset=['datasets', 'processing']).values()

# drop terrestrial datasets
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# *****************************
# Prepare the data for plotting
# --- Select only relevant columns and create anew dataframe
datasets = datasets[['PubKey', 'Key', 'Type']].set_index('Key')

processing_cols = ['Key', 'GCPs', 'Fiducial Marks', 'Pre-processing',
                   'Geometric Pre-processing', 'Radiometric Pre-processing']
processing = processing[processing_cols].set_index('Key')

# --- Merging the two dataframes on the 'Key' column
merged = datasets.join(processing).dropna(subset=['Type'])

# --- Rename columns
merged.rename(columns={'GCPs': 'gcps',
                       'Fiducial Marks': 'fiducial',
                       'Pre-processing': 'pre_pro',
                       'Geometric Pre-processing': 'pre_geom',
                       'Radiometric Pre-processing': 'pre_rad'},
              inplace=True)

# get dummy variables for gcps, fiducial, and pre_pro
merged = merged.join(pd.get_dummies(merged[['gcps', 'fiducial', 'pre_pro']]))

spaces = [c for c in merged.columns if ' ' in c]
replaces = [c.replace(' ', '_') for c in spaces]
merged.rename(columns=dict(zip(spaces, replaces)), inplace=True)

# get dummy variables for pre_geom, pre_rad
merged['pre_geom_yes'] = np.where(merged['pre_geom'].notna(), 1, 0)
merged['pre_geom_no'] = np.where(merged['pre_geom'].isna(), 1, 0)

merged['pre_rad_yes'] = np.where(merged['pre_rad'].notna(), 1, 0)
merged['pre_rad_no'] = np.where(merged['pre_rad'].isna(), 1, 0)

# Create a new column 'pre_both' with values equal 1 when there are 1 in both 'pre_geome' and 'pre_radio'
merged['pre_both_yes'] = np.where(merged['pre_geom_yes'] & merged['pre_rad_yes'], 1, 0)

# --- Remove 1 values from 'pre_geome_1' and 'pre_radio_1' when there are value 1 in 'pre_both_1'
# Set 'pre_geome_1' and 'pre_radio_1' to 0 where 'pre_both_1' is 1
merged.loc[merged['pre_both_yes'] == 1, ['pre_geom_yes', 'pre_rad_yes']] = 0

# --- Separate the Aerial with the satellite records based on the 'Type' column
(_, aerial), (_, satellite) = merged.groupby('Type')

# **************************************
# Count the values and group by category
pre_aerial_counts = get_pre_counts(aerial)
pre_satellite_counts = get_pre_counts(satellite)

gcp_aerial_counts = get_gcp_counts(aerial)
gcp_satellite_counts = get_gcp_counts(satellite)
# ***************************************************************************************************************
#                                       Plot using horizontal bar --> FINAL VERSION
# Horizontal bar plot where the first two bars are individual values
# and the third bar is a stacked bar with combined values

# Data for the plot
pre_labels = ['Not specified', 'No', 'yes', 'yes', 'yes']
gcp_labels = ['Not specified', 'No', 'Yes']

# --- AERIAL
pre_aerial = pre_aerial_counts.loc[[0, 1, 3, 4, 5], 'count_value'].to_list()
pre_bottoms_aerial = 3 * [0] + list(np.cumsum(pre_aerial[2:4]))

pre_satellite = pre_satellite_counts.loc[[0, 1, 3, 4, 5], 'count_value'].to_list()
pre_bottoms_satellite = 3 * [0] + list(np.cumsum(pre_satellite[2:4]))

gcp_aerial = gcp_aerial_counts['count_value'].to_list()
gcp_satellite = gcp_satellite_counts['count_value'].to_list()

# --- Setting
width_bar = 0.7
lineW = 0.6
fontTextPercent = 20

# Colors
color_notspec = '#1A354A'
col_aerial = '#108896'
col_spy = '#7456F1'

# --- Plot
# Set seaborn style
sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

# Create the figure and axes
aerial_colors = ['#1A354A66', '#1A354A', '#10889666', '#10889699', '#108896']
satellite_colors = ['#1A354A66', '#1A354A', '#7456F166', '#7456F199', '#7456F1']

fig, axs = plt.subplots(2, 2, figsize=(15, 6))
ax1, ax2, ax3, ax4 = axs.flatten()

# ax, labels, counts, bottoms, colors, lineW, width_bar
ax1 = plot_stacks(ax1, pre_labels, pre_aerial, pre_bottoms_aerial, aerial_colors, lineW, width_bar)
ax2 = plot_stacks(ax2, pre_labels, pre_satellite, pre_bottoms_satellite, satellite_colors, lineW, width_bar)

ax3 = plot_stacks(ax3, gcp_labels, gcp_aerial, np.zeros(3),
                  aerial_colors[:2] + [aerial_colors[-1]], lineW, width_bar)
ax4 = plot_stacks(ax4, gcp_labels, gcp_satellite, np.zeros(3),
                  satellite_colors[:2] + [satellite_colors[-1]], lineW, width_bar)

# Add labels and title
# ax1.set_xlabel('No. of datasets')
# ax2.set_xlabel('No. of datasets')
ax3.set_xlabel('No. of datasets')
ax4.set_xlabel('No. of datasets')

# set y-label manually
y_labels = ['Not specified', 'No', 'Yes: \n Geometric | Radiometric | Both']
ax1.set_yticks([0, 1, 2])
ax1.set_yticklabels(y_labels)
ax1.set_ylim([-0.5, 2.5])

for axis in (ax2, ax4):
    axis.set_yticks([])

# ax1.set_title('Aerial images', fontweight='bold')
# ax2.set_title('Satellite images', fontweight='bold')
ax1.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.05), xycoords='axes fraction')
ax3.annotate('c)', (0, 1.05), xycoords='axes fraction')
ax4.annotate('d)', (0, 1.05), xycoords='axes fraction')

# Invert y-axis
# Make the y-axis line and ticks invisible and move the x-axis line to the top
for axis in axs.flatten():
    axis.invert_yaxis()
    axis.spines['left'].set_visible(False)
    axis.tick_params(axis='y', which='both', length=0)
    axis.spines['top'].set_position(('axes', 0.0))

sns.despine(offset=10, trim=False)      # To make the axis separated
# plt.subplots_adjust(hspace=0.2, wspace=0.1)         # add some space between subplots

fig.tight_layout()
# save the figure
fig.savefig(Path('figures', 'FigA6_ProcessingComparison.png'), dpi=600, bbox_inches='tight')
