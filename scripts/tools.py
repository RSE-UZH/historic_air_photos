import pandas as pd
from pathlib import Path
import os
import numpy as np


def load_dataset(subset=None, relevant=True) -> dict:
    """
    Load the excel datasheet, cleaning empty/missing rows and renaming columns.

    The dataset (data/Review_Historic_Air_Photos.xlsx) has the following sheets:
        - publications
        - geographic
        - scientific
        - datasets
        - processing
        - accuracy
        - outputs

    By default, all sheets are loaded.

    :param subset: the subset of sheets to load (default: All)
    :param bool relevant: drop non-relevant studies from the dataset on loading (default: True)
    :return:
    """
    fn_data = Path('data', 'Review_Historic_Air_Photos.xlsx')

    sheet_names = ['publications', 'geographic', 'scientific', 'datasets', 'processing',
                   'accuracy', 'outputs']
    if subset is None:
        subset = sheet_names

    dataset = pd.read_excel(fn_data, sheet_name=None)

    # remove blanks from 'publications'
    blank_pubs = dataset['publications']['Human Key'] == ' ,  ()'
    dataset['publications'].drop(dataset['publications'][blank_pubs].index, inplace=True)
    dataset['publications'].rename(columns={'Key': 'PubKey'}, inplace=True)

    # extract the publication key for all sheets except the first one
    # and remove all rows where this is nan
    for sheet in sheet_names[1:]:
        dataset[sheet]['PubKey'] = dataset[sheet]['Publication Key'].str.extract(r'\(([^()]{8})\)')
        dataset[sheet].dropna(subset=['PubKey'], inplace=True)

    # drop the helper columns from the publications table
    dataset['publications'].drop(['interesting?', '.not_relevant', 'geographic', 'scientific',
                                  'dataset', 'processing', 'outputs', 'accuracy'],
                                 axis=1, inplace=True)

    # drop the .relevant column from the geographic table
    dataset['geographic'].drop(['.not_relevant'], axis=1, inplace=True)
    dataset['geographic'].rename(columns={'Notes': 'Geographic Notes'}, inplace=True)

    # rename columns in the scientific table
    dataset['scientific'].rename(columns={'Notes': 'Scientific Notes', 'Description': 'Study Description'},
                                 inplace=True)

    # make the relevant column a boolean
    dataset['scientific']['Relevant'].replace({'no': False, 'yes': True}, inplace=True)

    # drop the helper columns from the datasets table
    dataset['datasets'].drop(['processing', 'outputs', 'accuracy'], axis=1, inplace=True)

    # rename columns in the datasets table
    dataset['datasets'].rename(columns={'Camera calib?': 'Camera Calibration',
                                        'original media': 'Original Media',
                                        'Notes': 'Dataset Notes'}, inplace=True)
    # rename columns in the processing table
    dataset['processing'].rename(columns={'simplified geometric preprocessing': 'Geometric Pre-processing',
                                          'simplified radiometric preprocessing': 'Radiometric Pre-processing'},
                                 inplace=True)

    # rename columns in the accuracy table
    dataset['accuracy'].rename(columns={'comparison metric': 'Comparison Metric'}, inplace=True)

    # rename columns in the outputs table
    dataset['outputs'].rename(columns={'note': 'Output Notes'}, inplace=True)

    if relevant:
        relevant_keys = dataset['scientific'].loc[dataset['scientific']['Relevant'], 'PubKey'].to_list()
        for sheet in sheet_names:
            dataset[sheet].drop(dataset[sheet].index[~dataset[sheet]['PubKey'].isin(relevant_keys)], inplace=True)

    return dict((sheet, dataset[sheet].reset_index(drop=True)) for sheet in subset)

