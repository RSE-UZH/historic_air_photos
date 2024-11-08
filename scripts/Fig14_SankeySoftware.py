import pandas as pd
from pathlib import Path
import os
import numpy as np
import tools


# check if a software name is in a string
def check_software(s):
    software_names = ['ERDAS', 'Pix4D', 'PhotoMod', 'Agisoft', 'SocetSet', 'MicMac', 'SURE',
                      'Self', 'IMAGINE', 'Inpho', 'VirtuoZo', 'VisualSFM', 'PCI Geomatica',
                      'Corona Stereo Pipeline (CoSP)', 'Remote Sensing Software Package Graz (RSG)',
                      'HEXIMAP', 'Ames Stereo Pipeline (ASP)']

    for name in software_names:
        if name.lower() in s.lower():
            return name
    return 'Other'


# ....................
# prepare the dataset
datasets, processing = tools.load_dataset(subset=['datasets', 'processing']).values()

# drop terrestrial datasets
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# select the relevant columns, shortening the name
datasets = datasets[['Key', 'PubKey', 'Type']].set_index('Key')
processing = processing[['Key', 'Method', 'Software', 'GCPs', 'Fiducial Marks']].set_index('Key')
processing.rename(columns={'Fiducial Marks': 'fiducial'}, inplace=True)

# join on the dataset keys
merged = datasets.join(processing).dropna(subset=['Type'])

# =========================================================================
# Replace NaN values with a string
merged['Software'].fillna('not defined', inplace=True)

# clean up the software names
merged['Software'] = merged['Software'].apply(lambda s: check_software(s))
merged['Software'].replace({'IMAGINE': 'ERDAS'}, inplace=True)

# IMAGINE -> ERDAS
# merge smaller numbers of software into Other
# first, get the top 10 values
top_counts = merged['Software'].value_counts().head(n=10)

# get the names of everything that isn't in the top 10
bottom = merged['Software'].value_counts()[merged['Software'].value_counts() < top_counts.values[-1]].index.to_list()

# replace those names with Other
merged['Software'].replace(dict(zip(bottom, len(bottom) * ['Other'])), inplace=True)

# --- Count the Type per Method
type_count_method = merged.groupby(['Type', 'Method']).size().reset_index(name='count')
type_count_method = type_count_method[['Type', 'count', 'Method']].sort_values(by=['count'], ascending=False).reset_index(drop=True)

# add a [] in the text
type_count_method['count'] = type_count_method['count'].apply(lambda x: f"[{str(x)}]")

# --- Count the Method per software
method_count_software = merged.groupby(['Method', 'Software']).size().reset_index(name='count')
# reorder the columns
method_count_software = method_count_software.reindex(columns=['Method', 'count', 'Software_Name'])
method_count_software = method_count_software.sort_values(by=['count'], ascending=False)  # sort df by count
# add a [] in the text
method_count_software['count'] = method_count_software['count'].apply(lambda x: f"[{str(x)}]")

# --- Count the software per Fiducial
software_counts_fiducial = merged.groupby(['Software', 'fiducial']).size().reset_index(name='count')
# reorder the columns
software_counts_fiducial = software_counts_fiducial.reindex(columns=['Software', 'count', 'fiducial'])
software_counts_fiducial = software_counts_fiducial.sort_values(by=['count'], ascending=False)  # sort df by count
# add a [] in the text
software_counts_fiducial['count'] = software_counts_fiducial['count'].apply(lambda x: f"[{str(x)}]")

# --- Concatenate the values into a single dataframe
result_sankey = np.concatenate([type_count_method, method_count_software, software_counts_fiducial], axis=0)
result_sankey_df = pd.DataFrame(result_sankey)

# save the combined dataframe to a CSV file
outfilename = Path('figures', 'data', "dfSankey_allResults_typeMethodSoftwareFiducial.csv")
result_sankey_df.to_csv(outfilename, sep=" ", encoding='utf-8', index=False, header=False)

# --- prepare the color for the data_type & for applications. Copy this manually in the online tool
#: Satellite #7456F1
#: Aerial #1c9099
colours_method = {'Photogrammetric ': '#CC79A7',
                  'Combined': '#0072B2',
                  'SfM': '#56B4E9',
                  'Manual': '#E69F00',
                  'Time-SIFT': '#009E73'}

df_color = pd.DataFrame.from_dict(colours_method, orient='index', columns=['color'])
df_color.index.name = 'application'
df_color.reset_index(inplace=True)

# add a : before the application string e.g. : Archeology
df_color['application'] = df_color['application'].apply(lambda x: f": {str(x)}")
# export dataframe as csv and delimiter space
fn_color = Path('figures', 'data', "dfSankeySoftware_color_applications.csv")
df_color.to_csv(fn_color, sep=" ", encoding='utf-8', index=False)
