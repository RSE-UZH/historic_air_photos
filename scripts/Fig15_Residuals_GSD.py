from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import seaborn as sns
import tools


def add_regression_lines(_ax, x_data, styles):
    x_vals = np.linspace(min(x_data), max(x_data), 100)
    handles = []
    for factor, (color, style) in styles.items():
        y_vals = factor * x_vals
        h, = _ax.plot(x_vals, y_vals, linestyle=style, color=color, label=f'{factor}x GSD', linewidth=1.5)
        handles.append(h)

    return(handles)

# ....................................................
# Import excel file as pandas dataframe using datetime
datasets, accuracy = tools.load_dataset(subset=['datasets', 'accuracy']).values()

# make sure to calculate average accuracy measures
accuracy = tools.accuracy_measures(accuracy)

# --- SELECT RELEVANT COLUMNS
datasets = datasets[['Key', 'Type', 'GSD [m]']].copy()
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

accuracy = accuracy[['DatasetKey', 'Residuals to comparison [m] Z',
                     'Residuals to comparison [m] XY', 'Comparison Metric']].copy()

datasets.rename(columns={'GSD [m]': 'gsd'}, inplace=True)
accuracy.rename(columns={'Residuals to comparison [m] Z': 'residuals',
                         'Residuals to comparison [m] XY': 'planimetric',
                         'Comparison Metric': 'metric'}, inplace=True)

merged = datasets.merge(accuracy, left_on='Key', right_on='DatasetKey', how='left')
merged.drop(merged.loc[~merged['metric'].isin(['RMSE', 'Standard Deviation'])].index, inplace=True)
merged = merged.dropna(subset='gsd').dropna(how='all', subset=['residuals', 'planimetric'])

(_, aerial), (_, satellite) = merged.groupby('Type')
# ======================================================================================================================
#                           PLOT THE ACCURACY VS THE GSD
marker_size = 80
marker_size_legend = 20
alpha_value = 0.7

# --- Plot
# Set seaborn style
sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

# Create the figure and axes
fig, ax = plt.subplots(1, 1, figsize=(15, 6))
(ax1, ax2) = fig.subplots(1, 2,  sharey=True)

ax1.scatter(aerial['gsd'], aerial['planimetric'], marker='P', ec='k',
            c=tools.aerial_color, s=marker_size)

ax1.scatter(aerial['gsd'], aerial['residuals'],
            c=tools.aerial_color, s=marker_size, alpha=alpha_value)

ax2.scatter(satellite['gsd'], satellite['planimetric'], marker='P', ec='k',
            c=tools.satellite_color, s=marker_size)

ax2.scatter(satellite['gsd'], satellite['residuals'],
            c=tools.satellite_color, s=marker_size, alpha=alpha_value)

# Set logarithmic scale for both axes
ax1.set_xscale('log')
ax1.set_yscale('log')
ax2.set_xscale('log')
ax2.set_yscale('log')

# Set labels and titles if needed
ax.set_xlabel('GSD (m)', labelpad=35)
ax1.set_ylabel('Reported Accuracy (m)')

# Define line styles for 1x, 2x, 4x GSD lines
line_styles = {
    1: ('#1A354A', '--'),  # 1x GSD (dashed line)
    2: ('#1A354A', '-.'),  # 2x GSD (dash-dot line)
    4: ('#1A354A66', ':')}  # 4x GSD (dotted line)

# Add regression lines to both subplots
add_regression_lines(ax1, aerial['gsd'], line_styles)
handles = add_regression_lines(ax2, satellite['gsd'], line_styles)

# Add legends
# add marker shape to the legend
cross = mlines.Line2D([], [], markerfacecolor='none', markeredgecolor='k',
                       marker='P', markersize=10, linestyle='', label='Planimetric')

circ = mlines.Line2D([], [], markerfacecolor='none', markeredgecolor='k',
                     marker='o', markersize=10, linestyle='', label='Vertical')

ax2.legend(handles=[cross, circ] + handles, fontsize='small', loc='lower right')

# Customize x-axis ticks for better readability on log scale
xticks_ax1 = [0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50]
ax1.set_xticks(xticks_ax1)
ax1.set_xticklabels([str(tick) for tick in xticks_ax1])

# TODO: if using NMAD, add 0.5
xticks_ax2 = [1, 2, 5, 10, 20, 50]
ax2.set_xticks(xticks_ax2)
ax2.set_xticklabels([str(tick) for tick in xticks_ax2])

# Customize y-axis ticks for better readability on log scale
yticks = [0.1, 0.5, 1, 5, 10, 50, 100]
ax1.set_yticks(yticks)
ax1.set_yticklabels([str(tick) for tick in yticks])

ax2.set_yticks(yticks)
ax2.set_yticklabels([str(tick) for tick in yticks])

# annotate xlabels
ax1.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.05), xycoords='axes fraction')

# Show plot
plt.tight_layout()
sns.despine(offset=10, trim=False)  # To make the axis separated
plt.subplots_adjust(hspace=2)     # add some space between subplots

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

# TODO: why does this output look different?
# Save the figure
fig.savefig(Path('figures', 'Fig15_Residuals_GSD.png'), dpi=600, bbox_inches='tight')
