import pandas as pd
from pathlib import Path
import os
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
lineCol_aerial = '#108896'
lineCol_satellite = '#7456F1'
color_notspec = '1A354A'

line_width = 1

# Plot
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')

fig, ax = plt.subplots(figsize=(15, 5))
# white style with tick marks
for ind in range(1, datasets['study_index'].max()):
    aerial = datasets.loc[(datasets['study_index'] == ind) & (datasets['Type'] == 'Aerial')]
    #print(selection)
    ax.plot(aerial['start_date'], aerial['study_index'], color=lineCol_aerial,
            linewidth=line_width, marker='o', alpha=0.6)

    satellite = datasets.loc[(datasets['study_index'] == ind) & (datasets['Type'] == 'Satellite')]
    ax.plot(satellite['start_date'], satellite['study_index'], color=lineCol_satellite,
            linewidth=line_width, marker='s', alpha=0.6)

ax.legend(['Aerial', 'Satellite'], loc='upper left')
ax.set_yticks([])
ax.set_xticks(range(1930, 2021, 10))
ax.set_xlabel('Acquisition year')      #weight='bold'

# To make the axis separated
sns.despine(offset=10, trim=False)
# Save the figure
fig.savefig(Path('figures', 'Figure_timeLine_Studies.png'), dpi=600, bbox_inches='tight')
