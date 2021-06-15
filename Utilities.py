import ee
#import geetools
from geetools import tools
import geemap

def DSWE(imgCollection, DEM, aoi=None):
    
    """ Computes the DSWE water index for landsat image collection
    
    args:
        imgCollection: ee.Imagecollection 
            Landsat image collection
        DEM: digital elevation model
        aoi: area of interest or study area bounday
    returns:
        ee.ImageCollection
        collection of DWSE images
    """
    dem = DEM
    aoi = aoi

    def clipImages(img):
            clipped_image = img.clip(aoi).copyProperties(img, ['system:time_start'])
            return clipped_image


    # Mask clouds, cloud shadows, and snow
    def maskClouds(img):
        qa = img.select(['pixel_qa'])
        clouds = qa.bitwiseAnd(8).neq(0).Or(qa.bitwiseAnd(16).neq(0)).Or(qa.bitwiseAnd(32).neq(0)) # Cloud
        return img.addBands(clouds.rename('clouds')) # Add band of contaminated pixels

    # Apply mask
    img_masked = imgCollection.map(maskClouds)

    # ----------------------------------------------------------------------
    # Calculate hillshade mask
    # ----------------------------------------------------------------------
    def addHillshade(img):
        solar_azimuth = img.get('SOLAR_AZIMUTH_ANGLE')
        solar_zenith = img.get('SOLAR_ZENITH_ANGLE'); # solar altitude = 90-zenith
        solar_altitude = ee.Number(90).subtract(ee.Number(solar_zenith))
        return img.addBands(ee.Terrain.hillshade(dem, solar_azimuth, solar_altitude).rename('hillshade'))

    # Add hillshade bands
    img_hillshade = img_masked.map(addHillshade)
    # ----------------------------------------------------------------------
    # Calculate DSWE indices
    # ----------------------------------------------------------------------
    def addIndices(img):
        # NDVI
        img = img.addBands(img.normalizedDifference(['nir', 'red']).select([0], ['ndvi']))
        # MNDWI (Modified Normalized Difference Wetness Index) = (Green - SWIR1) / (Green + SWIR1)
        img = img.addBands(img.normalizedDifference(['green', 'swir1']).select([0], ['mndwi']))
        # MBSRV (Multi-band Spectral Relationship Visible) = Green + Red
        img = img.addBands(img.select('green').add(img.select('red')).select([0], ['mbsrv'])).toFloat()
        # MBSRN (Multi-band Spectral Relationship Near-Infrared) = NIR + SWIR1
        img = img.addBands(img.select('nir').add(img.select('swir1')).select([0], ['mbsrn']).toFloat())
        # AWEsh (Automated Water Extent Shadow) = Blue + (2.5 * Green) + (-1.5 * mbsrn) + (-0.25 * SWIR2)
        img = img.addBands(img.expression('blue + (2.5 * green) + (-1.5 * mbsrn) + (-0.25 * swir2)', {
             'blue': img.select('blue'),
             'green': img.select('green'),
             'mbsrn': img.select('mbsrn'),
             'swir2': img.select('swir2')
        }).select([0], ['awesh'])).toFloat()
        return img

    # Add indices
    img_indices = img_hillshade.map(addIndices)
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # DSWE parameter testing
    # ----------------------------------------------------------------------
    # 1. ========== Function: test MNDWI ===========
    # If (MNDWI > 0.124) set the ones digit (i.e., 00001)
    def test_mndwi(img):
        mask = img.select('mndwi').gt(0.124)
        return img.addBands(mask \
                .bitwiseAnd(0x1F) \
                .rename('mndwi_bit'))

    # 2. ======== Function: compare MBSRV and MBSRN ========
    # If (MBSRV > MBSRN) set the tens digit (i.e., 00010)
    def test_mbsrv_mbsrn(img):
        mask = img.select('mbsrv').gt(img.select('mbsrn'))
        return img.addBands(mask \
                .bitwiseAnd(0x1F) \
                .leftShift(1) \
                .rename('mbsrn_bit'))

    # 3. ======== Function: test AWEsh ========
    # If (AWEsh > 0.0) set the hundreds digit (i.e., 00100)
    def test_awesh(img):
        mask = img.select('awesh').gt(0.0)
        return img.addBands(mask \
                  .bitwiseAnd(0x1F) \
                  .leftShift(2) \
                  .rename('awesh_bit'))

    # 4. ======= Function: test PSW1 ========
    # If (MNDWI > -0.44 && SWIR1 < 900 && NIR < 1500 & NDVI < 0.7) set the thousands digit (i.e., 01000)
    def test_mndwi_swir1_nir(img):
        mask = img.select('mndwi').gt(-0.44) \
                  .And(img.select('swir1').lt(900)) \
                  .And(img.select('nir').lt(1500)) \
                  .And(img.select('ndvi').lt(0.7))
        return img.addBands(mask \
                .bitwiseAnd(0x1F) \
                .leftShift(3) \
                .rename('swir1_bit'))

    # 5. ======= Function: test PSW2 =========
    # If (MNDWI > -0.5 && SWIR1 < 3000 && SWIR2 < 1000 && NIR < 2500 && Blue < 1000) set the ten-thousands digit (i.e., 10000)
    def test_mndwi_swir2_nir(img):
        mask = img.select('mndwi').gt(-0.5) \
                  .And(img.select('swir1').lt(3000)) \
                  .And(img.select('swir2').lt(1000)) \
                  .And(img.select('nir').lt(2500)) \
                  .And(img.select('blue').lt(1000))
        return img.addBands(mask \
                  .bitwiseAnd(0x1F) \
                  .leftShift(4) \
                  .rename('swir2_bit'))

    # Add all bitwise bands to image collection
    img_indices_bit = ee.ImageCollection(img_indices) \
                  .map(test_mndwi) \
                  .map(test_mbsrv_mbsrn) \
                  .map(test_awesh) \
                  .map(test_mndwi_swir1_nir) \
                  .map(test_mndwi_swir2_nir)

    # Function: consolidate individual bit bands
    def sum_bit_bands(img):
        bands = img.select(['mndwi_bit', 'mbsrn_bit', 'awesh_bit', 'swir1_bit', 'swir2_bit'])
        summed_bands = bands.reduce(ee.Reducer.bitwiseOr())
        return img.addBands(summed_bands.rename('summed_bit_band'))

    # Add individual bit bands to image collection and summarize
    img_indices_bit = ee.ImageCollection(img_indices) \
                  .map(test_mndwi) \
                  .map(test_mbsrv_mbsrn) \
                  .map(test_awesh) \
                  .map(test_mndwi_swir1_nir) \
                  .map(test_mndwi_swir2_nir) \
                  .map(sum_bit_bands)
    # --------------------------------------------------------
    # Produce DSWE layers
    # ----------------------------------------------------------------------
    # Construct slope image from DEM
    #dem = dem.clip(aoi); # removed clipping in an attempt to speed up script
    slope = ee.Terrain.slope(dem)
    # Convert binary code into 4 DSWE categories
    def convert_bin_dswe(img):
        reclass = img.select('summed_bit_band').remap([0, 1, 2, 3, 4, 5, 6, 7, 8, 9,
                                                10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
                                                20, 21, 22, 23, 24, 25, 26, 27, 28, 29,
                                                30, 31],

                                                [0, 0, 0, 4, 0, 4, 4, 2, 0, 4,
                                                 4, 2, 4, 2, 2, 1, 4, 4, 4, 2,
                                                 4, 2, 2, 1, 3, 2, 2, 1, 2, 1,
                                                 1, 1]).rename('dswe')
        # ID cloud-contaminated pixels
        reclass = reclass.where(img.select('clouds').eq(1), 9)
        # ID shaded areas
        reclass = reclass.where(img.select('hillshade').lte(110), 8)
        # ID slopes
        reclass = reclass.where(img.select('dswe').eq(4) and slope.gte(5.71).Or  # 10% slope = 5.71°
                      (img.select('dswe').eq(3) and slope.gte(11.31)).Or           # 20% slope = 11.31°
                      (img.select('dswe').eq(2) and slope.gte(16.7)).Or            # 30% slope = 16.7°
                      (img.select('dswe').eq(1) and slope.gte(16.7)), 0);          # 30% slope = 16.7°

        return img.addBands(reclass).select('dswe')

    img_indices_all = img_indices_bit.map(convert_bin_dswe)
    dswe_Images_mosaic = tools.imagecollection.mosaicSameDay(img_indices_all)

    if aoi is None:
        dswe_Images = dswe_Images_mosaic
    else:
        dswe_Images = dswe_Images_mosaic.select('dswe').map(clipImages)

    return dswe_Images

def load_Landsat(aoi, StartDate, EndDate, cloud_thresh):
        
    """
    Function to retrieve and filter Landsat images

    args:
        aoi: region of interest
        StartDate: Starting date to filter data
        EndDate: End date to filter data
        cloud_thresh: Threshold for filtering cloudy images

    returns:
        Image collection of Landsat images
    """
    # Define Landsat surface reflectance bands
    sensor_band_dict = ee.Dictionary({
                        'l8' : ee.List([1,2,3,4,5,6,10]),
                        'l7' : ee.List([0,1,2,3,4,6,9]),
                        'l5' : ee.List([0,1,2,3,4,6,9]),
                        'l4' : ee.List([0,1,2,3,4,6,9])
                        })
    # Sensor band names corresponding to selected band numbers
    bandNames = ee.List(['blue','green','red','nir','swir1','swir2','pixel_qa'])
    # ------------------------------------------------------
    # Landsat 4 - Data availability Aug 22, 1982 - Dec 14, 1993
    ls4 = ee.ImageCollection('LANDSAT/LT04/C01/T1_SR') \
              .filterBounds(aoi.geometry()) \
              .select(sensor_band_dict.get('l4'), bandNames)

    # Landsat 5 - Data availability Jan 1, 1984 - May 5, 2012
    ls5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR') \
              .filterBounds(aoi.geometry()) \
              .select(sensor_band_dict.get('l5'), bandNames)

    # Landsat 7 - Data availability Jan 1, 1999 - Aug 9, 2016
    # SLC-off after 31 May 2003
    ls7 = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR') \
                  .filterDate('1999-01-01', '2003-05-31') \
                  .filterBounds(aoi.geometry()) \
                  .select(sensor_band_dict.get('l7'), bandNames)

    # Post SLC-off; fill the LS 5 gap
    # -------------------------------------------------------
    # Landsat 7 - Data availability Jan 1, 1999 - Aug 9, 2016
    # SLC-off after 31 May 2003
    ls7_2 = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR') \
                  .filterDate('2012-05-05', '2014-04-11') \
                  .filterBounds(aoi.geometry()) \
                  .select(sensor_band_dict.get('l7'), bandNames)

    # --------------------------------------------------------
    # Landsat 8 - Data availability Apr 11, 2014 - present
    ls8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
                  .filterBounds(aoi.geometry()) \
                  .select(sensor_band_dict.get('l8'), bandNames)

    # Merge landsat collections
    l4578 = ee.ImageCollection(ls4 \
              .merge(ls5) \
              .merge(ls7) \
              .merge(ls7_2) \
              .merge(ls8).sort('system:time_start')) \
              .filterDate(StartDate, EndDate)\
            .filter(ee.Filter.lt('CLOUD_COVER', cloud_thresh))

    return l4578

def load_Sentinel1(site, StartDate, EndDate):
    """
    Function to retrieve and filter Sentinel-1 images

    args:
        aoi: region of interest
        StartDate: Starting date to filter data
        EndDate: End date to filter data

    returns:
        Image collection of Sentinel-1 images
    """
    filtered_col = ee.ImageCollection('COPERNICUS/S1_GRD')\
        .filterDate(StartDate,EndDate)\
        .filter(ee.Filter.eq('instrumentMode', 'IW'))\
        .filterMetadata('transmitterReceiverPolarisation', 'equals',['VV','VH'])\
        .filterMetadata('resolution_meters', 'equals', 10)\
        .filterBounds(site)\
        .sort('system:time_start')
    return filtered_col

def load_Sentinel2(aoi, StartDate, EndDate, cloud_thresh):
    """
    Function to retrieve and filter Sentinel-2 images

    args:
        aoi: region of interest
        StartDate: Starting date to filter data
        EndDate: End date to filter data
        cloud_thresh: Threshold for filtering cloudy images

    returns:
        Image collection of Sentinel-2 images
    """
    filtered_col = ee.ImageCollection('COPERNICUS/S2')\
        .filterDate(StartDate,EndDate)\
        .filterBounds(aoi)\
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_thresh))\
        .sort('system:time_start')\
        .select(['B2','B3','B4','B8','B11','B12','QA60'], ['blue','green','red','nir','swir1','swir2','pixel_qa'])
    return filtered_col

def load_NAIP(aoi, StartDate, EndDate):
    """
    Function to retrieve and filter NAIP images

    args:
        aoi: region of interest
        StartDate: Starting date to filter data
        EndDate: End date to filter data

    returns:
        Image collection of NAIP images
    """
    filtered_col = ee.ImageCollection('USDA/NAIP/DOQQ')\
        .filterDate(StartDate,EndDate)\
        .filterBounds(aoi)\
        .sort('system:time_start')
    return filtered_col

def load_shapefile(shapefile):
    """
    Function to laod shapefile
        
    args:
        Shapefile: An ESRI shapefile for the aoi boudary (WGS84 projection)

    returns:
        ee user boundary
    """
    aoi = geemap.shp_to_ee(shapefile)
    return aoi

def maskS2clouds(image):
    """
    Function to mask out clouds from Sentinel-2 images
        
    args:
        Sentinel-2 image

    returns:
        Cloud masked image
    """
    orig = image
    qa = image.select('pixel_qa')
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11
    mask = qa.bitwiseAnd(cloudBitMask).eq(0) \
    .And(qa.bitwiseAnd(cirrusBitMask).eq(0))
    return (image.updateMask(mask).copyProperties(orig, orig.propertyNames()))

def maskLandsatclouds(image):
    """
    Function to mask out clouds from Landsat images
        
    args:
        Landsat image

    returns:
        Cloud masked image
    """
    orig = image
    qa = image.select('pixel_qa')
    #cloudsShadowBitMask = 1 << 3
    cloudsBitMask = 1 << 4
    mask = qa.bitwiseAnd(cloudsBitMask).eq(0) #\
    #.And(qa.bitwiseAnd(cloudsBitMask).eq(0))
    return (image.updateMask(mask).copyProperties(orig, orig.propertyNames()))

 