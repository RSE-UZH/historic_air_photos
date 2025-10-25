import numpy as np
import pandas as pd
from typing import Union
import tools


def print_reported_stats(df: pd.DataFrame, patt: Union[str, list], endswidth: bool=False) -> None:
    """
    Print the percentage of datasets and studies that reported different metrics or information.

    For example, to check the number of datasets/studies that reported only "Residual to GCPs [m] X"
    values (and not XY or XYZ):

        print_reported_stats(df, 'Residual to GCPs [m] X', endswidth=True)

    which prints the percentage of datasets (and studies) that have a value in the 'Residual to GCPs [m] X' column:

        Any Residuals to GCPs [m] X: 27.30
        Pct of studies: 27.27

    {patt} can also be a list - for example, to check whether datasets/studies have reported any Z comparison value:

        comps = ['Residuals to GCPs [m] Z', 'Residuals to CPs [m] Z', 'Residuals to comparison [m] Z']
        print_reported_stats(merged, comps)

        Any ['Residuals to GCPs [m] Z', 'Residuals to CPs [m] Z', 'Residuals to comparison [m] Z']: 68.72
        Pct of studies: 69.19
        Residuals to GCPs [m] Z: 32.92
        Residuals to CPs [m] Z: 16.87
        Residuals to comparison [m] Z: 62.83

    :param df: the dataframe to print values from
    :param patt: the pattern(s) in the column names to match
    :param endswidth: whether {patt} is at the end of the column name, {patt} is found anywhere in the name
    """
    if isinstance(patt, list):
        acc = df[patt]
    else:
        if not endswidth:
            acc = df[[c for c in merged.columns if patt in c]]
        else:
            acc = df[[c for c in merged.columns if c.endswith(patt)]]

    pct_any = 100 * np.count_nonzero((~acc.isna()).any(axis=1)) / len(acc)

    print(f"Any {patt}: {pct_any:.2f}")

    unique_studies = df.loc[(~acc.isna()).any(axis=1)].drop_duplicates(subset='Publication Key')
    pct_stud = 100 * len(unique_studies) / len(df.drop_duplicates(subset='Publication Key'))

    print(f"Pct of studies: {pct_stud:.2f}")

    if len(acc.columns) > 1:
        for col in acc.columns:
            pct = 100 * np.count_nonzero((~acc[col].isna())) / len(acc)
            print(f"{col}: {pct:.2f}")


datasets, accuracy = tools.load_dataset(subset=['datasets', 'accuracy']).values()

merged = accuracy.merge(datasets[['Key', 'Type', 'Scale']], left_on='DatasetKey', right_on='Key').drop(columns=['Key'])
merged.drop(merged.loc[merged['Type'] == 'Terrestrial'].index, inplace=True)

# these are the 5 categories we used for accuracy information
comparisons = ['Ground control accuracy', 'Residuals to GCPs', 'Residuals to CPs',
               'Accuracy comparison', 'Residuals to comparison']

# split into aerial, satellite
(_, aerial), (_, satellite) = merged.groupby('Type')

# get % of types of comparison metric
print('Percent of datasets using given comparison metrics:')
metrics = 100 * merged['Comparison Metric'].dropna().value_counts() / len(merged['Comparison Metric'].dropna())
print(metrics)

# count how many datasets/studies reported scale
print_reported_stats(merged, 'Scale')
print('\n')

# count how many datasets report both comparison Z accuracy and any Z accuracy for the products
report_both = merged.dropna(subset=['Accuracy comparison data [m] Z'])
report_both.dropna(subset=['Residuals to CPs [m] Z', 'Residuals to GCPs [m] Z', 'Residuals to comparison [m] Z'], how='any')

both_pct = 100 * len(report_both) / len(merged)

print(f"Reported both reference data quality and vertical accuracy: {both_pct:.2f}\n")

# next, check how many datasets/studies reported any Z information
print_reported_stats(merged, ['Residuals to GCPs [m] Z', 'Residuals to CPs [m] Z', 'Residuals to comparison [m] Z'])
print('\n')

# check how many datasets/studies reported any XY information
print_reported_stats(merged, ['Residuals to GCPs [m] X', 'Residuals to GCPs [m] Y', 'Residuals to GCPs [m] XY',
                              'Residuals to CPs [m] X', 'Residuals to CPs [m] Y', 'Residuals to CPs [m] XY',
                              'Residuals to comparison [m] X', 'Residuals to comparison [m] Y', 'Residuals to comparison [m] XY'])
print('\n')

# check how many datasets/studies reported any of the different accuracy information/metrics
for comp in comparisons:
    print_reported_stats(merged, comp)
    print('\n')

# now do the same for aerial and satellite:
print('Aerial Datasets')
for comp in comparisons:
    print_reported_stats(aerial, comp)
    print('\n')

print('Satellite Datasets')
for comp in comparisons:
    print_reported_stats(satellite, comp)
    print('\n')
