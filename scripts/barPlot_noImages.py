# import packages
import pandas as pd
from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ..........................
# Set directory and filename
file_folder = 'C:/Users/Livia/Desktop/2023_historicalImagesPaper/Data_TempForPlot/googleSheet_download'
excelFileName = 'Review_HistoricAirPhotos_download17May2023.xlsx'
outputPlot_path = Path(r"C:/Users/Livia/Desktop/2023_historicalImagesPaper/Figure_paper/Figure_BarPlot_noImages")

# Import excel file as pandas dataframe
df_dataset = pd.read_excel(os.path.join(file_folder, excelFileName), sheet_name='datasets')
df_dataset.head()

# ....................
# prepare the dataset
# select relevant columns
df_dataset_slct = df_dataset[['Key', 'Dataset Number', 'Type', 'Archive Location',
                              'Freely Available?', 'Archive Name', 'No. Images']].copy()
df_dataset_slct.head()

# extract the key and save it in a new column in the dataframe
unique_key_value = df_dataset_slct.Key.str[0:-1].str.split('.', expand=True)
df_dataset_slct['unique_key'] = unique_key_value[0]
# Select aerial images and satellite type
df_dataset_TypeNoImagesKey = df_dataset_slct[['Type', 'No. Images', 'unique_key']]
df_aerial = df_dataset_TypeNoImagesKey[(df_dataset_TypeNoImagesKey['Type'] == 'Aerial')]
df_satellite = df_dataset_TypeNoImagesKey[(df_dataset_TypeNoImagesKey['Type'] == 'Satellite')]

# --- create list of unique key of aerial & satellite
df_aerial_uniqueKey = df_aerial['unique_key'].unique()
df_satellite_uniqueKey = df_satellite['unique_key'].unique()

# add a new column ('uniquekey_ID') with a consecutive number for unique keys
df_aerial['uniquekey_ID'] = 1
n = 1
for i in df_aerial_uniqueKey:
    for j in df_aerial.index:
        if df_aerial.loc[j, 'unique_key'] == i:
            df_aerial.loc[j, 'uniquekey_ID'] = n
    n = n + 1

df_satellite['uniquekey_ID'] = 1
n = 1
for i in df_satellite_uniqueKey:
    for j in df_satellite.index:
        if df_satellite.loc[j, 'unique_key'] == i:
            df_satellite.loc[j, 'uniquekey_ID'] = n
    n = n + 1

# --- Count the number of Studies
maxAerialStudy = df_aerial['uniquekey_ID'].max()    # 113
df_aerial_cnt = df_aerial.groupby(['uniquekey_ID']).size().reset_index(name='count')

maxSatelliteStudy = df_satellite['uniquekey_ID'].max()    # 44
df_satellite_cnt = df_satellite.groupby(['uniquekey_ID']).size().reset_index(name='count')

# --- Calculate the maximum no. of images per each unique ID
df_aerial_maxNoImage = df_aerial.groupby('uniquekey_ID').max()['No. Images']
df_satellite_maxNoImage = df_satellite.groupby('uniquekey_ID').max()['No. Images']

# --- Create a new dataframe with the unique_ID i.e. the number of studies and the max of No. of images
df_aerial_imageID = pd.DataFrame()
df_satellite_imageID = pd.DataFrame()

# list of sorted unique ID key of aerial & satellite
listSortedID = df_aerial['uniquekey_ID'].unique()
df_aerial_imageID['uniquekey_ID'] = listSortedID
df_aerial_imageID['max'] =df_aerial_maxNoImage

listSortedID = df_satellite['uniquekey_ID'].unique()
df_satellite_imageID['uniquekey_ID'] = listSortedID
df_satellite_imageID['max'] = df_satellite_maxNoImage

maxNoImages_aerial = df_aerial_imageID['max'].max()          # 8507.0
maxNoImages_satellite = df_satellite_imageID['max'].max()    # 424.0

# ........................
# Prepare the data to plot

# --- Select the bin width
# bins_a = [0, 5, 10, 15, 20, 40, 60, 100, 400, 8600]
bins_a = [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 10000]
bins_s = [0, 8, 16, 24, 32, 40, 48, 208, 425]

# --- Group by and count the data according to the bin
df_a = df_aerial_imageID['max'].groupby(pd.cut(df_aerial_imageID['max'], bins=bins_a)).count()
df_s = df_satellite_imageID['max'].groupby(pd.cut(df_satellite_imageID['max'], bins=bins_s)).count()

# --- Count the number of nan
nanCount_a = df_aerial_imageID['max'].isna().sum()
nanCount_series_a = {len(df_a)+2: nanCount_a}

nanCount_s = df_satellite_imageID['max'].isna().sum()
nanCount_series_s = {len(df_s)+2: nanCount_s}

# --- Append the nan values
df_nanCount_series_a = pd.Series(nanCount_series_a)
df_a_nan = df_a.append(df_nanCount_series_a)

df_nanCount_series_s = pd.Series(nanCount_series_s)
df_s_nan = df_s.append(df_nanCount_series_s)


# --- Define the color style
col_aerial = '#69B3CA'
col_satell = '#7456F1'
col_nan = [224/255, 224/256, 224/256]
colors_a = [col_aerial, col_aerial,col_aerial,col_aerial,col_aerial,col_aerial,
          col_aerial,col_aerial,col_aerial,col_aerial, col_aerial,col_nan]
colors_s = [col_satell, col_satell, col_satell, col_satell,col_satell,
            col_satell, col_satell, col_satell, col_nan]
fontS = 14

# --- Bar plot
sns.set(font_scale=1.3, style="white")
sns.set_style('ticks')  # white style with tick marks
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 4))

# plot the bar
df_a_nan.plot(kind='bar', edgecolor='white',linewidth=1, color=colors_a, width=1, ax=ax1)     # width=1 to remove spaces
df_s_nan.plot(kind='bar', edgecolor='white',linewidth=1, color=colors_s, width=1, ax=ax2)

# axis tick
xtickLabels_arial = ['20', '40', '60', '80', '100', '120', '140', '160', '180', '200', '8500','Nan']
xtickLabels_satell = ['8', '16', '24', '32', '40', '48', '=208', '=424', 'Nan']

ax1.set_xticks(ticks=np.arange(0, len(df_a_nan)))
ax1.set_xticklabels(xtickLabels_arial)
ax2.set_xticks(ticks=np.arange(0, len(df_s_nan)))
ax2.set_xticklabels(xtickLabels_satell)

# plot labels
ax1.set_xlabel('No. of aerial images', fontsize=fontS)
ax1.set_ylabel('No. of study', fontsize=fontS)
ax1.set_title('Aerial images', fontsize=fontS)
ax2.set_xlabel('No. of satellite images', fontsize=fontS)
ax2.set_ylabel('No. of study', fontsize=fontS)
ax2.set_title('Satellite images', fontsize=fontS)

sns.despine(offset=10, trim=False)  # to make the axis separated

# --- Save the figure
plt.savefig(outputPlot_path/ 'BarPlot_MaxNoImagesPerStudy.png', dpi=300, bbox_inches='tight')