import pandas as pd
from pathlib import Path
import os
import numpy as np


aerial_color = '#108896'
satellite_color = '#7456F1'


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


# --- Convert the DPI to microns
# The formula to calculate DPI from microns is:
# a) Divide the number of microns by 1,000,000
# b) Multiply that amount by 39.37 (number of inches in a meter)
# c) Calculate the inverse of that number.

# formula --> microns per dot= 25,400 microns / DPI as There are 25,400 microns in an inch.
def microns_to_dpi(micrometer):
    dpi_conversion_factor = 25400  # 1 inch = 25,400 micrometers
    return dpi_conversion_factor / micrometer if micrometer is not None and micrometer > 0 else np.nan


def bar_text(ax, bar, label):
    width = bar.get_width()
    xmin, xmax = ax.get_xlim()

    axwidth = xmax - xmin

    xloc = bar.get_x()
    yloc = bar.get_y() + 1.1 * (bar.get_height() / 2)

    if width / axwidth < 0.1:
        halign = 'left'
        xloc += 1.1 * width
        color = 'k'
    else:
        halign = 'right'
        xloc += 0.98 * width
        color = 'w'

    ax.text(xloc, yloc, label, verticalalignment='center', horizontalalignment=halign, color=color)

    return ax


def accuracy_measures(table):
    # source accuracy, gcp residuals, cp residuals, comparison accuracy, comparison residuals
    fields = ['Ground control accuracy [m]', 'Residuals to GCPs [m]', 'Residuals to CPs [m]',
              'Accuracy comparison data [m]', 'Residuals to comparison [m]']

    for meas in fields:
        xyz = [f"{meas} X", f"{meas} Y", f"{meas} Z"]
        xy_z = [f"{meas} XY", f"{meas} Z"]

        # reported as 3d value
        is_3d = ~table[f"{meas} XYZ"].isna()

        # reported as x, y, z individually
        is_xyz = (~table[xyz].isna()).all(axis=1)

        # planimetric and height are reported
        is_xy_z = ((~table[xy_z].isna()).all(axis=1) &
                   table[[f"{meas} X", f"{meas} Y", f"{meas} XYZ"]].isna().all(axis=1))

        # only the planimetric value is reported
        is_xy = ((~table[f"{meas} XY"].isna()) &
                 table[xyz + [f"{meas} XYZ"]].isna().all(axis=1))

        # only the height is reported
        is_z = ((~table[f"{meas} Z"].isna()) &
                table[[f"{meas} X", f"{meas} Y", f"{meas} XY", f"{meas} XYZ"]].isna().all(axis=1))

        table.loc[is_3d, f"{meas} avg"] = table.loc[is_3d, f"{meas} XYZ"]

        # add x, y, z in quadrature to get 3d
        table.loc[is_xyz, f"{meas} avg"] = np.sqrt(table.loc[is_xyz, f"{meas} X"] ** 2 +
                                                   table.loc[is_xyz, f"{meas} Y"] ** 2 +
                                                   table.loc[is_xyz, f"{meas} Z"] ** 2)

        # add planimetric and height in quadrature to get 3d
        table.loc[is_xy_z, f"{meas} avg"] = np.sqrt(table.loc[is_xy_z, f"{meas} XY"] ** 2 +
                                                    table.loc[is_xy_z, f"{meas} Z"] ** 2)

        # if only some values are reported, we assume that the other coordinates are equal and add in quadrature
        table.loc[is_xy, f"{meas} avg"] = np.sqrt(2) * table.loc[is_xy, f"{meas} XY"]
        table.loc[is_z, f"{meas} avg"] = np.sqrt(3) * table.loc[is_z, f"{meas} Z"]

        # round to 3 decimal places
        table[f"{meas} avg"] = table[f"{meas} avg"].round(3)

    return table
