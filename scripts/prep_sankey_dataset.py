import pandas as pd
from pathlib import Path
import numpy as np
import tools


# ....................
# prepare the dataset
publications, scientific, outputs = tools.load_dataset(subset=['publications', 'scientific', 'outputs']).values()

# --- select the columns
publications.drop(columns=[c for c in publications.columns if c not in ['Year', 'PubKey']], inplace=True)
scientific = scientific[['PubKey', 'Data Type', 'Category', 'Relevant']].copy()
outputs.drop(columns=[c for c in outputs.columns if c not in ['PubKey', 'Output']], inplace=True)

# --- List of Unique filed in the column "Category"
unique_category = scientific['Category'].unique()

# just in case we haven't dropped all terrestrial values
terr_keys = scientific.loc[scientific['Data Type'] == 'Terrestrial', 'PubKey'].to_list()

# Filter the rows where 'Key' is in the 'terrestrial_keys' list
scientific = scientific.loc[~scientific['PubKey'].isin(terr_keys)].set_index('PubKey')
publications = publications.loc[~publications['PubKey'].isin(terr_keys)].set_index('PubKey')
outputs = outputs.loc[~outputs['PubKey'].isin(terr_keys)].set_index('PubKey')

#  --- Merge the dataframes on the "Key" column
merged = scientific.join(publications).join(outputs)

# drop repeated indices
merged = merged[~merged.sort_values(by='Output',
                                    ascending=False).index.duplicated(keep='first')].drop(columns=['Relevant'])

# .....................................................................
# Prepare the data for the online sankey https://sankeymatic.com/build/
merged.rename(columns={'Year': 'year', 'Data Type': 'data_type', 'Category': 'application', 'Output': 'output'},
              inplace=True)
merged.sort_values(by=['year'], ascending=True, inplace=True)

# Shortening the name
merged['application'].replace({'Landuse/Landcover': 'Landuse/cover'}, inplace=True)
merged['output'].replace({'3D (point cloud/DEM)': '3D',
                          '2D (orthophoto)': '2D-ortho',
                          '2D (georeferenced)': '2D-georef'},
                         inplace=True)

# --- Count the data_type per each year
counts_year_data = merged.groupby(['year', 'data_type']).size().reset_index(name='count')

# reorder the columns
year_count_type = counts_year_data.reindex(columns=['year', 'count', 'data_type'])
# add a [] in the text
year_count_type['count'] = year_count_type['count'].apply(lambda x: f"[{str(x)}]")

# export dataframe as csv and delimiter space
fn_year_count = Path('data', 'sankey_year_dataType.csv')
year_count_type.to_csv(fn_year_count, sep=" ", encoding='utf-8', index=False)

# --- Count the data_type per application
counts_data_field = merged.groupby(['data_type', 'application']).size().reset_index(name='count')
# reorder the columns
data_count_field = counts_data_field.reindex(columns=['data_type', 'count', 'application'])
data_count_field = data_count_field.sort_values(by=['count'], ascending=False)  # sort df by count

# add a [] in the text
data_count_field['count'] = data_count_field['count'].apply(lambda x: f"[{str(x)}]")

# export dataframe as csv and delimiter space
fn_data_count = Path('data', "sankey_dataType_application.csv")
data_count_field.to_csv(fn_data_count, sep=" ", encoding='utf-8', index=False)

# --- Count the application per output
merged.fillna('not reported', inplace=True)     # Convert the NaN in string as "not reported"
counts_field_out = merged.groupby(['application', 'output']).size().reset_index(name='count')
# reorder the columns
field_count_out = counts_field_out.reindex(columns=['application', 'count', 'output'])
field_count_out = field_count_out.sort_values(by=['count'], ascending=False)  # sort df by count

# add a [] in the text
field_count_out['count'] = field_count_out['count'].apply(lambda x: f"[{str(x)}]")

# export dataframe as csv and delimiter space
fn_field_count = Path('data', "sankey_application_output.csv")
field_count_out.to_csv(fn_field_count, sep=" ", encoding='utf-8', index=False)

# --- Concatenate the values into a single dataframe
result_sankey = np.concatenate([year_count_type, data_count_field, field_count_out], axis=0)
result_sankey_df = pd.DataFrame(result_sankey)

# save the combined dataframe to a CSV file
fn_out = Path('data', 'sankey_allResults.csv')
result_sankey_df.to_csv(fn_out, sep=" ", encoding='utf-8', index=False, header=False)

# --- prepare the color for the data_type & for applications. Copy this manually in the online tool
# Create a dataframe containing the application and colours
colours = {'Archeology': '#fed976',     #f7c003
           'Ecology': '#99d8c9',        # 99ff99; #b3c100
           'Forestry': '#41ae76',       #6ab187
           'Geomorphology': '#fe9929',  # ffcc99, #ea6a47
           'Glaciology': '#1d91c0',
           'Hydrology': '#a6bddb',      # a5d8dd
           'Landuse/cover': '#c994c7',  #c05780
           'Methodology': '#969696',    #488a99
           'Volcanology': '#ef6548'}    #ce1256

df_color = pd.DataFrame.from_dict(colours, orient='index', columns=['color'])
df_color.index.name = 'application'
df_color.reset_index(inplace=True)

# add a : before the application string e.g. : Archeology
df_color['application'] = df_color['application'].apply(lambda x: f": {str(x)}")
# export dataframe as csv and delimiter space
fn_color = Path('data', 'sankey_color_applications.csv')
df_color.to_csv(fn_color, sep=" ", encoding='utf-8', index=False)
