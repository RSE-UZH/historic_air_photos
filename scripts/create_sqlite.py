import pandas as pd
import numpy as np
import sqlite3
from shapely.geometry import Polygon
import tools


def _coords(row):
    return (tuple(row[['lon_min', 'lat_min']].values),
            tuple(row[['lon_max', 'lat_min']].values),
            tuple(row[['lon_max', 'lat_max']].values),
            tuple(row[['lon_min', 'lat_max']].values))


# read the sheets from the excel spreadsheet as individual dataframes
pubs, geog, sci, data, proc, acc, outs, archs = tools.load_dataset(relevant=False).values()

# create the database
db_conn = sqlite3.connect('data/Historic_Air_Photos.db')
db_conn.enable_load_extension(True)  # make it so we can add extensions
db_conn.load_extension('mod_spatialite')  # add the spatialite extension

# create publications table
db_conn.execute(
    """
    CREATE TABLE publications (
        PubKey TEXT NOT NULL,
        Author TEXT NOT NULL,
        Year INTEGER NOT NULL,
        Title TEXT NOT NULL,
        PubTitle TEXT,
        DOI TEXT,
        Relevant INTEGER,
        PRIMARY KEY(PubKey)
        );
    """
)

# create geographic table
db_conn.execute(
    """
    CREATE TABLE geographic (
        GeoKey TEXT NOT NULL,
        DatasetKey TEXT NOT NULL,
        PubKey TEXT NOT NULL,
        Geom BLOB,
        Area REAL,
        Region TEXT,
        Notes TEXT,
        PRIMARY KEY(GeoKey),
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey),
        FOREIGN KEY(DatasetKey) REFERENCES datasets(DatasetKey)
        );
    """
)

# add geometry to the geographic table, including a spatialite index and a CRS (EPSG:4326)
db_conn.execute('SELECT InitSpatialMetaData(1);')
db_conn.execute("SELECT AddGeometryColumn('geographic', 'Geometry', 4326, 'MULTIPOLYGON', 'XY');")
db_conn.execute("SELECT CreateSpatialIndex('geographic', 'Geometry');")

# create scientific table
db_conn.execute(
    """
    CREATE TABLE scientific (
        PubKey TEXT NOT NULL,
        DataType TEXT NOT NULL,
        StudyType TEXT NOT NULL,
        Category TEXT NOT NULL,
        Description TEXT,
        Notes TEXT,
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey)
        );
    """
)

# create datasets table
db_conn.execute(
    """
    CREATE TABLE datasets (
        DatasetKey TEXT NOT NULL,
        PubKey TEXT NOT NULL,
        Type TEXT NOT NULL,
        ArchiveKey TEXT NOT NULL,
        Free TEXT,
        StartYear INTEGER,
        EndYear INTEGER,
        Calibration TEXT,
        FlightHeight INTEGER,
        HeightRef TEXT,
        GSD REAL,
        Scale TEXT,
        ScanRes REAL,
        ScanUnit TEXT,
        NumImgs INTEGER,
        CameraType TEXT,
        Notes TEXT,
        PRIMARY KEY(DatasetKey),
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey)
        );
    """
)

# create processing table
db_conn.execute(
    """
    CREATE TABLE processing (
        DatasetKey TEXT NOT NULL,
        PubKey TEXT NOT NULL,
        Method TEXT NOT NULL,
        Software TEXT,
        Version TEXT,
        GCPs TEXT,
        Fiducial TEXT,
        PreProc TEXT,
        PreProcNote TEXT,
        Geometric TEXT,
        Radiometric TEXT,
        Workflow TEXT,
        PRIMARY KEY(DatasetKey),
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey),
        FOREIGN KEY(DatasetKey) REFERENCES datasets(PubKey)
        );
    """
)

# create accuracy table
db_conn.execute(
    """
    CREATE TABLE accuracy (
        AccuracyKey TEXT NOT NULL,
        DatasetKey TEXT NOT NULL,
        PubKey TEXT NOT NULL,
        SourceXY TEXT,
        SourceZ TEXT,
        SourceGroup TEXT,
        SourceAccuracyX REAL,
        SourceAccuracyY REAL,
        SourceAccuracyZ REAL,
        SourceAccuracyXY REAL,
        SourceAccuracyXYZ REAL,
        SourceAccuracy REAL,
        NumGCPs INTEGER,
        GCPResidualsX REAL,
        GCPResidualsY REAL,
        GCPResidualsZ REAL,
        GCPResidualsXY REAL,
        GCPResidualsXYZ REAL,
        GCPResiduals REAL,
        NumCPs INTEGER,
        CPResidualsX REAL,
        CPResidualsY REAL,
        CPResidualsZ REAL,
        CPResidualsXY REAL,
        CPResidualsXYZ REAL,
        CPResiduals REAL,
        Comparison TEXT,
        CompGroup TEXT,
        CompAccuracyX REAL,
        CompAccuracyY REAL,
        CompAccuracyZ REAL,
        CompAccuracyXY REAL,
        CompAccuracyXYZ REAL,
        CompAccuracy REAL,
        CompResidualsX REAL,
        CompResidualsY REAL,
        CompResidualsZ REAL,
        CompResidualsXY REAL,
        CompResidualsXYZ REAL,
        CompResiduals REAL,
        Metric TEXT,
        PostProcessing TEXT,
        Notes TEXT,
        PRIMARY KEY(AccuracyKey),
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey),
        FOREIGN KEY(DatasetKey) REFERENCES publications(DatasetKey)
        );
    """
)

# create outputs table
db_conn.execute(
    """
    CREATE TABLE outputs (
        DatasetKey TEXT NOT NULL,
        PubKey TEXT NOT NULL,
        Output TEXT,
        OrthoRes REAL,
        DEMRes REAL,
        Notes TEXT,
        PRIMARY KEY(DatasetKey),
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey),
        FOREIGN KEY(DatasetKey) REFERENCES publications(DatasetKey)
        );
    """
)

# create archives table
db_conn.execute(
    """
    CREATE TABLE archives (
        ArchiveKey TEXT NOT NULL,
        Country TEXT,
        LongName TEXT,
        ShortName TEXT,
        NumImages INTEGER,
        StartYear INTEGER,
        EndYear INTEGER,
        URL TEXT,
        GeoURL TEXT,
        Notes TEXT,
        PRIMARY KEY(ArchiveKey)
        );
    """
)

# now, we populate the tables using the sheets we opened, using pd.DataFrame.to_sql()
# we also re-name columns along the way

# populate the publications table
pubs = pubs.merge(sci[['PubKey', 'Relevant']], left_on='PubKey', right_on='PubKey')
pubs.rename(columns={'Publication Title': 'PubTitle'},
            inplace=True)
pubs_cols = ['PubKey', 'Author', 'Year', 'Title', 'PubTitle', 'DOI', 'Relevant']
pubs[pubs_cols].to_sql('publications', db_conn, if_exists='append', index=False)

# populate the geographic table
geog = tools.expand_study_areas(geog, data)

counts = dict(zip(list(geog['PubKey'].unique()),
                  np.zeros(len(geog['PubKey'].unique()))))

for ind, row in geog.sort_values('DatasetKey').iterrows():
    geog.loc[ind, 'GeoKey'] = row['PubKey'] + '.G' + str(int(counts[row['PubKey']] + 1))
    counts[row['PubKey']] += 1

geog.dropna(subset=['lat_min', 'lat_max', 'lon_min', 'lon_max'], inplace=True)
geog.rename(columns={'Geographic Notes': 'Notes'}, inplace=True)

geog['Geom'] = [Polygon(_coords(row)).wkb for _, row in geog.iterrows()]

geo_cols = ['GeoKey', 'DatasetKey', 'PubKey', 'Geom', 'Area', 'Region', 'Notes']
geog[geo_cols].to_sql('geographic', db_conn, if_exists='append', index=False)

db_conn.execute("UPDATE geographic SET Geometry = CastToMultiPolygon(ST_GeomFromWKB(Geom, 4326));")

# populate the scientific table
sci.rename(columns={'Data Type': 'DataType', 'Type of Study': 'StudyType',
                    'Study Description': 'Description', 'Scientific Notes': 'Notes'}, inplace=True)

sci_cols = ['PubKey', 'DataType', 'StudyType', 'Category', 'Description', 'Notes']
sci[sci_cols].to_sql('scientific', db_conn, if_exists='append', index=False)

# populate the dataset table
data[['PubID', 'Num']] = outs['Key'].str.split('.', expand=True)
data.rename(columns={'Key': 'DatasetKey', 'Freely Available?': 'Free',
                     'Acquisition Start Year': 'StartYear',
                     'Acquisition End Year': 'EndYear', 'Camera Calibration': 'Calibration',
                     'Flight Height [m]': 'FlightHeight', 'Height reference': 'HeightRef',
                     'GSD [m]': 'GSD', 'Scanner resolution': 'ScanRes', 'Scanner resolution units': 'ScanUnit',
                     'No. Images': 'NumImgs', 'Camera type': 'CameraType',
                     'Dataset Notes': 'Notes'}, inplace=True)

data_cols = ['DatasetKey', 'PubKey', 'Type', 'ArchiveKey', 'Free', 'StartYear', 'EndYear',
             'Calibration', 'FlightHeight', 'HeightRef', 'GSD', 'Scale', 'ScanRes', 'ScanUnit',
             'NumImgs', 'CameraType', 'Notes']
data[data_cols].to_sql('datasets', db_conn, if_exists='append', index=False)

# populate the processing table
proc.rename(columns={'Key': 'DatasetKey', 'Fiducial Marks': 'Fiducial', 'Pre-processing': 'PreProc',
                     'Simplified Pre-processing Note': 'PreProcNote',
                     'Geometric Pre-processing': 'Geometric',
                     'Radiometric Pre-processing': 'Radiometric',
                     'Workflow Note': 'Workflow',
                     'Related paper': 'Related'}, inplace=True)

proc_cols = ['DatasetKey', 'PubKey', 'Method', 'Software', 'Version', 'GCPs', 'Fiducial',
             'PreProc', 'PreProcNote', 'Geometric', 'Radiometric', 'Workflow']
proc[proc_cols].to_sql('processing', db_conn, if_exists='append', index=False)

# populate the accuracy table
# first, calculate the "avg" for the different metrics
acc = tools.accuracy_measures(acc)
acc.rename(columns={'Accuracy Key': 'AccuracyKey',
                    'Ground control source XY': 'SourceXY',
                    'Ground control source Z': 'SourceZ',
                    'Ground control source group': 'SourceGroup',
                    'Ground control accuracy [m] X': 'SourceAccuracyX',
                    'Ground control accuracy [m] Y': 'SourceAccuracyY',
                    'Ground control accuracy [m] Z': 'SourceAccuracyZ',
                    'Ground control accuracy [m] XY': 'SourceAccuracyXY',
                    'Ground control accuracy [m] XYZ': 'SourceAccuracyXYZ',
                    'Ground control accuracy [m] avg': 'SourceAccuracy',
                    'No. GCPs': 'NumGCPs',
                    'Residuals to GCPs [m] X': 'GCPResidualsX',
                    'Residuals to GCPs [m] Y': 'GCPResidualsY',
                    'Residuals to GCPs [m] Z': 'GCPResidualsZ',
                    'Residuals to GCPs [m] XY': 'GCPResidualsXY',
                    'Residuals to GCPs [m] XYZ': 'GCPResidualsXYZ',
                    'Residuals to GCPs [m] avg': 'GCPResiduals',
                    'No. CPs': 'NumCPs',
                    'Residuals to CPs [m] X': 'CPResidualsX',
                    'Residuals to CPs [m] Y': 'CPResidualsY',
                    'Residuals to CPs [m] Z': 'CPResidualsZ',
                    'Residuals to CPs [m] XY': 'CPResidualsXY',
                    'Residuals to CPs [m] XYZ': 'CPResidualsXYZ',
                    'Residuals to CPs [m] avg': 'CPResiduals',
                    'Comparison data': 'Comparison',
                    'Comparison source group': 'CompGroup',
                    'Accuracy comparison data [m] X': 'CompAccuracyX',
                    'Accuracy comparison data [m] Y': 'CompAccuracyY',
                    'Accuracy comparison data [m] Z': 'CompAccuracyZ',
                    'Accuracy comparison data [m] XY': 'CompAccuracyXY',
                    'Accuracy comparison data [m] XYZ': 'CompAccuracyXYZ',
                    'Accuracy comparison data [m] avg': 'CompAccuracy',
                    'Residuals to comparison [m] X': 'CompResidualsX',
                    'Residuals to comparison [m] Y': 'CompResidualsY',
                    'Residuals to comparison [m] Z': 'CompResidualsZ',
                    'Residuals to comparison [m] XY': 'CompResidualsXY',
                    'Residuals to comparison [m] XYZ': 'CompResidualsXYZ',
                    'Residuals to comparison [m] avg': 'CompResiduals',
                    'Comparison Metric': 'Metric',
                    'Post-Processing': 'PostProcessing'}, inplace=True)

acc_cols = ['AccuracyKey', 'DatasetKey', 'PubKey', 'SourceXY', 'SourceZ', 'SourceGroup',
            'SourceAccuracyX', 'SourceAccuracyY', 'SourceAccuracyZ', 'SourceAccuracyXY', 'SourceAccuracyXYZ',
            'SourceAccuracy', 'NumGCPs', 'GCPResidualsX', 'GCPResidualsY', 'GCPResidualsZ', 'GCPResidualsXY',
            'GCPResidualsXYZ', 'GCPResiduals', 'NumCPs', 'CPResidualsX', 'CPResidualsY', 'CPResidualsZ',
            'CPResidualsXY', 'CPResidualsXYZ', 'CPResiduals', 'Comparison', 'CompGroup', 'CompAccuracyX',
            'CompAccuracyY', 'CompAccuracyZ', 'CompAccuracyXY', 'CompAccuracyXYZ', 'CompAccuracy',
            'CompResidualsX', 'CompResidualsY', 'CompResidualsZ', 'CompResidualsXY', 'CompResidualsXYZ',
            'CompResiduals', 'Metric', 'PostProcessing']
acc[acc_cols].to_sql('accuracy', db_conn, if_exists='append', index=False)

# populate the outputs table
outs[['PubID', 'Num']] = outs['Key'].str.split('.', expand=True)
outs.rename(mapper={'Key': 'DatasetKey', 'DEM resolution [m]': 'DEMRes',
                    'Orthophoto resolution [m]': 'OrthoRes', 'Output Notes': 'Notes'}, axis='columns', inplace=True)

outs_cols = ['DatasetKey', 'PubKey', 'Output', 'OrthoRes', 'DEMRes', 'Notes']
outs[outs_cols].to_sql('outputs', db_conn, if_exists='append', index=False)

# populate the archives table
archs.to_sql('archives', db_conn, if_exists='append', index=False)

# close the connection to the database
db_conn.close()
