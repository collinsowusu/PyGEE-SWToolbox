import ee
import eemont
from geetools import tools, cloud_mask
import geemap
import hydrafloods as hf
import hydrafloods.depths as hfd
from hydrafloods import geeutils, corrections
from urllib.request import urlretrieve
import shutil
from geetools.utils import makeName
import os

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

#         return img.addBands(reclass).select('dswe')
        return img.addBands(reclass)

    img_indices_all = img_indices_bit.map(convert_bin_dswe)
    dswe_Images_mosaic = tools.imagecollection.mosaicSameDay(img_indices_all)

    if aoi is None:
        dswe_Images = dswe_Images_mosaic
    else:
#         dswe_Images = dswe_Images_mosaic.select('dswe').map(clipImages)
        dswe_Images = dswe_Images_mosaic.map(clipImages)

    return dswe_Images


def load_Landsat_Coll_2(aoi, StartDate, EndDate, cloud_thresh):
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
        'l8': ee.List([1, 2, 3, 4, 5, 6, 17]),
        'l7': ee.List([0, 1, 2, 3, 4, 5, 17]),
        'l5': ee.List([0, 1, 2, 3, 4, 5, 17]),
        'l4': ee.List([0, 1, 2, 3, 4, 5, 17])
    })
    # Sensor band names corresponding to selected band numbers
    bandNames = ee.List(['blue', 'green', 'red', 'nir',
                        'swir1', 'swir2', 'pixel_qa'])

    # Apply scaling factors
    # def applyScaleFactors(img):
    #     orig = img
    #     qa = img.select('pixel_qa')
    #     opticalBands_scaled = img.select(
    #         ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']).multiply(0.0000275).add(-0.2)
    #     return opticalBands_scaled.addBands(qa).copyProperties(orig, orig.propertyNames())
    
    def applyScaleFactors(img):
        orig = img
        qa = img.select('pixel_qa')
        opticalBands_scaled = img.select(['blue', 'green', 'red', 'nir', 'swir1', 'swir2']).multiply(0.0000275).add(-0.2)
        return img.addBands(opticalBands_scaled, None, True).addBands(qa, None, True).copyProperties(orig, orig.propertyNames())

    # ------------------------------------------------------
    # Landsat 4 - Data availability Aug 22, 1982 - Dec 14, 1993
    ls4 = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') \
        .filterBounds(aoi.geometry()) \
        .select(sensor_band_dict.get('l4'), bandNames)

    # Landsat 5 - Data availability Jan 1, 1984 - May 5, 2012
    ls5 = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
        .filterBounds(aoi.geometry()) \
        .select(sensor_band_dict.get('l5'), bandNames)

    # Landsat 7 - Data availability Jan 1, 1999 - Aug 9, 2016
    # SLC-off after 31 May 2003
    ls7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
        .filterDate('1999-01-01', '2003-05-31') \
        .filterBounds(aoi.geometry()) \
        .select(sensor_band_dict.get('l7'), bandNames)

    # Post SLC-off; fill the LS 5 gap
    # -------------------------------------------------------
    # Landsat 7 - Data availability Jan 1, 1999 - Aug 9, 2016
    # SLC-off after 31 May 2003
    ls7_2 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
        .filterDate('2012-05-05', '2014-04-11') \
        .filterBounds(aoi.geometry()) \
        .select(sensor_band_dict.get('l7'), bandNames)

    # --------------------------------------------------------
    # Landsat 8 - Data availability Apr 11, 2014 - present
    ls8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(aoi.geometry()) \
        .select(sensor_band_dict.get('l8'), bandNames)

    # Merge landsat collections
    l4578 = ee.ImageCollection(ls4
                               .merge(ls5)
                               .merge(ls7)
                               .merge(ls7_2)
                               .merge(ls8).sort('system:time_start')) \
        .filterDate(StartDate, EndDate)\
        .filter(ee.Filter.lt('CLOUD_COVER', cloud_thresh))

    l4578_scaled = l4578.map(applyScaleFactors)

    return l4578_scaled
    
def load_Landsat_Coll_1(aoi, StartDate, EndDate, cloud_thresh):
        
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
        .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))\
        .filterMetadata('resolution_meters', 'equals', 10)\
        .filterBounds(site)\
        .sort('system:time_start')
    return filtered_col

def slope_correction(img):
    elev = ee.Image("USGS/SRTMGL1_003").select("elevation")
    corrected_image = corrections.slope_correction(img,elevation=elev)
    return corrected_image.copyProperties(img, img.propertyNames())

def SAR_indices(img):
    # From Huang et al. (2018), doi: 10.3390/rs10050797
    # Polarized raio
    PR = img.select('VH').divide(img.select('VV')).rename('PR')
    # Normalized Difference Polarized Index (NDPI)
    NDPI = img.normalizedDifference(['VV','VH']).rename('NDPI')
    # Normalized VH Index (NVHI)
    NVHI = img.expression('VH / (VV + VH)', {
                                'VH': img.select('VH'),
                                'VV': img.select('VV')}).rename('NVHI')
    # Normalized VV Index (NVVI)
    NVVI = img.expression('VV / (VV + VH)', {
                                'VH': img.select('VH'),
                                'VV': img.select('VV')}).rename('NVVI')
    
    return img.addBands([PR,NDPI,NVHI,NVVI])

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
    filtered_col = ee.ImageCollection('COPERNICUS/S2_SR')\
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

def load_boundary(boundaryfile):
    """
    Function to laod shapefile
        
    args:
        boundaryfile: An ESRI shapefile for the aoi boudary (WGS84 projection) or KML OR KMZ

    returns:
        ee user boundary
    """
    extension = boundaryfile[-3:]
    if extension == "shp":       
        aoi = geemap.shp_to_ee(boundaryfile)
    elif extension == "kml":
        aoi = geemap.kml_to_ee(boundaryfile)
    else:
        aoi = geemap.kmz_to_ee(boundaryfile)
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
    cloudsShadowBitMask = 1 << 3
    cloudsBitMask = 1 << 4
    mask = qa.bitwiseAnd(cloudsBitMask).eq(0) \
    .And(qa.bitwiseAnd(cloudsBitMask).eq(0))
    return (image.updateMask(mask).copyProperties(orig, orig.propertyNames()))

def cloudMaskL457(image):
    orig = image
    qa = image.select('pixel_qa')
    # If the cloud bit (5) is set and the cloud confidence (7) is high
    # or the cloud shadow bit is set (3), then it's a bad pixel.
    cloud = qa.bitwiseAnd(1 << 5).And(qa.bitwiseAnd(1 << 7)).Or(qa.bitwiseAnd(1 << 3))
    mask2 = image.mask().reduce(ee.Reducer.min())
    return (image.updateMask(cloud.Not()).updateMask(mask2).copyProperties(orig, orig.propertyNames()))

def compute_histogram(img,aoi,img_scale):
    
    reducers = ee.Reducer.histogram(255,2).combine(reducer2=ee.Reducer.mean(), sharedInputs=True)\
                .combine(reducer2=ee.Reducer.variance(), sharedInputs= True)
    histogram = img.select('waterMask').reduceRegion(
        reducer=reducers,
        geometry=aoi.geometry(),
        scale=img_scale,
        bestEffort=True)
    return histogram

def otsu(histogram):
    """
    Function to use Otsu algorithm to compute DN that maximizes interclass variance in the region 

    args:
        Histogram

    returns:
        Otsu's threshold
    """
    counts = ee.Array(ee.Dictionary(histogram).get('histogram'))
    means = ee.Array(ee.Dictionary(histogram).get('bucketMeans'))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    sum = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    mean = sum.divide(total)
    indices = ee.List.sequence(1, size)
    
    # Compute between sum of squares, where each mean partitions the data.
    def func_bss(i):
        aCounts = counts.slice(0, 0, i)
        aCount = aCounts.reduce(ee.Reducer.sum(), [0]).get([0])
        aMeans = means.slice(0, 0, i)
        aMean = aMeans.multiply(aCounts) \
            .reduce(ee.Reducer.sum(), [0]).get([0]) \
            .divide(aCount)
        bCount = total.subtract(aCount)
        bMean = sum.subtract(aCount.multiply(aMean)).divide(bCount)
        return aCount.multiply(aMean.subtract(mean).pow(2)).add(
               bCount.multiply(bMean.subtract(mean).pow(2)))
    
    bss = indices.map(func_bss)
    return means.sort(bss).get([-1])

def image_scale(img):
    """Retrieves the image cell size (e.g., spatial resolution)
    Args:
        img (object): ee.Image
    Returns:
        float: The nominal scale in meters.
    """   
    return img.projection().nominalScale().getInfo()

def image_max_value(img, region=None, scale=None):
    """Retrieves the maximum value of an image.
    Args:
        img (object): The image to calculate the maximum value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    max_value = ee.Number(img.reduceRegion(**{
        'reducer': ee.Reducer.max(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12,
        'bestEffort':True
        }).values().get(0))
    return max_value.getInfo()

def image_min_value(img, region=None, scale=None):
    """Retrieves the minimum value of an image.
    Args:
        img (object): The image to calculate the minimum value.
        region (object, optional): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float, optional): A nominal scale in meters of the projection to work in. Defaults to None.
    Returns:
        object: ee.Number
    """
    if region is None:
        region = img.geometry()

    if scale is None:
        scale = image_scale(img)

    min_value = ee.Number(img.reduceRegion(**{
        'reducer': ee.Reducer.min(),
        'geometry': region,
        'scale': scale,
        'maxPixels': 1e12,
        'bestEffort':True
    }).values().get(0))
    return min_value.getInfo()

def estimateDepths_FromDEM(dem, site, img_scale):
    """Estimates water depth based on water extent and DEM elevations
    Args:
        dem (object): Elevation data
        region (object): The region over which to reduce data. Defaults to the footprint of the image's first band.
        scale (float): A nominal scale in meters of the projection to work in. Defaults to None.
    Returns:
        object: ee.Image
    """
    def wrap(img):
        """Estimates water depth based on water extent and DEM elevations
        Args:
            img (object): Water mask
        Returns:
            object: ee.Image
        """
        flood = img.select('waterMask')
        dem_mask = dem.mask(flood)

        polys = flood.addBands(dem_mask).reduceToVectors(**{
                'geometry':site,
                'scale':img_scale,
                'reducer':ee.Reducer.max(),
                'eightConnected': False,
                'geometryType':'polygon',
                'crs': flood.projection()
                })

        polys2 = dem.reduceRegions(polys, ee.Reducer.max())

        properties = ['max'] # property for creating max image
        maxImage = polys2.filter(ee.Filter.notNull(properties))\
                    .reduceToImage(**{'properties': properties, 'reducer': ee.Reducer.first()})

        Depths = maxImage.subtract(dem_mask).rename('Depth')
        DepthFilter = Depths.where(Depths.lt(0),0)
        return img.addBands(DepthFilter)
    return wrap

# def estimateDepths_Experimental(dem, site, img_scale):
#     """Estimates water depth based on water extent and DEM elevations
#     Args:
#         dem (object): Elevation data
#         region (object): The region over which to reduce data. Defaults to the footprint of the image's first band.
#         scale (float): A nominal scale in meters of the projection to work in. Defaults to None.
#     Returns:
#         object: ee.Image
#     """
#     def wrap(img):
#         """Estimates water depth based on water extent and DEM elevations
#         Args:
#             img (object): Water mask
#         Returns:
#             object: ee.Image
#         """
#         flood = img.select('waterMask')
#         watermap_edge = (flood.selfMask().unmask(-999).focal_min(img_scale, "square", "meters").eq(-999))
#         watermap_edge = watermap_edge.updateMask(flood.unmask(0))
#         watermap_edge = watermap_edge.selfMask()

#         edge_Elevations = dem.updateMask(watermap_edge)
#         mean_Elev = ee.Number(edge_Elevations.reduceRegion(**{
#                             'reducer': ee.Reducer.mean(),
#                             'geometry': site,
#                             'scale': img_scale,
#                             'maxPixels': 1e12
#                             }).values().get(0)).getInfo()

#         dem_mask = dem.mask(flood) # extract DEM values of the flooded area

#         mean_Elev_Image = ee.Image(mean_Elev)
        
#         maxImage = polys2.filter(ee.Filter.notNull(properties))\
#             .reduceToImage(**{'properties': properties, 'reducer': ee.Reducer.first()})

#         Depths = maxImage.subtract(dem_mask).rename('Depth')
#         DepthFilter = Depths.where(Depths.lt(0), 0)
# #         return DepthFilter.copyProperties(flood, flood.propertyNames())
#         return img.addBands(DepthFilter)
#     return wrap

def add_depth_variables(img):
    orig = img
    scaled_image = img.multiply(1000)
    mod_green = scaled_image.select('green').log().rename('mod_green')
    mod_swir1 = scaled_image.select('swir1').log().rename('mod_swir1')
    stumpf = mod_green.divide(mod_swir1).rename('Stumpf')
    return img.addBands([mod_green,mod_swir1,stumpf]).copyProperties(orig, orig.propertyNames())

def RF_Depth_Estimate(rf_ee_classifier):
    def wrap(img):
        orig = img
        waterMask = img.select('waterMask')
        feature_names = ['mod_green','mod_swir1']
        depth_map = img.select(feature_names).classify(rf_ee_classifier).rename('Depth')
        depth_map = depth_map.mask(waterMask).selfMask()
        return img.addBands(depth_map).copyProperties(orig, orig.propertyNames())
    return wrap

def Mod_Stumpf_Depth_Estimate(img):
    orig = img
    waterMask = img.select('waterMask')
    depth_map = img.expression('(7.36996152 * Stumpf) - 6.414202728845137', {'Stumpf': img.select('Stumpf')}).rename('Depth')
    depth_map = depth_map.mask(waterMask).selfMask()
    return img.addBands(depth_map).copyProperties(orig, orig.propertyNames())

def Mod_Lyzenga_Depth_Estimate(img):
    orig = img
    waterMask = img.select('waterMask')
    depth_map = img.expression('(0.40411079 * mod_green) + (-0.65231439 *mod_swir1) + 4.364452405536028', {
                                'mod_green': img.select('mod_green'),
                                'mod_swir1': img.select('mod_swir1')}).rename('Depth')
    depth_map = depth_map.mask(waterMask).selfMask()
    return img.addBands(depth_map).copyProperties(orig, orig.propertyNames())

def FwDET_Depth_Estimate(dem):
    """Estimates depth of water based on the FwDET algorithm (Peter et al 2020 as implementd in hydrafloods)
    Args:
        img (ee.Image): Image containing a 'waterMask' band
        dem (object): Elevation data
    Returns:
        object: ee.Image with depth band
    """
    def wrap(img):
        orig = img
        watermask = img.select('water')
        depth_map = hfd.fwdet(watermask,dem).rename('Depth')
        return img.addBands(depth_map).copyProperties(orig, orig.propertyNames())
    return wrap

def local_download(img, filename, region, scale):
    print("Generating URL ...")
    proj = img.select(0).projection()
    crs = proj.getInfo()['crs']
    img = img.reproject(crs=crs,scale=scale)
    url = ee.data.makeDownloadUrl(ee.data.getDownloadId({
            'image': img,
            'region': region.geometry(),
            'filePerBand': False,
            'format':"GEO_TIFF",
            'maxPixels':1e13,
            'scale':scale,
            }))
    print(f"Downloading data from {url}")
    local_zip, headers = urlretrieve(url)
    shutil.move(local_zip,filename)
    return

def export_image_collection_to_local(ee_object, out_dir, name_pattern, date_pattern, extra, scale, region=None):
    """Exports an ImageCollection as GeoTIFFs to local drive.
    Adapted from geemap's "ee_export_image_collection" method
    Args:
        ee_object (object): The ee.ImageCollection to download.
        out_dir (str): The output directory for the exported images.
        name_pattern (str): The file naming pattern
        date_pattern (str): The date pattern
        extra (dict): A dictionary of additional file naming parameters; satellite platform and type of image collection
        scale (float, optional): A default scale to use for any bands that do not specify one; ignored if crs and crs_transform is specified. Defaults to None.
      crs (str, optional): A default CRS string to use for any bands that do not explicitly specify one. Defaults to None.
      region (object, optional): A polygon specifying a region to download; ignored if crs and crs_transform is specified. Defaults to None.
    """

    if not isinstance(ee_object, ee.ImageCollection):
        print("The ee_object must be an ee.ImageCollection.")
        return

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    try:

        count = int(ee_object.size().getInfo())
        print(f"Total number of images: {count}\n")

        for i in range(0, count):
            image = ee.Image(ee_object.toList(count).get(i))
            name_Pattern = name_pattern
            date_pattern = date_pattern
            extra = extra
            name = makeName(image, name_Pattern, date_pattern, extra).getInfo()
            name = name + ".tif"
            filename = os.path.join(os.path.abspath(out_dir), name)
            print(f"Exporting {i + 1}/{count}: {name}")
            local_download(
                image,
                filename=filename,
                region=region,
                scale=scale
            )
            print("\n")

    except Exception as e:
        print(e)
