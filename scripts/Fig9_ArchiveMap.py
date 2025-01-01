from pathlib import Path
import geopandas as gpd
from shapely.geometry.polygon import Polygon
import cartopy.crs as ccrs
import cartopy.feature as cf
from cartopy import mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.path as mpath
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import tools


# https://stackoverflow.com/a/25628397
def get_cmap(n, name='hsv'):
    """
    Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name.
    """
    return plt.cm.get_cmap(name, n)


# https://stackoverflow.com/a/43505887
def curved_extent(lon_min, lon_max, lat_min, lat_max):
    vertices = [(lon, lat_min) for lon in range(lon_min, lon_max, 1)] + \
               [(lon, lat_max) for lon in range(lon_max, lon_min, -1)]
    return mpath.Path(vertices)


# read the geographic and datasets sheets from the excel file
geographic, datasets, archives = tools.load_dataset(subset=['geographic', 'datasets', 'archives']).values()
geographic = tools.expand_study_areas(geographic, datasets)

# add geometry to the geographic table
geographic['geometry'] = [tools._coords(row) for ii, row in geographic.iterrows()]
geographic['geometry'] = geographic['geometry'].apply(Polygon)

# select necessary columns
geographic = geographic[['DatasetKey', 'geometry']].copy()
datasets = datasets[['Key', 'PubKey', 'Type', 'ArchiveKey']].copy()
archives = archives[['ArchiveKey', 'Country']].copy()

# merge the tables
merged = geographic.merge(datasets.merge(archives, left_on='ArchiveKey', right_on='ArchiveKey'),
                          left_on='DatasetKey', right_on='Key').drop(columns=['Key'])

# count top 10 countries by archive location, ignoring duplicated datasets
top_ten = merged.drop_duplicates(subset='DatasetKey')['Country'].value_counts().head(n=10).index.to_list()

# map other locations to "Other/Not Specified"
merged['Country'] = merged['Country'].fillna('Other/Not Specified')

for location in merged['Country'].unique():
    if location not in top_ten:
        merged['Country'] = merged['Country'].replace({location: 'Other/Not Specified'})

top_ten.append('Other/Not Specified')

study_areas = gpd.GeoDataFrame(merged[['DatasetKey', 'Type', 'Country', 'geometry']])
study_areas.set_crs(epsg=4326, inplace=True)

# reproject to the robinson projection
study_areas['x'] = study_areas.to_crs("esri:54030")['geometry'].centroid.x
study_areas['y'] = study_areas.to_crs("esri:54030")['geometry'].centroid.y

# create a Robinson projection object
robinson = ccrs.Robinson()

# set the marker size for both figures
msize = 4

# get a dict of colors to pair with archive names
# order is: USA, UK, France, Italy, Switzerland, Poland, Canada, Austria, Spain, Finland, Other
colors = ['#b5285f','#ad94f4','#f4970e','#09be93','#176be5',
          '#7b40ec','#f1e000','#db4839','#7ecd14','#f09ab6','#91bccc']
color_dict = dict(zip(top_ten, colors))

fig = plt.figure(figsize=(20, 10))

ax = plt.axes(projection=robinson)
ax.add_feature(cf.BORDERS, linewidth=0.2)
ax.coastlines(resolution='50m', linewidth=0.2)
ax.set_ylim(robinson.y_limits)
ax.set_xlim(robinson.x_limits)

# add an inset for Europe
europe = inset_axes(ax, width="100%", height="100%",
                    bbox_to_anchor=(-0.05, -0.1, 0.26, 0.6),
                    bbox_transform=ax.transAxes,
                    axes_class=mpl.geoaxes.GeoAxes,
                    # axes_kwargs=dict(map_projection=ccrs.AlbersEqualArea(central_longitude=5, central_latitude=58)))
                    axes_kwargs=dict(projection=robinson))

europe.add_feature(cf.BORDERS, linewidth=0.2)
europe.coastlines(resolution='50m', linewidth=0.2)
europe.set_extent([-20, 29, 35, 71])

# boundary = curved_extent(-26, 36, 34, 82)
# boundary.set_boundary(boundary, transform=ccrs.PlateCarree())
xmin, xmax, ymin, ymax = europe.get_extent()

ax.plot([xmin, xmax, xmax, xmin, xmin], [ymin, ymin, ymax, ymax, ymin], 'k', lw=0.5, transform=robinson)
ax.text(xmin + 100000, ymin + 150000, 'a)', fontsize=18)

europe.text(0.02, 0.04, 'a)', fontsize=18, transform=europe.transAxes)

# add an inset for HMA
hma = inset_axes(ax, width="100%", height="100%",
                 bbox_to_anchor=(0.9, 0.55, 0.22, 0.6),
                 bbox_transform=ax.transAxes,
                 axes_class=mpl.geoaxes.GeoAxes,
                 # axes_kwargs=dict(map_projection=ccrs.AlbersEqualArea(central_longitude=82, central_latitude=35)))
                 axes_kwargs=dict(projection=robinson))

hma.add_feature(cf.BORDERS, linewidth=0.2)
hma.coastlines(resolution='50m', linewidth=0.2)
hma.set_extent([70, 94, 26, 44])

# boundary = curved_extent(70, 94, 26, 44)
# hma.set_boundary(boundary, transform=ccrs.PlateCarree())

xmin, xmax, ymin, ymax = hma.get_extent()

ax.plot([xmin, xmax, xmax, xmin, xmin], [ymin, ymin, ymax, ymax, ymin], 'k', lw=0.5, transform=robinson)
ax.text(xmin + 100000, ymin + 150000, 'b)', fontsize=18)

hma.text(0.02, 0.04, 'b)', fontsize=18, transform=hma.transAxes)

alpha = 0.8  # set the transparency for the markers

handles = list()
handles.append(mlines.Line2D([], [], color='black', marker='s', linestyle='None',
                             fillstyle='none', markersize=msize))
handles.append(mlines.Line2D([], [], color='black', marker='o', linestyle='None',
                             fillstyle='none', markersize=msize))
# handles.append(mlines.Line2D([], [], color='black', marker='^', linestyle='None', fillstyle='none', markersize=12))

for ind, arch_loc in enumerate(top_ten):
    this_sat = (study_areas['Type'] == 'Satellite') & (study_areas['Country'] == arch_loc)
    this_aer = (study_areas['Type'] == 'Aerial') & (study_areas['Country'] == arch_loc)
    # this_ter = (study_areas['Type'] == 'Terrestrial') & (study_areas['Archive Location'] == arch_loc)

    ax.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
            color=color_dict[arch_loc], alpha=alpha, ms=msize)
    ax.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
            color=color_dict[arch_loc], alpha=alpha, ms=msize)
    # ax.plot(study_areas.loc[this_ter, 'x'], study_areas.loc[this_ter, 'y'], '^', color=colors(ii), alpha=alpha, ms=12)

    europe.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
                color=color_dict[arch_loc], alpha=alpha, ms=msize) #, transform=robinson)
    europe.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
                color=color_dict[arch_loc], alpha=alpha, ms=msize) #, transform=robinson)

    hma.plot(study_areas.loc[this_sat, 'x'], study_areas.loc[this_sat, 'y'], 's',
             color=color_dict[arch_loc], alpha=alpha, ms=msize) #, transform=robinson)
    hma.plot(study_areas.loc[this_aer, 'x'], study_areas.loc[this_aer, 'y'], 'o',
             color=color_dict[arch_loc], alpha=alpha, ms=msize) #, transform=robinson)

    handles.append(mpatches.Rectangle((0, 0), 1, 1,
                                      facecolor=color_dict[arch_loc], edgecolor='k', alpha=alpha))

labels = ['Satellite', 'Aerial'] + top_ten

ax.legend(handles, labels, fontsize=16, loc=(-0.055, 0.45), frameon=True, framealpha=1)
fig.savefig(Path('figures', 'Fig9_ArchiveMap.png'), dpi=600, bbox_inches='tight')
