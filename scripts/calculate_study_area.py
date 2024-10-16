import os
import numpy as np
import pandas as pd
from pyproj import Proj
from shapely.geometry import shape


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


# load the "clean" version of the database
df_dict = pd.read_excel('data/Review_Historic_Air_Photos.xlsx', sheet_name=None)

# remove blanks from 'publications'
blank_pubs = df_dict['publications']['Human Key'] == ' ,  ()'
df_dict['publications'].drop(df_dict['publications'][blank_pubs].index, inplace=True)

# add the publication key to the dictionary
df_dict['geographic']['Pub Key'] = df_dict['geographic']['Publication Key'].str.extract(r'\(([^()]{8})\)')

# get the geographic table from the dictionary
df_geo = df_dict['geographic']
df_geo.dropna(subset=['lat_min'], inplace=True)

# calculate the area for each polygon in the table
df_geo['area'] = [calculate_area(row) for ii, row in df_geo.iterrows()]
df_geo['area'] /= 1e6 # get the area in square km

# set any polygons with 0 area to nan
df_geo.loc[df_geo['area'] == 0, 'area'] = np.nan

# get the total area for each study
summed_area = df_geo.groupby(['Pub Key'])['area'].sum()
summed_area[summed_area == 0] = np.nan

# write the results to a csv
summed_area.to_csv('data/StudyAreaSize.csv')
