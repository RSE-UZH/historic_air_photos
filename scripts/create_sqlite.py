import pandas as pd
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
        GeoID TEXT NOT NULL,
        DatasetKey TEXT NOT NULL,
        PubKey TEXT NOT NULL,
        Geometry BLOB,
        Area REAL,
        Country TEXT,
        Notes TEXT,
        PRIMARY KEY(GeoID),
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
        PRIMARY KEY(DataKey),
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
        ComparisonGroup TEXT,
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
        FOREIGN KEY(DatasetKey) REFERENCES publications(DatasetKey),
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
        Note TEXT,
        PRIMARY KEY(DatasetKey),
        FOREIGN KEY(PubKey) REFERENCES publications(PubKey),
        FOREIGN KEY(DatasetKey) REFERENCES publications(DatasetKey),
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
        PRIMARY KEY(ArchiveKey),
        );
    """
)

# now, we populate the tables using the sheets we opened, using pd.DataFrame.to_sql()
# we also re-name columns along the way

# populate the publications table
pubs.rename(mapper={'Key': 'id', 'Publication Title': 'PubTitle', '.not_relevant': 'Relevant'},
            axis='columns', inplace=True)
pubs_cols = ['id', 'Author', 'Year', 'Title', 'PubTitle', 'DOI', 'Relevant']
pubs[pubs_cols].to_sql('publications', db_conn, if_exists='append', index=False)

# populate the geographic table
geog['GeoID'] = geog.index
geog['PubID'] = geog['Publication Key'].str.extract(r'\((.*?)\)')

geog.dropna(subset=['lat_min', 'lat_max', 'lon_min', 'lon_max'], inplace=True)
geog['Geom'] = [Polygon(_coords(row)).wkb for ii, row in geog.iterrows()]

geo_cols = ['GeoID', 'Geom', 'Notes', 'PubID']
geog[geo_cols].to_sql('geographic', db_conn, if_exists='append', index=False)

db_conn.execute("UPDATE geographic SET Geometry = CastToMultiPolygon(ST_GeomFromWKB(Geom, 4326));")

# populate the scientific table
sci['PubID'] = sci['Publication Key'].str.extract(r'\((.*?)\)')
sci.rename(mapper={'Data Type': 'DataType', 'Type of Study': 'StudyType'}, axis='columns', inplace=True)

sci_cols = ['PubID', 'DataType', 'StudyType', 'Category', 'Relevant', 'Description', 'Notes']
sci[sci_cols].to_sql('scientific', db_conn, if_exists='append', index=False)

# populate the dataset table
data[['PubID', 'Num']] = outs['Key'].str.split('.', expand=True)
data.rename(mapper={'Key': 'DataID', 'Archive Location': 'Location', 'Freely Available?': 'Free',
                    'Archive Name': 'ArchiveName', 'Acquisition Start Year': 'StartYear',
                    'Acquisition End Year': 'EndYear', 'Camera calib?': 'Calibration',
                    'Flight Height [m]': 'FlightHeight', 'Height reference': 'HeightRef',
                    'GSD [m]': 'GSD', 'Scanner resolution': 'ScanRes', 'Scanner resolution units': 'ScanUnit',
                    'No. Images': 'NumImgs'}, axis='columns', inplace=True)

data_cols = ['PubID', 'DataID', 'Type', 'Location', 'Free', 'ArchiveName', 'StartYear', 'EndYear',
             'Calibration', 'FlightHeight', 'HeightRef', 'GSD', 'Scale', 'ScanRes', 'ScanUnit',
             'NumImgs', 'Notes']
data[data_cols].to_sql('datasets', db_conn, if_exists='append', index=False)

# populate the processing table
proc[['PubID', 'Num']] = outs['Key'].str.split('.', expand=True)
proc.rename(mapper={'Key': 'DataID', 'Fiducial Marks': 'Fiducial', 'Pre-processing': 'PreProc',
                    'Pre-processing Note': 'PreProcNote', 'Workflow Note': 'WorkNote',
                    'Related paper': 'Related'}, axis='columns', inplace=True)

proc_cols = ['PubID', 'DataID', 'Method', 'Software', 'Version', 'GCPs', 'Fiducial',
             'PreProc', 'PreProcNote', 'WorkNote', 'Related']
proc[proc_cols].to_sql('processing', db_conn, if_exists='append', index=False)

# populate the accuracy table
acc[['PubID', 'Num']] = outs['Key'].str.split('.', expand=True)
acc.rename(mapper={'Key': 'DataID', 'Ground control source XY': 'SourceXY', 'Ground control source Z': 'SourceZ',
                   'Ground control accuracy [m] XY': 'AccuracyXY', 'Ground control accuracy [m] Z': 'AccuracyZ',
                   'No. GCPs': 'NumGCPs', 'Residuals to GCPs [m] XY': 'XYRes', 'Residuals to GCPs [m] Z': 'ZRes', 
                   'Comparison data': 'Comparison', 'Accuracy comparison data [m] XY': 'CompAccXY',
                   'Accuracy comparison data [m] Z': 'CompAccZ', 'Residuals to comparison [m] XY': 'CompResXY',
                   'Residuals to comparison [m] Z': 'CompResZ', 'comparison metric': 'Metric',
                   'Post-Processing': 'PostProc'}, axis='columns', inplace=True)

acc_cols = ['PubID', 'DataID', 'SourceXY', 'SourceZ', 'AccuracyXY', 'AccuracyZ', 'NumGCPs',
            'XYRes', 'ZRes', 'Comparison', 'CompAccXY', 'CompAccZ', 'Metric', 'PostProc', 'Notes']
acc[acc_cols].to_sql('accuracy', db_conn, if_exists='append', index=False)

# populate the outputs table
outs[['PubID', 'Num']] = outs['Key'].str.split('.', expand=True)
outs.rename(mapper={'Key': 'DataID', 'DEM resolution [m]': 'DEMRes',
                    'Orthophoto resolution [m]': 'OrthoRes', 'note': 'Note'}, axis='columns', inplace=True)

outs_cols = ['PubID', 'DataID', 'Output', 'OrthoRes', 'DEMRes', 'Note']
outs[outs_cols].to_sql('outputs', db_conn, if_exists='append', index=False)

# close the connection to the database
db_conn.close()

