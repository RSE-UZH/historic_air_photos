from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tools


# ....................................................
# Import excel file as pandas dataframe using datetime
datasets, = tools.load_dataset(subset=['datasets']).values()

# ....................
# prepare the dataset
columns = ['PubKey', 'Dataset Number', 'Type', 'Acquisition Start Year', 'Acquisition End Year', 'GSD [m]', 'Scale']
datasets.drop(columns=[c for c in datasets.columns if c not in columns], inplace=True)

# rename 'Acquisition Start Year', 'Acquisition End Year' using shorter name
datasets.rename(columns={'Acquisition Start Year': 'start_date', 'Acquisition End Year': 'end_date',
                         'Dataset Number': 'no_dataset', 'GSD [m]': 'gsd'}, inplace=True)

# Drop the rows where 'Data Type' is 'Terrestrial'
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# Sort the dataframe by Type and dates
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

fig, ax = plt.subplots(figsize=(15, 5))

time_ax = ax.twinx()

# plot a histogram of the # of datasets by decade
decades = np.arange(1930, 2021, 10)
datasets['center_date'] = datasets[['start_date', 'end_date']].mean(axis=1)

ax.hist(datasets['center_date'], bins=decades, alpha=0.3, color='grey', edgecolor='black')

ax.set_xlim(1930, 2021)
ax.set_ylim(0, 160)
ax.set_ylabel('No. of datasets')

# white style with tick marks
for ind in range(1, datasets['study_index'].max()):
    aerial = datasets.loc[(datasets['study_index'] == ind) & (datasets['Type'] == 'Aerial')]
    #print(selection)
    time_ax.plot(aerial['start_date'], aerial['study_index'], color=tools.aerial_color,
            linewidth=line_width, marker='o', alpha=0.6)

    satellite = datasets.loc[(datasets['study_index'] == ind) & (datasets['Type'] == 'Satellite')]
    time_ax.plot(satellite['start_date'], satellite['study_index'], color=tools.satellite_color,
            linewidth=line_width, marker='s', alpha=0.6)

time_ax.legend(['Aerial', 'Satellite'], loc='upper left')
time_ax.set_yticks([])
time_ax.set_xlim([1930, 2020])
time_ax.set_xticks(range(1930, 2021, 10))
time_ax.set_xlabel('Acquisition year')      #weight='bold'

# To make the axis separated
sns.despine(offset=10, trim=False)

# ax.spines['left'].set_visible(False)
# Save the figure
fig.savefig(Path('figures', 'Fig8_Studies_Timeline.png'), dpi=600, bbox_inches='tight')
