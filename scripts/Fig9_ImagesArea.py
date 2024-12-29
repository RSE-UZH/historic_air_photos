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


# =======================================
# Read the xlsx file and prepare the data
datasets, geographic = tools.load_dataset(subset=['datasets', 'geographic']).values()

# expand number of study areas to match number of datasets
geographic = tools.expand_study_areas(geographic, datasets)

# select columns needed
datasets = datasets[['Key', 'PubKey', 'Type', 'No. Images']].copy()
geographic = geographic[['DatasetKey', 'Area', 'Region']].copy()

# merge
merged = geographic.merge(datasets, left_on='DatasetKey', right_on='Key').drop(columns=['Key'])

# rename columns
merged.rename(columns={'No. Images': 'num_images'}, inplace=True)

merged.drop(merged.loc[merged['Type'] == 'Terrestrial'].index, inplace=True)
merged.dropna(subset=['Area', 'num_images'], how='any', inplace=True)

# reduce to avoid duplicating datasets
reduced = merged.drop_duplicates(subset='DatasetKey').set_index('DatasetKey')
reduced['Area'] = merged.groupby('DatasetKey')['Area'].sum()

# split into aerial and satellite
(_, aerial), (_, satellite) = reduced.groupby('Type')

# =====================================================================================================================
# NEW PLOT  logarithmic SCALE
# --- Plot aerial and satellite with two subplots
marker_size = 60
marker_size_zoom = 100
alpha_values = 0.7

# --- Plot
sns.set_theme(font_scale=1.7, style="white")
sns.set_style('ticks')

fig, ax = plt.subplots(1, 1, figsize=(15, 5))
ax1, ax2 = fig.subplots(1, 2)

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

ax.set_ylabel('Area (km$^2$)', labelpad=85)
ax.set_xlabel('No. of images', labelpad=35)

# annotate panels
ax1.annotate('a)', (0, 1.05), xycoords='axes fraction')
ax2.annotate('b)', (0, 1.05), xycoords='axes fraction')

# Display the plot with  axis separated
sns.despine(offset=5, trim=False)
plt.tight_layout()

# remove background axis
plt.setp(ax.spines.values(), visible=False)
ax.set_xticks([])
ax.set_yticks([])

# Save the figure
fig.savefig(Path('figures', 'Fig9_ImagesArea.png'), dpi=600, bbox_inches='tight')
