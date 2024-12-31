from pathlib import Path
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D, HandlerTuple
import seaborn as sns
import tools


accuracy, datasets = tools.load_dataset(subset=['accuracy', 'datasets']).values()

# drop terrestrial datasets
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# select the necessary columns
datasets = datasets[['Key', 'Type']].copy()

accuracy = accuracy[['DatasetKey', 'Accuracy comparison data [m] Z',
                     'Residuals to comparison [m] Z', 'Comparison Metric',
                     'Comparison source group']].copy()

accuracy.rename(columns={'Accuracy comparison data [m] Z': 'comparison',
                         'Residuals to comparison [m] Z': 'residual',
                         'Comparison Metric': 'metric',
                         'Comparison source group': 'source'}, inplace=True)

merged = datasets.merge(accuracy, left_on='Key', right_on='DatasetKey').drop(columns=['DatasetKey'])

# drop missing values, and values that aren't RMSE or Standard Deviation
metrics = ['RMSE', 'Standard Deviation']
merged.dropna(subset=['comparison', 'residual', 'metric'], how='any', inplace=True)
merged.drop(merged.loc[~merged['metric'].isin(metrics)].index, inplace=True)

# split into aerial, satellite tables
(_, aerial), (_, satellite) = merged.groupby('Type')

# ------------------------            AERIAL DATASET             -------------------------------------------------------
# --- calculate regression line and correlation between the two datasets
corr = dict()
coeffs = dict()
data = dict()
ns = dict()

for source, vals in aerial.groupby('source'):
    ns[source] = len(vals)
    corr[source] = stats.pearsonr(vals['comparison'], vals['residual']).statistic
    coeffs[source] = np.polyfit(vals['comparison'], vals['residual'], deg=1)

ns['satellite'] = len(satellite)
corr['satellite'] = stats.pearsonr(satellite['comparison'], satellite['residual']).statistic
coeffs['satellite'] = np.polyfit(satellite['comparison'], satellite['residual'], deg=1)

# --- Plot aerial and satellite scatter plots (ax1 and ax2) ---
marker_size = 80
marker_size_legend = 20
alpha_value = 0.4

# Set seaborn style
sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

# Create the figure and axes
fig, ax = plt.subplots(1, 1, figsize=(15, 7))
ax1, ax2 = fig.subplots(1, 2)

handles = dict()
labels = dict()
for marker, source in zip(['o', 's'], ['point-based', 'area-based']):
    handles[source] = ax1.scatter(aerial.loc[aerial['source'] == source, 'comparison'],
                                  aerial.loc[aerial['source'] == source, 'residual'],
                                  c=tools.aerial_color, marker=marker, s=marker_size, alpha=alpha_value)
    labels[source] = f"{source.capitalize()} (r={corr[source]:.2f}, n={ns[source]})"

sat_handles = dict()
for marker, source in zip(['o', 's'], ['point-based', 'area-based']):
    sat_handles[source] = ax2.scatter(satellite.loc[satellite['source'] == source, 'comparison'],
                                      satellite.loc[satellite['source'] == source, 'residual'],
                                      c=tools.satellite_color, marker=marker, s=marker_size, alpha=alpha_value)

labels['satellite'] = f"Point- and\narea-based\n(r={corr['satellite']:.2f}, n={ns['satellite']})"


xvals_pt = np.linspace(aerial.loc[aerial['source'] == 'point-based', 'comparison'].min(),
                       aerial.loc[aerial['source'] == 'point-based', 'comparison'].max(), 10)

xvals_area = np.linspace(aerial.loc[aerial['source'] == 'area-based', 'comparison'].min(),
                         aerial.loc[aerial['source'] == 'area-based', 'comparison'].max(), 10)

xvals_sat = np.linspace(satellite['comparison'].min(),
                        satellite['comparison'].max(), 10)

pt_reg, = ax1.plot(xvals_pt, np.polyval(coeffs['point-based'], xvals_pt),
                   color=tools.aerial_color, linestyle='-', linewidth=2)

area_reg, = ax1.plot(xvals_area, np.polyval(coeffs['area-based'], xvals_area),
                     color=tools.aerial_color, linestyle='--', linewidth=2)

sat_reg, = ax2.plot(xvals_sat, np.polyval(coeffs['satellite'], xvals_sat),
                    color=tools.satellite_color, linestyle='-', linewidth=2)

# Set labels and titles if needed
ax.set_xlabel('Accuracy reference data (m)', labelpad=35)
ax1.set_ylabel('Accuracy historical datasets (m)')

# add a legend
ax1.legend([(handles['point-based'], pt_reg), (handles['area-based'], area_reg)],
           [labels['point-based'], labels['area-based']], numpoints=1,
           handler_map={tuple: HandlerTuple(ndivide=1)}, loc='upper left')

ax2.legend([(sat_handles['point-based'], sat_handles['area-based'], sat_reg)],
           [labels['satellite']], numpoints=1,
           handler_map={tuple: HandlerTuple(ndivide=None)}, loc='upper left')

# Show plot
plt.tight_layout()
sns.despine(offset=10, trim=False)  # To make the axis separated
plt.subplots_adjust(hspace=2)     # add some space between subplots

# add panel labels
ax1.annotate('a)', (0, 1.02), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.02), xycoords='axes fraction')

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

# Save the figure
fig.savefig(Path('figures', 'FigA12_AccuracyDEM_Comparison.png'), dpi=600, bbox_inches='tight')
