import pandas as pd
from pathlib import Path
import os
import matplotlib.pyplot as plt
import seaborn as sns
import tools


def get_counts(df, ds_type):
    subset = df.loc[df['Type'] == ds_type]
    counts = subset.groupby(['location', 'free']).size().unstack(fill_value=0)

    # Rename columns to match the desired format
    counts = counts.rename(columns={'yes': 'free_yes', 'unclear': 'free_unclear',
                                    'no': 'free_no'}).reset_index()

    # --- Add a new column 'total_count' that sums 'free_yes', 'free_unclear', and 'free_no'
    # counts['total_count'] = counts.sum(axis=1, numeric_only=True)

    # Sort the dataframe by 'total_count' in descending order
    # counts = counts.sort_values(by='total_count', ascending=False).reset_index(drop=True)

    return counts


def get_top_archives(df, ds_type):
    is_ds_type = df['Type'] == ds_type
    top_names = datasets.loc[is_ds_type, 'name'].value_counts().head(10)

    # Find corresponding locations for each top name
    locations = []
    for name in top_names.index:
        location = datasets.loc[is_ds_type & (datasets['name'] == name), 'location'].iloc[0]
        locations.append(location)

    # Create dataframe for top 10 aerial names with country and count
    top_df = pd.DataFrame({'Rank': range(1, len(top_names) + 1),
                           'Location': locations,
                           'Name': top_names.index,
                           'Count': top_names.values})

    return top_df


# Import excel file as pandas dataframe
datasets, = tools.load_dataset(subset=['datasets']).values()

# =====================================================================================================================
#            PLOT THE NUMBER OF DATASET PER ARCHIVE LOCATION & AVAILABILITY
# =====================================================================================================================
# ....................
# prepare the dataset
# Create a new dataframe with only information of 'Type' and 'No. Images'.
columns = ['Type', 'Archive Location', 'Freely Available?', 'Archive Name']
datasets = datasets[columns].copy()

# rename the column name
datasets.rename(columns={'Archive Location': 'location',
                         'Freely Available?': 'free',
                         'Archive Name': 'name'},
                inplace=True)

# fill missing values
datasets['location'].fillna('Not reported', inplace=True)

# Select aerial and spy images
aerial_counts = get_counts(datasets, 'Aerial')
satellite_counts = get_counts(datasets, 'Satellite')

# rename the satellite columns
old = [c for c in satellite_counts if 'free' in c]
new = [c + '_spy' for c in old]
satellite_counts.rename(columns=dict(zip(old, new)), inplace=True)

# ==============================================================
# --- # Merge dataframes using the 'location' column
merged = aerial_counts.merge(satellite_counts, left_on='location', right_on='location', how='outer').fillna(0)
merged['total_count'] = merged.sum(axis=1, numeric_only=True)

# sort by total count (ascending) and location (descending)
# note: this is reversed here so that the plot shows the correct order
merged = merged.sort_values(by=['total_count', 'location'], ascending=[True, False]).reset_index(drop=True)

# =====================================================================================================================
#            PLOT THE NUMBER OF DATASET PER ARCHIVE LOCATION & AVAILABILITY
# =====================================================================================================================

fontText = 24
# Define colors with adjusted alpha values for the last three values
col_aerial = '#108896'
col_spy = '#7456F1'
color_notspec = '#1A354A'
color_notspec_alpha = ['#1A354ACC', '#1A354A99', '#1A354A66']

colors_spy_free_no_unclear = ['#7456F1', '#1A354A', '#1A354A66']
colors_aerial_free_no_unclear = ['#108896', '#1A354A', '#1A354A66']

sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')

fig, ax = plt.subplots(figsize=(16, 9.3))

# Bar plot in stack manner combined aerial and spy in the same barplot
merged.plot(x='location', y=['free_yes', 'free_no', 'free_unclear', 'free_yes_spy', 'free_no_spy', 'free_unclear_spy'],
               kind='barh', stacked=True, width=0.8, color=colors_aerial_free_no_unclear + colors_spy_free_no_unclear,
               fontsize=14, ax=ax) # title='No. of dataset per archive', xlabel="Number of datasets", ylabel="Archive location (Country)"

# Create custom legend labels for the first three values
# plt.legend(loc='lower right')
custom_legend_labels = {'free_yes': 'Free aerial', 'free_yes_spy': 'Free satellite',
                        'free_no': 'Not free', 'free_unclear': 'Not reported'}
# Get handles and labels for the plot
handles, labels = ax.get_legend_handles_labels()

# Set axis label, and defining the font size
ax.set_ylabel('Archive location (country)', fontsize=fontText) # fontweight='bold')
ax.set_xlabel('Number of datasets', fontsize=fontText)

# Create a custom legend with modified labels for the first three values
custom_legend = ax.legend(handles[:4], [custom_legend_labels.get(label, label) for label in labels[:4]],
                          loc='lower left', bbox_to_anchor=(0.03, 0))
sns.despine(offset=10, trim=False)  # to make the axis separated

# Save the figure
plt.savefig(Path('figures', 'Fig12_ArchiveAvailability.png'),
            dpi=600, bbox_inches='tight')

# =====================================================================================================================
#            Find the 10 most frequent Archive names for each type (aerial and satellite)
# =====================================================================================================================
top_aerial = get_top_archives(datasets, 'Aerial')
top_aerial.to_csv(Path('data', 'top_aerial_archives.csv'), index=False)

top_satellite = get_top_archives(datasets, 'Satellite')
top_satellite.to_csv(Path('data', 'top_satellite_archives.csv'), index=False)
