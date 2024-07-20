# import packages
import pandas as pd
from pathlib import Path
import os
import matplotlib.pyplot as plt
import seaborn as sns


# ..........................
# Set directory and filename
file_folder = 'C:/Users/Livia/Desktop/2023_historicalImagesPaper/Data_TempForPlot/googleSheet_download'
outputPlot_path = Path(r"C:/Users/Livia/Desktop/2023_historicalImagesPaper/Figure_paper/Figure12_timelineStudies")
excelFileName = 'Review_HistoricAirPhotos_download7May2023.xlsx'

# ....................................................
# Import excel file as pandas dataframe using datetime
df = pd.read_excel(os.path.join(file_folder, excelFileName), sheet_name='datasets',
                   parse_dates=['Acquisition Start Year', 'Acquisition End Year'])
df.head()

# ....................
# prepare the dataset
df = df[['Key', 'Dataset Number', 'Type',
         'Acquisition Start Year', 'Acquisition End Year',
         'GSD [m]', 'Scale']].copy()

# rename 'Acquisition Start Year', 'Acquisition End Year' using shorter name
df.rename(columns={'Acquisition Start Year':'start_date', 'Acquisition End Year': 'end_date',
                   'Dataset Number': 'no_dataset', 'GSD [m]': 'gsd'}, inplace=True)

# Drop the rows where 'Data Type' is 'Terrestrial'
df = df.loc[df['Type'] != 'Terrestrial']

# Extract the unique key and add it the a new column
unique_key_value = df.Key.str[0:-1].str.split('.', expand = True)
df['unique_key'] = unique_key_value[0]

# Sort the dataframe by Type and dates
df_sortDate = df.sort_values(['Type', 'start_date'], ascending=[True, True])
# # create list of unique key of aerial and satellite
listKey_sorted_all = df_sortDate['unique_key'].unique()

df_sortDate['uniquekey_ID'] = 1
n = 1
for i in listKey_sorted_all:
    for j in df_sortDate.index:
        if df_sortDate.loc[j,'unique_key']== i:
            df_sortDate.loc[j,'uniquekey_ID']=n
    n = n + 1

df_sortDate['uniquekey_ID'][df_sortDate['Type'] == 'Aerial'].max()    # 113
y_max = df_sortDate['uniquekey_ID'][df_sortDate['Type'] == 'Satellite'].max()    # 150

# ................
# Plot the results

# Define the style
lineCol_aer = '#69B3CA'
lineCol_satel = '#7456F1'
labels_legend = ['Aerial', 'Satellite']
linW = 1

# Plot
sns.set(font_scale=1.2, style="white"), sns.set_style('ticks')
fig, ax = plt.subplots(figsize=(12, 5))
 # white style with tick marks
for n in range(1, y_max):
    selection = df_sortDate.loc[(df_sortDate['uniquekey_ID'] == n) & (df_sortDate['Type'] == 'Aerial')]
    #print(selection)
    plt.plot( selection['start_date'], selection['uniquekey_ID'], color=lineCol_aer, linewidth=linW, marker='o', alpha=0.6)

    selection = df_sortDate.loc[(df_sortDate['uniquekey_ID'] == n) & (df_sortDate['Type'] == 'Satellite')]
    plt.plot(selection['start_date'], selection['uniquekey_ID'], color=lineCol_satel, linewidth=linW, marker='o', alpha=0.6)

labels_legend = ['Aerial', 'Satellite']
plt.legend(labels_legend,loc='upper left')
plt.ylabel('Number of studies', fontsize=13)
plt.xlabel('Acquisition year', fontsize=13)    #weight='bold'
# plt.title("Timeline of historical images for each study", fontsize=20)

# To make the axis separated
sns.despine(offset=10, trim=False)
# Save the figure
plt.savefig(outputPlot_path/ 'Figure_timeLine_Studies.png', dpi=300, bbox_inches='tight')
