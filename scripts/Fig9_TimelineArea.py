from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tools


def bar_plot(_ax, df, _bins):
    # -- Calculate histogram data
    counts, _ = np.histogram(df['num_images'], bins=_bins)
    widths = np.diff(_bins)
    _ax.bar(_bins[:-1], counts, width=widths, align='edge', alpha=0.3, color='grey', edgecolor='black')

    # Set the secondary y-axis labels
    # _ax.set_yticks(np.arange(0, max(counts) + 1, step=max(counts) // 10))
    # _ax.set_yticklabels([str(int(label)) for label in ax1_bar.get_yticks()])
    _ax.tick_params(axis='y', colors='grey')

    return _ax

# ....................................................
# Read the xlsx file and prepare the data
datasets, geographic = tools.load_dataset(subset=['datasets', 'geographic']).values()

# expand number of study areas to match number of datasets
geographic = tools.expand_study_areas(geographic, datasets)
geographic = geographic[['DatasetKey', 'Area', 'Region']].copy()

# ....................
# prepare the dataset to plot the timeline, distribution plots
tl_columns = ['PubKey', 'Dataset Number', 'Type', 'Acquisition Start Year', 'Acquisition End Year', 'GSD [m]', 'Scale']
dst_columns = ['Key', 'PubKey', 'Type', 'No. Images']

datasets.drop(columns=[c for c in datasets.columns if c not in set(tl_columns + dst_columns)], inplace=True)

# rename 'Acquisition Start Year', 'Acquisition End Year' using shorter name
datasets.rename(columns={'Acquisition Start Year': 'start_date', 'Acquisition End Year': 'end_date',
                         'Dataset Number': 'no_dataset', 'GSD [m]': 'gsd', 'No. Images': 'num_images'}, inplace=True)

# Drop the rows where 'Data Type' is 'Terrestrial'
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# merge datasets and geographic to make panels b, c
merged = geographic.merge(datasets, left_on='DatasetKey', right_on='Key').drop(columns=['Key'])

# rename columns
merged.rename(columns={'No. Images': 'num_images'}, inplace=True)
merged.dropna(subset=['Area', 'num_images'], how='any', inplace=True)

# reduce to avoid duplicating datasets
reduced = merged.drop_duplicates(subset='DatasetKey').set_index('DatasetKey')
reduced['Area'] = merged.groupby('DatasetKey')['Area'].sum()

# split into aerial and satellite
(_, aerial), (_, satellite) = reduced.groupby('Type')

# Sort the dataframe by Type and dates to make panel a
datasets.sort_values(['Type', 'start_date'], ascending=[True, True], inplace=True)

# create list of unique key of aerial and satellite
unique_keys = datasets['PubKey'].unique().tolist()

# get the index number for each study
datasets['study_index'] = -1 # initialize as integer
for ind, row in datasets.iterrows():
    datasets.loc[ind, 'study_index'] = unique_keys.index(row['PubKey']) + 1

# ................
# Plot the results
labels_legend = ['Aerial', 'Satellite']
color_notspec = '1A354A'

line_width = 1

# Plot
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')

fig = plt.figure(figsize=(15, 10))

gs = fig.add_gridspec(2, 2)

ax = fig.add_subplot(gs[0, :])

_ax = fig.add_subplot(gs[1, :])



ax1 = fig.add_subplot(gs[1, 0])
ax2 = fig.add_subplot(gs[1, 1])

time_ax = ax.twinx()

# plot a histogram of the # of datasets by decade
decades = np.arange(1930, 2021, 10)
datasets['center_date'] = datasets[['start_date', 'end_date']].mean(axis=1)

ax.hist(datasets['center_date'], bins=decades, alpha=0.3, color='grey', edgecolor='black')

ax.set_xlim(1930, 2021)
ax.set_ylim(0, 160)
ax.set_ylabel('No. of datasets')
ax.set_xlabel('Acquisition Year')

# white style with tick marks
for ind in range(1, datasets['study_index'].max()):
    aerial_df = datasets.loc[(datasets['study_index'] == ind) & (datasets['Type'] == 'Aerial')]
    #print(selection)
    time_ax.plot(aerial_df['start_date'], aerial_df['study_index'], color=tools.aerial_color,
            linewidth=line_width, marker='o', alpha=0.6)

    satellite_df = datasets.loc[(datasets['study_index'] == ind) & (datasets['Type'] == 'Satellite')]
    time_ax.plot(satellite_df['start_date'], satellite_df['study_index'], color=tools.satellite_color,
            linewidth=line_width, marker='s', alpha=0.6)

time_ax.legend(['Aerial', 'Satellite'], loc='upper left')
time_ax.set_yticks([])
time_ax.set_xlim([1930, 2020])
time_ax.set_xticks(range(1930, 2021, 10))
time_ax.set_xlabel('Acquisition year')      #weight='bold'

# --- Plot aerial and satellite with two subplots
marker_size = 60
marker_size_zoom = 100
alpha_values = 0.7

ax1.scatter(aerial['num_images'], aerial['Area'], color=tools.aerial_color, s=marker_size, alpha=alpha_values)
ax2.scatter(satellite['num_images'], satellite['Area'], color=tools.satellite_color, s=marker_size, alpha=alpha_values)

# Set the x-axis to a logarithmic scale
ax1.set_xscale('log')
ax1.set_yscale('log')
ax2.set_xscale('log')
ax2.set_yscale('log')

# Customize x-axis and y-axis ticks for better readability
x_ticks_ax1 = [1, 10, 100, 1000, 10000]
ax1.set_xticks(x_ticks_ax1)
ax1.set_xticklabels([f'{int(tick)}' for tick in x_ticks_ax1])

x_ticks_ax2 = [1, 5, 10, 100, 1000]
ax2.set_xticks(x_ticks_ax2)
ax2.set_xticklabels([f'{int(tick)}' for tick in x_ticks_ax2])

# Customize y-axis ticks with labels such as "1 km²" and "10 km²"
y_ticks_ax1 = [1, 10, 100, 1000, 10000, 100000, 1000000]
ax1.set_yticks(y_ticks_ax1)
ax1.set_yticklabels([f'{int(tick):,}' if tick >= 1 else f'{tick}' for tick in y_ticks_ax1])

y_ticks_ax2 = [10, 100, 1000, 10000, 100000, 1000000, 10000000]
ax2.set_yticks(y_ticks_ax2)
ax2.set_yticklabels([f'{int(tick):,}' if tick >= 1 else f'{tick}' for tick in y_ticks_ax2])

# Add a secondary y-axis for the bar plot
ax1_bar = ax1.twinx()
ax2_bar = ax2.twinx()

# plot bar graphs
ax1_bar = bar_plot(ax1_bar, aerial, [1, 5, 10, 50, 100, 1000, 10000])
ax2_bar = bar_plot(ax2_bar, satellite, [1, 5, 10, 50, 100, 1000])

ax2_bar.set_ylabel('No. of Datasets', color='grey')

_ax.set_ylabel('Area (km$^2$)', labelpad=85)
_ax.set_xlabel('No. of images', labelpad=35)

# annotate panels
ax.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax1.annotate('b)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('c)', (0, 1.05), xycoords='axes fraction')

# To make the axis separated
sns.despine(offset=10, trim=False)
plt.tight_layout()

# remove background axis
plt.setp(_ax.spines.values(), visible=False)
_ax.set_xticks([])
_ax.set_yticks([])

# Save the figure
fig.savefig(Path('figures', 'Fig9_TimelineArea.png'), dpi=600, bbox_inches='tight')
