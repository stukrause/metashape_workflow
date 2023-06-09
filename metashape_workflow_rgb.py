"""
Script for processing RGB imagery (e.g. Phantom P4) sensor imagery in Metashape with no gcps.

This script requires the Geoid to be installed in Metashape.

"""

import Metashape
import os
import sys
import time
import glob


# Start timer
startTime = time.time()

# Set image and output folder paths
image_folder = sys.argv[1]
output_folder = sys.argv[1]

# Get list of folder names in output folder
foldernames = os.listdir(output_folder)
len(foldernames)

# Loop through folders
#for i in range (0,1):
for i in range (10,len(foldernames)):
    print(os.path.normpath(output_folder + '/' + foldernames[i] + '/' + os.path.basename(foldernames[i])))

    photos = glob.glob(image_folder + "/" + foldernames[i] + '/**/*.jpg', recursive = True)
    
    doc = Metashape.Document()
    doc.read_only = False
    doc.save(image_folder + "/" + foldernames[i] + '/project.psx')

    chunk = doc.addChunk()

    chunk.addPhotos(photos)
    doc.save()

    print(str(len(chunk.cameras)) + " images loaded")
    
    # import reference
    crs = Metashape.CoordinateSystem("EPSG::4326")
    chunk.crs = Metashape.CoordinateSystem("EPSG::4326")

    wkt = 'COMPD_CS["ETRS89 / UTM zone 33N + gcg2016",PROJCS["ETRS89 / UTM zone 33N",GEOGCS["ETRS89",DATUM["European Terrestrial Reference System 1989 ensemble",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6258"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9102"]],AUTHORITY["EPSG","4258"]],PROJECTION["Transverse_Mercator",AUTHORITY["EPSG","9807"]],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","25833"]],VERT_CS["gcg",VERT_DATUM["GCG2016_BB",2005],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]]'

# adapted from https://www.agisoft.com/forum/index.php?topic=9250.0
    out_crs = Metashape.CoordinateSystem(wkt)
    #out_crs = Metashape.CoordinateSystem("EPSG::25833")
    for camera in chunk.cameras:
        if camera.reference.location:
            camera.reference.location = Metashape.CoordinateSystem.transform(camera.reference.location, chunk.crs, out_crs)

    chunk.crs = out_crs
    chunk.updateTransform()

    chunk.analyzePhotos(chunk.cameras)

    # adapted from https://www.agisoft.com/forum/index.php?topic=2487.0
    for j in range(0, len(chunk.cameras)):
       camera = chunk.cameras[j]
        #print(camera)
       quality = camera.frames[0].meta['Image/Quality']
        #print(quality)
       if float(quality) < 0.6:# 0.6
          camera.enabled = False
    doc.save()

    #chunk.matchPhotos(downscale = 1, keypoint_limit = 60000, tiepoint_limit = 10000, generic_preselection = False, 
    chunk.matchPhotos(downscale = 1, keypoint_limit = 40000, tiepoint_limit = 4000, generic_preselection = False, 
        reference_preselection = True)
    doc.save()

    chunk.alignCameras()
    doc.save()
    Metashape.CoordinateSystem.addGeoid("C:/Program Files/Agisoft/Metashape Pro/geoids/gcg2016_BB.tif")
    
    wkt = 'COMPD_CS["ETRS89 / UTM zone 33N + gcg2016",PROJCS["ETRS89 / UTM zone 33N",GEOGCS["ETRS89",DATUM["European Terrestrial Reference System 1989 ensemble",SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6258"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9102"]],AUTHORITY["EPSG","4258"]],PROJECTION["Transverse_Mercator",AUTHORITY["EPSG","9807"]],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","25833"]],VERT_CS["gcg",VERT_DATUM["GCG2016_BB",2005],UNIT["metre",1,AUTHORITY["EPSG","9001"]]]]'
    chunk.crs = Metashape.CoordinateSystem(wkt)
    chunk.updateTransform()
    doc.save()

    crs = Metashape.CoordinateSystem(wkt)
    #crs = Metashape.CoordinateSystem("EPSG::25833")
    shape_path = "D:/path/to/shapefile.shp"
    chunk.importShapes(path=shape_path, crs=crs, boundary_type=Metashape.Shape.OuterBoundary)
    #shape.boundary_type = Metashape.Shape.BoundaryType.OuterBoundary

    chunk.buildDepthMaps(downscale = 2, filter_mode = Metashape.MildFiltering)
    doc.save()  

    # Point cloud: factor image quality is reduced:
    # Low quality = 8
    # Medium quality = 4
    # High quality = 2

    chunk.buildDenseCloud(point_colors=True)
    doc.save()

    chunk.exportPoints(image_folder + '/' + foldernames[i] + '/' + os.path.basename(foldernames[i]) + '_dense_cloud.las', 
        source_data = Metashape.DenseCloudData, clip_to_boundary=False)
        
    chunk.buildModel(source_data = Metashape.DepthMapsData)
    doc.save()
        
    chunk.buildDem(source_data=Metashape.DenseCloudData)
    doc.save()

    chunk.exportRaster(image_folder + '/' + foldernames[i] + '/' + os.path.basename(foldernames[i]) + '_dsm.tif', 
        source_data = Metashape.DataSource.ElevationData, clip_to_boundary=False, save_alpha=False)

    doc.save()

    chunk.buildOrthomosaic(surface_data=Metashape.ElevationData, fill_holes = True)
    doc.save()

    compression = Metashape.ImageCompression()
    compression.tiff_big = True
    chunk.exportRaster(image_folder + '/' + foldernames[i] + '/' + os.path.basename(foldernames[i]) + '_orthomosaic.tif', 
        image_format = Metashape.ImageFormatTIFF, 
        save_alpha=False, 
        clip_to_boundary=False,
        image_compression = compression)

    chunk.exportReport(image_folder + '/' + foldernames[i] + '/' + os.path.basename(foldernames[i]) + '_report.pdf')

    print('Processing finished, results saved to ' + os.path.basename(output_folder) + '.')
    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))
