import pandas as pd
import geopandas as gpd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import cartopy.crs as ccrs
import cartopy.feature as cf
from cartopy import mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def _coords(row):
    return (tuple(row[['lon_min', 'lat_min']].values),
            tuple(row[['lon_max', 'lat_min']].values),
            tuple(row[['lon_max', 'lat_max']].values),
            tuple(row[['lon_min', 'lat_max']].values))


# https://stackoverflow.com/a/25628397
def get_cmap(n, name='hsv'):
    """
    Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.
    """
    return plt.cm.get_cmap(name, n)


plt.ion()

# read the geographic sheet from the excel file
df = pd.read_csv('data/Review_Historic_Air_Photos.csv')

# drop any rows with geometry missing
df.dropna(subset=['lat_min', 'lat_max', 'lon_min', 'lon_max'], inplace=True)

# add a geometry column
df['geometry'] = [_coords(row) for ii, row in df.iterrows()]

# get only unique geometry and data types
df.drop_duplicates(subset=['geometry', 'Type'], inplace=True)
df['geometry'] = df['geometry'].apply(Polygon)

# only take the papers that are counted as "relevant"
df = df[df['Relevant'] == 'yes']

study_areas = gpd.GeoDataFrame(df[['Key', 'Type', 'Archive Location', 'geometry']])
study_areas.set_crs(epsg=4326, inplace=True)

# reproject to the robinson projection
study_areas['x'] = study_areas.to_crs("esri:54030")['geometry'].centroid.x
study_areas['y'] = study_areas.to_crs("esri:54030")['geometry'].centroid.y

# create a Robinson projection object
robinson = ccrs.Robinson()

# set the marker size for both figures
msize = 6

# -------------------------------------------------------------------------------------------------------------------
# create a map that shows the study sites plotted using an individual marker
study_area_fig = plt.figure(figsize=(18, 10))
ax = plt.axes(projection=robinson)
ax.add_feature(cf.BORDERS, linewidth=0.2)
ax.coastlines(resolution='50m', linewidth=0.2)
ax.set_ylim(robinson.y_limits)
ax.set_xlim(robinson.x_limits)

sat = study_areas['Type'] == 'Satellite'
aer = study_areas['Type'] == 'Aerial'
# ter = study_areas['Type'] == 'Terrestrial'

ax.plot(study_areas.loc[sat, 'x'], study_areas.loc[sat, 'y'], 'bs',
        markerfacecolor='none', ms=msize, label='Satellite')
ax.plot(study_areas.loc[aer, 'x'], study_areas.loc[aer, 'y'], 'ro',
        markerfacecolor='none', ms=msize, label='Aerial')

# ax.plot(study_areas.loc[ter, 'x'], study_areas.loc[ter, 'y'], 'k^',
#         markerfacecolor='none', ms=12, label='Terrestrial')

# add a legend with the type of data
ax.legend(fontsize=14, frameon=False, loc='upper right')

full_ext = ax.get_extent()
study_area_fig.savefig('study_map.png', dpi=300, bbox_inches='tight')

# -------------------------------------------------------------------------------------------------------------------
# color each symbol according to the type of data and the archive location

archive_fig = plt.figure(figsize=(20, 10))
ax = plt.axes(projection=robinson)
ax.add_feature(cf.BORDERS, linewidth=0.2)
ax.coastlines(resolution='50m', linewidth=0.2)
ax.set_ylim(robinson.y_limits)
ax.set_xlim(robinson.x_limits)

inset = inset_axes(ax, width="100%", height="100%",
                   bbox_to_anchor=(-0.05, -0.1, 0.26, 0.6),
                   bbox_transform=ax.transAxes,
                   axes_class=mpl.geoaxes.GeoAxes,
                   axes_kwargs=dict(map_projection=robinson))
inset.add_feature(cf.BORDERS, linewidth=0.2)
inset.coastlines(resolution='50m', linewidth=0.2)

inset.set_ylim(3.84e6, 7.48e6)
inset.set_xlim(-1.78e6, 2.56e6)

# arch_locs = study_areas['Archive Location'].unique()
archive_count = study_areas.groupby(['Archive Location'])['geometry'].count()
arch_locs = list(archive_count.sort_values(ascending=False).head(8).index)

# get a colormap with unique colors for each archive location
colors = get_cmap(len(arch_locs) + 1, name='tab10')

alpha = 0.6  # set the transparency for the markers

handles = list()
handles.append(mlines.Line2D([], [], color='black', marker='s', linestyle='None',
                             fillstyle='none', markersize=msize))
handles.append(mlines.Line2D([], [], color='black', marker='o', linestyle='None',
                             fillstyle='none', markersize=msize))
# handles.append(mlines.Line2D([], [], color='black', marker='^', linestyle='None', fillstyle='none', markersize=12))

for ii, arch_loc in enumerate(arch_locs):
    this_sat = (study_areas['Type'] == 'Satellite') & (study_areas['Archive Location'] == arch_loc)
    this_aer = (study_areas['Type'] == 'Aerial') & (study_areas['Archive Location'] == arch_loc)
    # this_ter = (study_areas['Type'] == 'Terrestrial') & (study_areas['Archive Location'] == arch_loc)

    ax.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
            color=colors(ii), alpha=alpha, ms=msize)
    ax.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
            color=colors(ii), alpha=alpha, ms=msize)
    # ax.plot(study_areas.loc[this_ter, 'x'], study_areas.loc[this_ter, 'y'], '^', color=colors(ii), alpha=alpha, ms=12)

    inset.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
               color=colors(ii), alpha=alpha, ms=msize)
    inset.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
               color=colors(ii), alpha=alpha, ms=msize)

    handles.append(mpatches.Rectangle((0, 0), 1, 1, facecolor=colors(ii), edgecolor='k', alpha=alpha))

# now add the "other" category
this_sat = (study_areas['Type'] == 'Satellite') & (~study_areas['Archive Location'].isin(arch_locs))
this_aer = (study_areas['Type'] == 'Aerial') & (~study_areas['Archive Location'].isin(arch_locs))
# this_ter = (study_areas['Type'] == 'Terrestrial') & (~study_areas['Archive Location'].isin(arch_locs))

ax.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
        color=colors(ii+1), alpha=alpha, ms=msize)
ax.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
        color=colors(ii+1), alpha=alpha, ms=msize)
# ax.plot(study_areas.loc[this_ter, 'x'], study_areas.loc[this_ter, 'y'], '^', color=colors(ii+1), alpha=alpha, ms=12)

inset.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
           color=colors(ii+1), alpha=alpha, ms=msize)
inset.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
           color=colors(ii+1), alpha=alpha, ms=msize)

handles.append(mpatches.Rectangle((0, 0), 1, 1, facecolor=colors(ii+1), edgecolor='k', alpha=alpha))
labels = ['Satellite', 'Aerial'] + arch_locs
labels.append('other/not specified')

plt.show()


ax.legend(handles, labels, fontsize=12, loc=(-0.05, 0.42), frameon=True, framealpha=1)
plt.savefig('archive_locations.png', dpi=300, bbox_inches='tight')
