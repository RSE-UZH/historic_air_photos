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
    is_specified = df['name'] != 'Not specified'
    top_names = df.loc[is_ds_type & is_specified, 'name'].value_counts().head(10)

    # Find corresponding locations for each top name
    locations = []
    for name in top_names.index:
        location = df.loc[is_ds_type & (df['name'] == name), 'location'].iloc[0]
        locations.append(location)

    # Create dataframe for top 10 aerial names with country and count
    top_df = pd.DataFrame({'Rank': range(1, len(top_names) + 1),
                           'Location': locations,
                           'Name': top_names.index,
                           'Count': top_names.values})

    return top_df


# Import excel file as pandas dataframe
datasets, archives = tools.load_dataset(subset=['datasets', 'archives']).values()

# =====================================================================================================================
#            PLOT THE NUMBER OF DATASET PER ARCHIVE LOCATION & AVAILABILITY
# =====================================================================================================================
# ....................
# prepare the dataset
# Create a new dataframe with only information of 'Type' and 'No. Images'.
datasets = datasets[['Type', 'Freely Available?', 'ArchiveKey']].copy()

merged = datasets.merge(archives[['ArchiveKey', 'Country', 'LongName']],
                        left_on='ArchiveKey', right_on='ArchiveKey')

# rename the column name
merged.rename(columns={'Country': 'location',
                       'Freely Available?': 'free',
                       'LongName': 'name'},
              inplace=True)

# fill missing values
merged['location'] = merged['location'].fillna('Not reported')

# Select aerial and spy images
aerial_counts = get_counts(merged, 'Aerial')
satellite_counts = get_counts(merged, 'Satellite')

# rename the satellite columns
old = [c for c in satellite_counts if 'free' in c]
new = [c + '_spy' for c in old]
satellite_counts.rename(columns=dict(zip(old, new)), inplace=True)

# ==============================================================
# --- # Merge dataframes using the 'location' column
merged_counts = aerial_counts.merge(satellite_counts, left_on='location', right_on='location', how='outer').fillna(0)
merged_counts['total_count'] = merged_counts.sum(axis=1, numeric_only=True)

# sort by total count (ascending) and location (descending)
# note: this is reversed here so that the plot shows the correct order
merged_counts = merged_counts.sort_values(by=['total_count', 'location'],
                                          ascending=[True, False]).reset_index(drop=True)

# =====================================================================================================================
#            PLOT THE NUMBER OF DATASET PER ARCHIVE LOCATION & AVAILABILITY
# =====================================================================================================================

fontText = 18
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
merged_counts.plot(x='location', y=['free_yes', 'free_no', 'free_unclear', 'free_yes_spy',
                                    'free_no_spy', 'free_unclear_spy'],
               kind='barh', stacked=True, width=0.8, color=colors_aerial_free_no_unclear + colors_spy_free_no_unclear,
               fontsize=14, ax=ax)

# Create custom legend labels for the first three values
# plt.legend(loc='lower right')
custom_legend_labels = {'free_yes': 'Free aerial', 'free_yes_spy': 'Free satellite',
                        'free_no': 'Not free', 'free_unclear': 'Not reported'}
# Get handles and labels for the plot
handles, labels = ax.get_legend_handles_labels()

# Set axis label, and defining the font size
ax.set_ylabel('Archive location (country)', fontsize=fontText) # fontweight='bold')
ax.set_xlabel('Number of datasets', fontsize=fontText)

# set the x-axis limits
ax.set_xlim(0, 160)

# Create a custom legend with modified labels for the first three values
custom_legend = ax.legend(handles[:4], [custom_legend_labels.get(label, label) for label in labels[:4]],
                          loc='lower left', bbox_to_anchor=(0.03, 0))
sns.despine(offset=10, trim=False)  # to make the axis separated

# Save the figure
plt.savefig(Path('figures', 'Fig10_ArchiveAvailability.png'),
            dpi=600, bbox_inches='tight')

# =====================================================================================================================
#            Find the 10 most frequent Archive names for each type (aerial and satellite)
# =====================================================================================================================
top_aerial = get_top_archives(merged, 'Aerial')
top_aerial.to_csv(Path('figures','data', 'top_aerial_archives.csv'), index=False)

top_satellite = get_top_archives(merged, 'Satellite')
top_satellite.to_csv(Path('figures','data', 'top_satellite_archives.csv'), index=False)
