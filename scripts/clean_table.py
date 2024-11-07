import os
import pandas as pd
import numpy as np
import tools


# load all sheets from the excel file as a dict
df_dict = pd.read_excel('data/Review_Historic_Air_Photos.xlsx', sheet_name=None)

# remove blanks from 'publications'
blank_pubs = df_dict['publications']['Human Key'] == ' ,  ()'
df_dict['publications'].drop(df_dict['publications'][blank_pubs].index, inplace=True)

# remove blank rows from the datasets table
blank_data = df_dict['datasets']['Key'].isna()
df_dict['datasets'].drop(df_dict['datasets'][blank_data].index, inplace=True)

# remove blank rows from the datasets table
blank_acc = df_dict['accuracy']['DatasetKey'].isna()
df_dict['accuracy'].drop(df_dict['accuracy'][blank_acc].index, inplace=True)

# extract the publication key from the geographic and scientific tables
df_dict['geographic']['Pub Key'] = df_dict['geographic']['Publication Key'].str.extract(r'\(([^()]{8})\)')
df_dict['scientific']['Pub Key'] = df_dict['scientific']['Publication Key'].str.extract(r'\(([^()]{8})\)')

# first, remove all the blank rows
for sheet in df_dict.keys():
    df_dict[sheet].dropna(how='all', inplace=True)

    # delete the git blame column
    if 'git blame' in df_dict[sheet].columns:
        del df_dict[sheet]['git blame']

    # delete the publication key from each of the tables
    if 'Publication Key' in df_dict[sheet].columns:
        del df_dict[sheet]['Publication Key']

# drop the helper columns from the publications table
df_dict['publications'].drop(['interesting?', '.not_relevant', 'geographic', 'scientific',
                              'dataset', 'processing', 'outputs', 'accuracy'],
                             axis=1, inplace=True)

# drop the .relevant column from the geographic table
df_dict['geographic'].drop(['.not_relevant'], axis=1, inplace=True)
df_dict['geographic'].rename(columns={'Notes': 'Geographic Notes'}, inplace=True)

# rename columns in the scientific table
df_dict['scientific'].rename(columns={'Notes': 'Scientific Notes', 'Description': 'Study Description'}, inplace=True)

# drop the helper columns from the datasets table
df_dict['datasets'].drop(['processing', 'outputs', 'accuracy'], axis=1, inplace=True)

# add a pub key column to the datasets table
df_dict['datasets']['Pub Key'] = df_dict['datasets']['Key'].str.split('.', expand=True)[0]

# rename columns in the datasets table
df_dict['datasets'].rename(columns={'Camera calib?': 'Camera Calibration',
                                    'original media': 'Original Media',
                                    'Notes': 'Dataset Notes'}, inplace=True)

# rename columns in the processing table
df_dict['processing'].rename(columns={'simplified geometric preprocessing': 'Geometric Pre-processing',
                                      'simplified radiometric preprocessing': 'Radiometric Pre-processing'},
                             inplace=True)

# rename columns in the accuracy table
df_dict['accuracy'].rename(columns={'comparison metric': 'Comparison Metric'}, inplace=True)

# rename columns in the outputs table
df_dict['outputs'].rename(columns={'note': 'Output Notes'}, inplace=True)

# join the dataset columns:
datasets_df = df_dict['datasets'].set_index('Key')\
    .join(df_dict['processing'].set_index('Key'), rsuffix='_proc')\
    .join(df_dict['outputs'].set_index('Key'), rsuffix='_out')\
    .reset_index()\
    .rename(columns={'Key': 'DatasetKey'})

# join the publications, geographic, and scientific tables to the datasets_df
pubs_df = df_dict['publications'].set_index('Key')\
    .join(df_dict['geographic'].set_index('Pub Key'), rsuffix='_geog')\
    .join(df_dict['scientific'].set_index('Pub Key'), rsuffix='_sci')\
    .join(datasets_df.set_index('Pub Key'), rsuffix='_data')

# join the accuracy table to the other tables
pubs_df = pubs_df.reset_index(names='Key')\
    .merge(df_dict['accuracy'], left_on='DatasetKey', right_on='DatasetKey', suffixes=('', '_acc'))\
    .set_index('Key')

# get the final accuracy measurements
pubs_df = tools.accuracy_measures(pubs_df)

# save to a csv file after replacing NaN with NA
pubs_df.fillna('NA').sort_values('Human Key').to_csv(os.path.join('data', 'Review_Historic_Air_Photos.csv'),
                                                     index_label='Key')
