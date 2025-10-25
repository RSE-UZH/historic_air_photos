from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tools


scientific, = tools.load_dataset(subset=['scientific'], relevant=False).values()

# split into relevant, not relevant
relevant = scientific.loc[scientific['Relevant']]
not_relevant = scientific.loc[~scientific['Relevant']]

# count the number of studies in each category
rel_counts = relevant.value_counts('Category').rename('Relevant')
nr_counts = not_relevant.value_counts('Category').rename('Not Relevant')

# combine the tables
comparison = pd.concat([rel_counts, nr_counts], axis=1).drop(['History of Science', 'Review']).fillna(0).reset_index()

sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, ax = plt.subplots(1, 1, figsize=(6, 6))

bottom = np.zeros_like(comparison['Category'])
ax.bar(comparison['Category'], comparison['Relevant'],
       fc='#0066cc', ec='k', label='Relevant', bottom=bottom)

bottom += comparison['Relevant']

ax.bar(comparison['Category'], comparison['Not Relevant'],
       fc='#ffcc66', ec='k', label='Not Relevant', bottom=bottom)

ax.set_ylabel('No. of studies')

labels = comparison['Category']
locs = range(len(labels))

ax.legend()

sns.despine(offset=10, trim=False)
ax.set_xticks(locs, labels, rotation=45, ha='right')

fig.savefig(Path('figures', 'FigA5_RelevantDisciplines.png'), bbox_inches='tight', dpi=200)
