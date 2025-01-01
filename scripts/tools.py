import pandas as pd
from pathlib import Path
from pyproj import Proj
from shapely.geometry import shape
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
        - archives

    By default, all sheets are loaded.

    :param subset: the subset of sheets to load (default: All)
    :param bool relevant: drop non-relevant studies from the dataset on loading (default: True)
    :return:
    """
    fn_data = Path('data', 'Review_Historic_Air_Photos.xlsx')

    sheet_names = ['publications', 'geographic', 'scientific', 'datasets', 'processing',
                   'accuracy', 'outputs', 'archives']
    if subset is None:
        subset = sheet_names

    dataset = pd.read_excel(fn_data, sheet_name=None)

    # remove blanks from 'publications'
    blank_pubs = dataset['publications']['Human Key'] == ' ,  ()'
    dataset['publications'].drop(dataset['publications'][blank_pubs].index, inplace=True)
    dataset['publications'].rename(columns={'Key': 'PubKey'}, inplace=True)

    # extract the publication key for all sheets except the first and last ones
    # (publications and archives)
    # and remove all rows where this is nan
    for sheet in sheet_names[1:-1]:
        dataset[sheet]['PubKey'] = dataset[sheet]['Publication Key'].str.extract(r'\(([^()]{8})\)')
        dataset[sheet].dropna(subset=['PubKey'], inplace=True)

    # drop the helper columns from the publications table
    dataset['publications'].drop(['interesting?', '.not_relevant', 'geographic', 'scientific',
                                  'dataset', 'processing', 'outputs', 'accuracy'],
                                 axis=1, inplace=True)

    # drop the .relevant column from the geographic table
    dataset['geographic'].drop(['.not_relevant'], axis=1, inplace=True)
    dataset['geographic'].rename(columns={'Notes': 'Geographic Notes'}, inplace=True)

    # add study areas from bounding areas if not reported
    dataset['geographic'] = get_study_area_size(dataset['geographic'])

    # rename columns in the scientific table
    dataset['scientific'].rename(columns={'Notes': 'Scientific Notes', 'Description': 'Study Description'},
                                 inplace=True)

    # make the relevant column a boolean
    dataset['scientific']['Relevant'] = dataset['scientific']['Relevant'].map({'no': False, 'yes': True})

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
            if sheet == 'archives':
                continue
            dataset[sheet].drop(dataset[sheet].index[~dataset[sheet]['PubKey'].isin(relevant_keys)], inplace=True)

    return dict((sheet, dataset[sheet].reset_index(drop=True)) for sheet in subset)


def get_study_area_size(table):
    table.dropna(subset=['lat_min', 'lat_max', 'lon_min', 'lon_max'], how='any', inplace=True)

    areas = pd.Series(index=table.index,
                      data=[calculate_area(row) / 1e6 for _, row in table.iterrows()])

    table.loc[table['Area'].isna(), 'Area'] = areas.loc[table['Area'].isna()]

    return table


def _coords(row):
    return (tuple(row[['lon_min', 'lat_min']].values),
            tuple(row[['lon_max', 'lat_min']].values),
            tuple(row[['lon_max', 'lat_max']].values),
            tuple(row[['lon_min', 'lat_max']].values))


# based on sgillies answer on SO:
# https://stackoverflow.com/a/4683144
# calculates the area using an equal area projection centered on the polygon
def calculate_area(row):
    coords = _coords(row)

    lon, lat = zip(*coords)

    if max(lon) == min(lon) == max(lat) == min(lat) == 0:
        return np.nan

    else:
        pa = Proj("+proj=aea +lat_1={} +lat_2={} +lat_0={} + lon_0={}".format(row.lat_min,
                                                                              row.lat_max,
                                                                              np.mean([lat]),
                                                                              np.mean([lon])))
        x, y = pa(lon, lat)
        poly = {'type': 'Polygon', 'coordinates': [zip(x, y)]}

        return shape(poly).area


def expand_study_areas(geo, data):

    has_dataset = geo.dropna(subset=['DatasetKey'])
    no_dataset = geo.drop(has_dataset.index)

    many_one = no_dataset.loc[no_dataset.duplicated(subset='PubKey', keep=False)].copy()
    one_many = no_dataset.drop(many_one.index)

    many_keys = many_one.merge(data, left_on='PubKey', right_on='PubKey')['Key']
    many_one.loc[:, 'DatasetKey'] = many_keys.values

    one_merge = one_many.merge(data[['PubKey', 'Key']], left_on='PubKey', right_on='PubKey')
    one_merge['DatasetKey'] = one_merge['Key']

    one_many = one_merge[geo.columns].copy()

    return pd.concat([has_dataset, many_one, one_many], ignore_index=True)


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


def plot_stacked_histogram(df, _ax, _bins, cat_name, count_name, color_map, width_value=1, alpha_value=0.8):
    # Initialize a list to hold the bottom values for stacking
    bottom = np.zeros(len(_bins) - 1)

    # Loop through each category and stack the bars
    for category in df[cat_name].sort_values().unique():
        subset = df[df[cat_name] == category]
        counts, _ = np.histogram(subset[count_name], bins=_bins)
        _ax.bar(_bins[:-1], counts, width=width_value, bottom=bottom,
                label=category,
                color=color_map[category],
                edgecolor='black', alpha=alpha_value)
        bottom += counts  # Update bottom to stack the next bar on top

    return _ax
