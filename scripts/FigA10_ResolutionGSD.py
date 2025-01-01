from pathlib import Path
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import tools


# ....................................................
# Import excel file as pandas dataframe using datetime
datasets, outputs = tools.load_dataset(subset=['datasets', 'outputs']).values()

merged = datasets[['Key', 'Type', 'GSD [m]']].merge(
    outputs[['Key', 'Orthophoto resolution [m]', 'DEM resolution [m]']],
    left_on='Key', right_on='Key'
)

merged.rename(columns={'GSD [m]': 'gsd',
                       'Orthophoto resolution [m]': 'ortho',
                       'DEM resolution [m]': 'dem'}, inplace=True)
merged.dropna(inplace=True)
merged.drop(merged.loc[merged['Type'] == 'Terrestrial'].index, inplace=True)

# split into aerial, satellite data
(_, aerial), (_, satellite) = merged.groupby('Type')

# .................................................................................
# Plot the Resolution Ortho & DSM versus the GSD: SCATTER PLOT WITH REGRESSION LINE
marker_size = 80
alpha_value = 0.4

# Set seaborn style
sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

# Create the figure and axes
fig, ax = plt.subplots(1, 1, figsize=(15, 7))
ortho, dem = fig.subplots(1, 2)

x = aerial['gsd']

types = ['Aerial', 'Satellite']

for dtype, color, marker in zip(types, [tools.aerial_color, tools.satellite_color], ['o', 's']):
    data = merged.loc[merged['Type'] == dtype]
    x = data['gsd']

    for key, _ax in zip(['ortho', 'dem'], [ortho, dem]):
        y = data[key]
        coeffs = np.polyfit(x, y, deg=1)

        corr = stats.pearsonr(x, y).statistic

        _ax.scatter(x, y, c=color, marker=marker, s=marker_size, alpha=alpha_value, label=f"{dtype} (r={corr:.2f})")

        _x = np.linspace(x.min(), x.max(), 10)
        _ax.plot(_x, np.polyval(coeffs, _x), color=color, linestyle='-', linewidth=2)

# set legends
ortho.legend(loc='upper left')
dem.legend(loc='upper left')

# set extents
ortho.set_ylim(0, 10)
ortho.set_yticks(range(0, 11, 2))

dem.set_ylim(0, 60)

# set labels
ax.set_xlabel('GSD (m)', labelpad=35)
ortho.set_ylabel('Output resolution (m)')

# add panel labels
ortho.annotate('a)', (0, 1.02), xycoords='axes fraction')
dem.annotate('b)', (0, 1.02), xycoords='axes fraction')

# Adjust layout to prevent overlap
plt.tight_layout()
sns.despine(offset=10, trim=False)      # To make the axis separated
plt.subplots_adjust(hspace=0.5)         # add some space between subplots

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

# save the figure
fig.savefig(Path('figures', 'FigA10_ResolutionGSD.png'), dpi=600, bbox_inches='tight')
