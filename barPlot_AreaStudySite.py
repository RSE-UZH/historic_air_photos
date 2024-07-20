# import packages
import pandas as pd
from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ..........................
# Set directory and filename
file_folder = 'C:/Users/Livia/Desktop/2023_historicalImagesPaper/Data_TempForPlot'
excelFileName_area = 'AreaCaseStudy_key.xlsx'
excelFileName_data = 'Review_HistoricAirPhotos_download24Feb2023.xlsx'
outputPlot_path = Path(r"C:/Users/Livia/Desktop/2023_historicalImagesPaper/Figure_paper/Figure2_Areakm2_studySites")

# .....................................
# Import excel file as pandas dataframe
df = pd.read_excel(os.path.join(file_folder, excelFileName_area), sheet_name='clean_data')
df.head()
df_data = pd.read_excel(os.path.join(file_folder, 'googleSheet_download', excelFileName_data),
                        sheet_name='datasets')

# .....................................
# Prepare the data with the area values

# Separate the values and the Key
keys = [df['Pub Key']]

# Convert the values to km2
values = df['area']
values_km2 = [val / 1000000 for val in values]

# Rename the column "Pub Key" as "Key"
df.rename(columns={'Pub Key':'unique_key'}, inplace=True)

# ......................................................
# Extract the Key and the camera type from the satellite
df_data_select = df_data[['Key', 'Type']].copy()

# find unique key and create a new column in the dataframe
unique_key_value = df_data_select.Key.str[0:-1].str.split('.', expand=True)
df_data_select['unique_key'] = unique_key_value[0]

# drop duplicated unique_key --> drop_duplicates()
df_data_select_unique = df_data_select.copy()
df_data_select_unique.drop_duplicates(subset="unique_key", keep='first', inplace=True)

# ...........................................................
# merge two pandas dataframe based on the column values "key"
merged_df = pd.merge(df, df_data_select, on='unique_key', how='left')
merged_df_AERIAL = merged_df[merged_df['Type'] == 'Aerial']
merged_df_SPY = merged_df[merged_df['Type'] == 'Satellite']

# .........................
# Histogram using log scale

# --- Preparing the dataset
# aerial --> 50 bins with logarithmic scaling on the x-axis
n_bins = 50
log_bins_aerial = np.logspace(np.log10(merged_df_AERIAL['area'].min()),
                      np.log10(merged_df_AERIAL['area'].max()), n_bins)

# satellite --> 50 bins with logarithmic scaling on the x-axis
log_bins_satell = np.logspace(np.log10(merged_df_SPY['area'].min()),
                      np.log10(merged_df_SPY['area'].max()), n_bins)

# Color style
cr_aerial = '#69B3CA'
cr_satell = '#7456F1'
fontS = 14

# Plot
sns.set(font_scale=1.2, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 4))

# AERIAL
ax1.hist(merged_df_AERIAL['area'].values, bins=log_bins_aerial, color=cr_aerial)
ax1.set_xscale('log')
# SATELLITE
ax2.hist(merged_df_SPY['area'].values, bins=log_bins_satell, color=cr_satell)
ax2.set_xscale('log')

# plot labels
ax1.set_xlabel('Area range (km²) (log scale)', fontsize=fontS)
ax1.set_ylabel('Frequency', fontsize=fontS)
ax1.set_title('Aerial images', fontsize=fontS)
ax2.set_xlabel('Area range (km²) (log scale)', fontsize=fontS)
ax2.set_ylabel('Frequency', fontsize=fontS)
ax2.set_title('Satellite images', fontsize=fontS)

# to make the axis separated
sns.despine(offset=10, trim=False)

# save the figure
plt.savefig(outputPlot_path/'histogram_AreaStudySite_km2.png', dpi=300, bbox_inches='tight')