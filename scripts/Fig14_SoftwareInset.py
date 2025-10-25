import pandas as pd
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
import tools


publications, datasets, processing = tools.load_dataset(subset=['publications', 'datasets', 'processing']).values()

# drop terrestrial datasets
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# select the relevant columns, shortening the name
datasets = datasets[['Key', 'PubKey', 'Type']].set_index('Key')
processing = processing[['Key', 'Method', 'Software', 'GCPs', 'Fiducial Marks']].set_index('Key')
processing.rename(columns={'Fiducial Marks': 'fiducial'}, inplace=True)

# join on the dataset keys
merged = datasets.join(processing).dropna(subset=['Type'])
merged = merged.merge(publications[['PubKey', 'Year']], on='PubKey')

# split into photogrammetric, sfm
photog, sfm = merged.loc[merged['Method'].isin(['Photogrammetric', 'SfM'])].groupby('Method')

# get rid of duplicate publications
photog = photog[1].drop_duplicates(subset='PubKey')
sfm = sfm[1].drop_duplicates(subset='PubKey')

# count the number of published studies each year
pcounts = pd.DataFrame(-photog.value_counts('Year'))
pcounts['method'] = 'Photogrammetric'

scounts = pd.DataFrame(sfm.value_counts('Year'))
scounts['method'] = 'SfM'

counts = pd.concat([pcounts.reset_index(), scounts.reset_index()], ignore_index=True)

# make the pyramid plot
sns.set_theme(font_scale=1.8, style='white')
sns.set_style('ticks')  # white style with tick marks

fig, ax = plt.subplots(1, 1, figsize=(5, 8))
ax = sns.barplot(data=counts, x='count', y='Year',
                 hue='method', palette=['#E497A7', '#A9BEED'], orient='horizontal',
                 dodge=False, native_scale=True, ax=ax, saturation=1)

ax.vlines(0, 2000, 2024, colors='k', linestyles='dashed')

ax.set_xlabel('Number of Studies')
ax.set_ylabel('Year Published')

ax.set_ylim(2000, 2024)

ax.set_xticks([-15, -10, -5, 0, 5, 10, 15])
ax.set_xticklabels([15, 10, 5, 0, 5, 10, 15])

ax.set_xlim(-15, 15)

# re-make the legend with no title
ax.legend(fontsize=16, bbox_to_anchor=(0.5, 0.12))

sns.despine(offset=10, trim=False)

# save the figure
fig.savefig(Path('figures', 'Fig14_SoftwareInset.png'), dpi=200, bbox_inches='tight')
