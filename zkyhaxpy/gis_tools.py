#Authored by : Pongporamat C. 
#Updated by Surasak C.

from pandas import DataFrame
import numpy as np
import pandas as pd
import datetime
import os
import subprocess
from tqdm import tqdm
import tarfile
import utm
from osgeo import ogr, gdal, gdal_array, gdalconst
import geopandas as gpd
from shapely import wkt
from shapely.geometry import Polygon, mapping
import rasterio
from rasterio.features import rasterize
from rasterio.mask import mask

import skimage
from skimage import filters, exposure
from skimage.io import imsave

import matplotlib.pyplot as plt

np.seterr(divide='ignore', invalid='ignore')




def extract_bits(img, position):
    """
    Contributed by Pongporamat Charuchinda
    Extract specific bit(s)
    

    Parameters
    ----------
    img: numpy array (M, N)
        QA image.
    position: tuple(int, int) or int
        Bit(s)'s position read from Left to Right (if tuple)
    
    Examples
    --------
    >>> extract_bits(qa_img, position=(6, 5)) # For cloud confidence
    
    Returns
    -------
    None
    """    
    if type(position) is tuple:
        bit_length = position[0]-position[1]+1
        bit_mask = int(bit_length*"1", 2)
        return ((img>>position[1]) & bit_mask).astype(np.uint8)
    
    elif type(position) is int:
        return ((img>>position) & 1).astype(np.uint8)
    
    



def reproject_raster_from_ref(src_path, dest_path, ref_path, dest_dtype='src', driver_nm='GTiff'):
    '''

    Reproject a source raster into a destination raster with reference raster's transform.
    
    Parameters
    ----------
    src_path: str
        A path of the source raster
        
    dest_path: str
        A path of the destination raster to be saved
        
    ref_path: str
        A path of the reference raster
        
    dest_dtype: str
        Data type of the destination raster.
        
    Returns
    -------
    None

	'''  
  

    inputfile = src_path
    input = gdal.Open(inputfile, gdalconst.GA_ReadOnly)
    inputProj = input.GetProjection()
    inputTrans = input.GetGeoTransform()

    
    reference = gdal.Open(ref_path, gdalconst.GA_ReadOnly)
    referenceProj = reference.GetProjection()
    referenceTrans = reference.GetGeoTransform()
    
    x = reference.RasterXSize 
    y = reference.RasterYSize

    if dest_dtype=='src':
        dest_dtype=input.GetRasterBand(1).DataType
    elif dest_dtype=='ref':
        dest_dtype=reference.GetRasterBand(1).DataType
    
    driver= gdal.GetDriverByName(driver_nm)
    output = driver.Create(dest_path, x, y, 1, dest_dtype)
    output.SetGeoTransform(referenceTrans)
    output.SetProjection(referenceProj)

    gdal.ReprojectImage(input,output,inputProj,referenceProj,gdalconst.GRA_Bilinear)

    del output





def df_to_gdf(df, geom_col_nm):
    '''
    INPUT 
    df : dataframe with a column containing geometry in wkt format
    geom_col_nm : str specifies column name of geometry in df
    
    OUTPUT
    return :GeoPandas's DataFrame (gdf)
    '''
    
    df['geometry'] = df[geom_col_nm].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry='geometry', crs={'init' : 'epsg:4326'})
    return gdf



def shape_to_raster(in_shp, out_tif, ref_tif):
    #Code by PongporC 23/Jan/2020
    '''
    params
    ----------------------------------
    in_shp : path of input shapefile
    out_tif : path of output tif
    ref_tif : path of reference tif 
    '''


    InputVector = in_shp
    OutputImage = out_tif

    RefImage = ref_tif

    gdalformat = 'GTiff'
    datatype = gdal.GDT_Byte
    burnVal = 1 #value for the output image pixels
    ##########################################################
    # Get projection info from reference image
    Image = gdal.Open(RefImage, gdal.GA_ReadOnly)

    # Open Shapefile
    Shapefile = ogr.Open(InputVector)
    Shapefile_layer = Shapefile.GetLayer()

    # Rasterise
    print("Rasterising shapefile...")
    Output = gdal.GetDriverByName(gdalformat).Create(OutputImage, Image.RasterXSize, Image.RasterYSize, 1, datatype, options=['COMPRESS=DEFLATE'])
    Output.SetProjection(Image.GetProjectionRef())
    Output.SetGeoTransform(Image.GetGeoTransform()) 

    # Write data to band 1
    Band = Output.GetRasterBand(1)
    Band.SetNoDataValue(0)
    gdal.RasterizeLayer(Output, [1], Shapefile_layer, burn_values=[burnVal])

    # Close datasets
    Band = None
    Output = None
    Image = None
    Shapefile = None

    # Build image overviews
    subprocess.call("gdaladdo --config COMPRESS_OVERVIEW DEFLATE "+OutputImage+" 2 4 8 16 32 64", shell=True)
    print("Done.")



def calculate_polygon_area_from_lat_long(multi_polygon):
    #Code by PongporC 23/Jan/2020
    ''' Return the area of polygon in square metre unit
        "multi_polygon" is the string of latlon 
    '''
    # Create polygon
    ring = ogr.Geometry(ogr.wkbLinearRing)
    coords = split_polygon(multi_polygon)
    for item in coords:
        coord = utm.from_latlon(float(item.split(" ")[1]), float(item.split(" ")[0]))[0:2]
        ring.AddPoint(coord[0], coord[1])
    # Find polygon area
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    polygon = ogr.CreateGeometryFromWkt(poly.ExportToWkt())
    area = polygon.GetArea()
    return area


def raster_to_jpg(output_path, raster=None, raster_path=None, save_im=None, band=1, min_value=-1.0, max_value=1.0, na_value=0.0):  
    #Code by PongporC 23/Jan/2020
    #   
    if raster == None and raster_path != None and save_im==None:
        raster = gdal.Open(raster_path)
        save_im = raster.GetRasterBand(band).ReadAsArray()
    elif raster != None and raster_path == None and save_im==None:
        save_im = raster.GetRasterBand(band).ReadAsArray()
    elif raster == None and raster_path == None and save_im!=None:    
        save_im = save_im
    else :
        print('Invalid input')
        return
    
    max_value = max_value
    min_value = min_value
    
    #fill nan with 0.0
    save_im = np.where(save_im == save_im, save_im, na_value)
    
    #override out-of-bound values with min/max values
    save_im = np.where(save_im > max_value, max_value, save_im)
    save_im = np.where(save_im < min_value, min_value, save_im)
    

    mask = save_im!=na_value
    save_im = (255*((save_im-save_im.min())/(save_im.max()-save_im.min()))).astype('uint8')
    save_im = exposure.equalize_hist(save_im)
    save_im = exposure.equalize_hist(save_im, mask=mask)
    save_im = (255*((save_im-save_im.min())/(save_im.max()-save_im.min()))).astype('uint8')
    imsave(output_path, save_im)    


def show_raster(raster, band=1, min_pctl=2, max_pctl=98, figsize=(10, 10), cmap=None, show_cbar=False):
    '''

    Display raster as a matplotlib's plot.

    Parameters
    ----------
    raster: str or array-like
        A path of raster or an array of raster  
    band: int
        Band ID to be shown in case a path of raster is given.
    min_pctl (max_pctl): int
        Min (Max) percentile to be filterred out.
    figsize: tuple (h, w)
        A tuple for plot figure size (Height, Width)
    show_cbar: boolean
        If True, show cbar

    Returns
    -------
    None

	'''
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    
    
    if type(raster) == np.ndarray:
        arr_raster = raster
    else:
        with rasterio.open(raster) as raster:
            arr_raster = raster.read(band)    
        
    vmin, vmax = np.nanpercentile(arr_raster, (min_pctl, max_pctl))    
    im = ax.imshow(arr_raster, vmin=vmin, vmax=vmax, cmap=cmap)
    
    if show_cbar==True:
        cbar = ax.figure.colorbar(im)
    



def split_polygon(multi_polygon):
    #Code by PongporC 23/Jan/2020
    ''' split the polygon string in excel cell into a list of lat and long
        "multi_polygon" is the string of latlon 
    '''
    polygon_list = multi_polygon.split("(")[3].split(")")[0].split(",")
    return polygon_list



    
    