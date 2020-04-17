from arosics import COREG_LOCAL
from osgeo import gdal
import geoarray
import numpy


### INPUT ARGS
# bands = ['blue', 'bnir']#, 'coastal', 'evi', 'green', 'ndvi', 'nir', 'red', 'redge1', 'redge2', 'redge3', 'swir1', 'swir2'] #Sentinel-2 bands
bands = ['blue', 'evi', 'green', 'ndvi', 'nir', 'red'] #CBERS-4 bands

img_reference = '/home/marujo/Downloads/arosics_test/CBERS/2017_02/C4_64_1M_STK_089098_2017-02-01_2017-02-28_{}.tif'
img_target = '/home/marujo/Downloads/arosics_test/CBERS/2019_10/C4_64_1M_STK_089098_2019-10-01_2019-10-31_{}.tif'
vrt_ref = 'ref.vrt' #create vrt on current working dir
vrt_targ = 'targ.vrt' #create vrt on current working dir

shp_output = '/home/marujo/Downloads/arosics_test/output/output_shapefile.shp'

dst_epsg = 'EPSG:32723'

### AROSICS PARAMS
grid_res = 100
window_size = (64,64)
path_out = '/home/marujo/Downloads/arosics_test/output/out.tif'
projectDir = '/home/marujo/Downloads/arosics_test/output/'


def run_arosics(ref_geoArr, targ_geoArr, grid_res, window_size, path_out, projectDir, shp_output= None):
    kwargs = {
        'grid_res'     : grid_res,
        'window_size'  : window_size,
        'path_out'     : path_out,
        'projectDir'   : projectDir,
        'q'            : False,
    }

    CRL = COREG_LOCAL(ref_geoArr, targ_geoArr, **kwargs)

    CRL.correct_shifts()

    ###Visualize tie point grid with INITIAL shifts present in your input target image
    ## import matplotlib
    ## matplotlib.use("TkAgg")
    # CRL.view_CoRegPoints(figsize=(15,15), backgroundIm='ref')
    ###Visualize tie point grid with shifts present AFTER shift correction
    # CRL_after_corr = COREG_LOCAL(img_reference.format('nir'), CRL.path_out, **kwargs)
    # CRL_after_corr.view_CoRegPoints(figsize=(15,15),backgroundIm='ref')

    if shp_output:
        CRL.tiepoint_grid.to_PointShapefile(path_out=shp_output)

    return


def stack_virtual_raster(image_patter, bands, output):
    band_list = list()
    for band in bands:
        img_path = image_patter.format(band)
        band_list.append(img_path)

    #Set Virtual Raster options
    vrt_options = gdal.BuildVRTOptions(separate='-separate')
    #Create virtual raster
    ds = gdal.BuildVRT(output, band_list, options=vrt_options)
    return ds


def warp(ds):
    ### Geotrans and projections
    geotrans, prj = ds.GetGeoTransform(), ds.GetProjection()

    ### Warp
    gdaloptions = {'format':'VRT', 'srcSRS':prj, 'dstSRS':dst_epsg, 'xRes':geotrans[1], 'yRes':geotrans[5]}
    ds = gdal.Warp('', ds, **gdaloptions)

    return ds


def load_reftar_singband_geoarray(band):
    ### Open Gdal Dataset
    ds_ref = gdal.Open(img_reference.format(band))
    ds_targ = gdal.Open(img_target.format(band))

    ### Warp
    ds_ref = warp(ds_ref)
    ds_targ = warp(ds_targ)

    ### Array, Geotrans and Projections
    ref_array, ref_geotrans, ref_prj = ds_ref.ReadAsArray(), ds_ref.GetGeoTransform(), ds_ref.GetProjection()
    targ_array, targ_geotrans, targ_prj = ds_targ.ReadAsArray(), ds_targ.GetGeoTransform(), ds_targ.GetProjection()

    ### Load into GeoArray
    ref_geoArr = geoarray.GeoArray(ref_array, ref_geotrans, ref_prj)
    targ_geoArr = geoarray.GeoArray(targ_array, targ_geotrans, targ_prj)

    del ds_ref, ds_targ
    return ref_geoArr, targ_geoArr


def load_reftar_multband_geoarray():
    ### Create Virtual Raster
    ds_ref = stack_virtual_raster(img_reference, bands, vrt_ref)
    ds_targ = stack_virtual_raster(img_target, bands, vrt_targ)

    ### Warp
    ds_ref = warp(ds_ref)
    ds_targ = warp(ds_targ)

    ### Array, Geotrans and Projections
    ref_array, ref_geotrans, ref_prj = ds_ref.ReadAsArray(), ds_ref.GetGeoTransform(), ds_ref.GetProjection()
    targ_array, targ_geotrans, targ_prj = ds_targ.ReadAsArray(), ds_targ.GetGeoTransform(), ds_targ.GetProjection()

    ### Load into GeoArray
    ref_geoArr = geoarray.GeoArray(numpy.transpose(ref_array, (1,2,0)), ref_geotrans, ref_prj) #transpose due to geoarray using wrong gdal dimensions
    targ_geoArr = geoarray.GeoArray(numpy.transpose(targ_array, (1,2,0)), targ_geotrans, targ_prj) #transpose due to geoarray using wrong gdal dimensions

    del ds_ref, ds_targ
    return ref_geoArr, targ_geoArr


def main():
    # ref_geoArr, targ_geoArr = load_reftar_singband_geoarray('nir')
    ref_geoArr, targ_geoArr = load_reftar_multband_geoarray()
    run_arosics(ref_geoArr, targ_geoArr, grid_res, window_size, path_out, projectDir, shp_output)
    print('END')
    return


if __name__ == "__main__":
    main()
