import geopandas as gpd
import numpy as np
import folium
from folium.features import GeoJsonTooltip, GeoJsonPopup
from folium.plugins import HeatMap, GroupedLayerControl
import branca.colormap as cmp
from scripts import tools


def grouped_categories(df: gpd.GeoDataFrame, name: str,
                       color_dict: dict, pop_args: dict,
                       show: bool = True) -> tuple[folium.FeatureGroup, list]:
    """
    Create a FeatureGroup using different categories from a geodataframe.

    :param df: The geodataframe to use
    :param name: the name of the column to group on
    :param color_dict: a dict that maps from a category value to a color
    :param pop_args: arguments for creating popups
    :param show: show the group by default
    :return: the FeatureGroup, and a list of the individual layers to add to GroupedLayerControl
    """

    # initialize the layer and the list of groups
    fg = folium.FeatureGroup(name=name, show=show)
    grps = []

    # iterate over the grouped dataframe, creating a geojson object for each group
    for (ind, gp_df) in df.groupby(name):
        gjson = folium.GeoJson(
            gp_df.sort_values('poly_area', ascending=False),
            style_function=lambda feature: {
                'fillColor': color_dict[feature['properties'][name]],
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6
            },
            zoom_on_click=True,
            show=True,
            name=ind,
            highlight_function=lambda x: {'fillColor': '#ffffff'},
            popup=GeoJsonPopup(**pop_args),
            popup_keep_highlighted=True
        )

        fg.add_child(gjson)
        grps.append(gjson)

    return fg, grps


# load the data
pubs, sci, datasets = tools.load_dataset(subset=['publications', 'scientific', 'datasets'], relevant=False).values()
study_areas = gpd.read_file('data/Historic_Air_Photos.db')

# drop terrestrial datasets
datasets.drop(datasets.loc[datasets['Type'] == 'Terrestrial'].index, inplace=True)

# first, merge the dataframes so each polygon has attributes
merged = study_areas.drop(columns=['PubKey']).merge(datasets, left_on='DatasetKey', right_on='Key').drop(columns=['Publication Key'])
merged = merged.merge(pubs, on='PubKey').merge(sci, on='PubKey').drop(columns=['Reviewed By', 'Data Type',
                                                                               'Geom', 'Human Key', 'Publication Key',
                                                                               'Notes of technical interest', 'Study Description',
                                                                               'Scientific Notes', 'Notes'])
# rename type as data type for the map
merged = merged.rename(columns={'Type': 'Data Type'})

# drop duplicates from each study
merged = merged.drop_duplicates(subset=['geometry', 'PubKey', 'Data Type'])

# only use 'relevant' studies
merged = merged.loc[merged['Relevant']]

# re-format the Year, Area, and DOI for the popups
merged['Year'] = merged['Year'].apply(lambda x: f'{x}')
merged['Area'] = merged['Area'].apply(lambda x: f'{x:.2f} km<sup>2</sup>')
merged['DOI'] = merged['DOI'].apply(lambda x: f'<a target="_blank" href="https://doi.org/{x}">{x}</a>')

# sort the geometries by polygon size so that the smaller layers get added last
merged['poly_area'] = merged.to_crs(8857).geometry.area

# create popups
popup_args = {
    'fields': ['Author', 'Title', 'Publication Title', 'Year',
               'Data Type', 'Category', 'Region', 'Area', 'GeoKey', 'DOI'],
    'localize': True,
    'sticky': False,
    'smooth_factor': 0,
    'labels': True,
    'style': """
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
        font-size: 12px;
    """,
    'max_width': 500
}

# use the same colors for categories we used in fig. 10
category_colors = {'Glaciology': '#77AADD',
                   'Geomorphology': '#fe9929',
                   'Volcanology': '#ef6548',
                   'Forestry': '#41ae76',
                   'Ecology': '#99d8c9', # AAAA00
                   'Archeology': '#fed976',
                   'Landuse/Landcover': '#c994c7',  #c05780
                   'Urban Change': '#FFAABB',
                   'Methodology': '#969696'}

# use the same colors from the paper
type_colors = {'Aerial': tools.aerial_color,
               'Satellite': tools.satellite_color}

# create the heatmap layer
centroids = merged.to_crs(3857).centroid.to_crs(4326)
data = list(zip(centroids.y, centroids.x))

# create a plasma-like colormap
vals = np.arange(0, 1.1, 0.1)
hexs = [cmp.linear.magma.rgb_hex_str(vv) for vv in vals]
gradient = dict(zip(vals, hexs))

heatmap = HeatMap(data, gradient=gradient, name='Density', show=True)

# create the map, and add cartodb positron and openstreetmap as options
mymap = folium.Map(location=[0, 0], zoom_start=2, tiles=None, world_copy_jump=True)

folium.TileLayer('cartodbpositron', name='CartoDB Positron').add_to(mymap)
folium.TileLayer('openstreetmap', name='OpenStreetMap').add_to(mymap)

folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='ESRI',
    name='Esri World Imagery'
).add_to(mymap)

# create the two grouped categories, using Category and Data Type. Show Category by default
fg_cat, cat_grps = grouped_categories(merged, 'Category', category_colors, popup_args)
fg_typ, typ_grps = grouped_categories(merged, 'Data Type', type_colors, popup_args, show=False)

# add the featuregroups to the map
fg_cat.add_to(mymap)
fg_typ.add_to(mymap)

# add the heatmap to the map
heatmap.add_to(mymap)

# add layer control to switch layers
folium.LayerControl(collapsed=False).add_to(mymap)

# add grouped layer control to turn different values on/off
GroupedLayerControl(groups={'Category': cat_grps, 'Data Type': typ_grps},
                    collapsed=False,
                    exclusive_groups=False).add_to(mymap)

# save the map
mymap.save('data/interactive_map.html')
