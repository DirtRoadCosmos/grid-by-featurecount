# python C:\Users\andresmi\Dropbox\work\queries\split-by-featurecount.py

import os
from osgeo import ogr

print 'ok'


# f = 'C:/Data/names/TIFMEX_WS_MX1_STREETNAME_V_4_0.shp'
# out_f = 'C:/Data/names/TIFMEX_WS_MX1_STREETNAME_V_4_0__GRID.shp'

# f = 'C:/Data/names/mx1_streets_sample.shp'
# out_f = 'C:/Data/names/mx1_streets_sample__GRID.shp'

f = 'C:/Data/split-test/MX1_SMALL/mx1_streets_sample_small.shp'
out_f = 'C:/Data/split-test/MX1_SMALL/mx1_streets_sample_small__GRID.shp'

FCOUNT_THRESHOLD = 100

class GridSquare(object):
    def __init__(self, minX, minY, maxX, maxY):
        self.minX = minX
        self.minY = minY
        self.maxX = maxX
        self.maxY = maxY
        
    def sing_me_a_song(self):
        for line in self.lyrics:
            print line
        print '\n\n'
        
    def add_a_line(self, newline):
        self.lyrics.append(newline)

def splitPoly(p): 

    # based on http://pcjericks.github.io/py-gdalogr-cookbook/geometry.html#quarter-polygon-and-create-centroids
    # 
    # coord0----coord1----coord2
    # |   poly0   |   poly1    |
    # coord3----coord4----coord5
    # |   poly2   |   poly3    |
    # coord6----coord7----coord8
    #

    polys = []

    geom_poly_envelope = p.GetEnvelope()
    minX = geom_poly_envelope[0]
    minY = geom_poly_envelope[2]
    maxX = geom_poly_envelope[1]
    maxY = geom_poly_envelope[3]
    
    print 'splitting', minX, minY, maxX, maxY
    
    coord0 = minX, maxY
    coord1 = minX+(maxX-minX)/2, maxY
    coord2 = maxX, maxY
    coord3 = minX, minY+(maxY-minY)/2
    coord4 = minX+(maxX-minX)/2, minY+(maxY-minY)/2
    coord5 = maxX, minY+(maxY-minY)/2
    coord6 = minX, minY
    coord7 = minX+(maxX-minX)/2, minY
    coord8 = maxX, minY
    
    ring0 = ogr.Geometry(ogr.wkbLinearRing)
    ring0.AddPoint_2D(*coord0)
    ring0.AddPoint_2D(*coord1)
    ring0.AddPoint_2D(*coord4)
    ring0.AddPoint_2D(*coord3)
    ring0.AddPoint_2D(*coord0)
    poly0 = ogr.Geometry(ogr.wkbPolygon)
    poly0.AddGeometry(ring0)
    polys.append(poly0)
    
    ring1 = ogr.Geometry(ogr.wkbLinearRing)
    ring1.AddPoint_2D(*coord1)
    ring1.AddPoint_2D(*coord2)
    ring1.AddPoint_2D(*coord5)
    ring1.AddPoint_2D(*coord4)
    ring1.AddPoint_2D(*coord1)
    poly1 = ogr.Geometry(ogr.wkbPolygon)
    poly1.AddGeometry(ring1)
    polys.append(poly1)
    
    ring2 = ogr.Geometry(ogr.wkbLinearRing)
    ring2.AddPoint_2D(*coord3)
    ring2.AddPoint_2D(*coord4)
    ring2.AddPoint_2D(*coord7)
    ring2.AddPoint_2D(*coord6)
    ring2.AddPoint_2D(*coord3)
    poly2 = ogr.Geometry(ogr.wkbPolygon)
    poly2.AddGeometry(ring2)
    polys.append(poly2)
    
    ring3 = ogr.Geometry(ogr.wkbLinearRing)
    ring3.AddPoint_2D(*coord4)
    ring3.AddPoint_2D(*coord5)
    ring3.AddPoint_2D(*coord8)
    ring3.AddPoint_2D(*coord7)
    ring3.AddPoint_2D(*coord4)
    poly3 = ogr.Geometry(ogr.wkbPolygon)
    poly3.AddGeometry(ring3)
    polys.append(poly3)
    
    return polys

def saveFilteredShapes(inlyr):
    global NewFileCount
    NewFileCount += 1
    filename = ''.join([f[:-4], '_CLIPPED', padNum(NewFileCount), f[-4:]])
    drv = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(filename):
        drv.DeleteDataSource(filename)
    outds = drv.CreateDataSource(filename)
    outlyr = outds.CopyLayer(inlyr,'filteredRoads')
    del inlyr,outlyr,outds
    print 'saved features in poly to %s\n' % (filename)
    
def grabPoly(poly):
    # print 'saving poly', poly
    layer.SetSpatialFilter(None)
    layer.SetSpatialFilter(poly)
    fCount = layer.GetFeatureCount()
    print 'grabbing poly, count = %d' % (fCount)
   
    saveFilteredShapes(layer)
    
    global out_features
    out_features.append((poly, fCount))

def checkPoly(poly):
    layer.SetSpatialFilter(None)
    layer.SetSpatialFilter(poly)
    fCount = layer.GetFeatureCount()
    print 'checked poly, count = %d' % (fCount)
    if fCount <= FCOUNT_THRESHOLD:
        grabPoly(poly)
    else:
        subPolys = splitPoly(poly)
        for poly in subPolys:
            checkPoly(poly)
            
def makePolyFromExtent(e):
    left = e[0]
    right = e[1]
    top = e[3]
    bottom = e[2]
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(left, top)
    ring.AddPoint(right, top)
    ring.AddPoint(right, bottom)
    ring.AddPoint(left, bottom)
    ring.AddPoint(left, top)
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return ring

def padNum(num):
    length = 3
    zerosToAdd = length - 4
    if num < 10:
        zerosToAdd = length - 1
    elif num < 100:
        zerosToAdd = length - 2
    elif num < 1000:
        zerosToAdd = length - 3
    return ''.join(['0'*zerosToAdd, str(num)])

def clip_shp_to_shp(directory, shpclippath, pref="", suf="_clip"):
    # List shp file in a directory (not recursive)
    listResults = glob.glob(os.path.join(directory, '*.shp'))
    # call ogr2ogr to clip with shpclip var
    import subprocess
    for source in listResults:
        subprocess.call(["ogr2ogr", "-f", "ESRI Shapefile", "-clipsrc", shpclip, os.path.basename(source) + "_clip.shp", source])


        
if __name__ == '__main__':

    driver = ogr.GetDriverByName('ESRI Shapefile')

    dataSource = driver.Open(f, 0) # 0 means read-only. 1 means writeable.

    NewFileCount = 0
            
    # Check to see if shapefile is found.
    if dataSource is None:
        print 'Could not open %s' % (f)
    else:
        print 'Opened %s' % (f)
        layer = dataSource.GetLayer()
        featureCount = layer.GetFeatureCount()
        extent = layer.GetExtent()
        print "Number of features in %s: %d \nExtent: %s" % (os.path.basename(f),featureCount, extent)
        
        out_features = []
        fullpoly = makePolyFromExtent(extent)
        checkPoly(fullpoly)
        
     
        # Save extent to a new Shapefile
        outShapefile = out_f
        outDriver = ogr.GetDriverByName("ESRI Shapefile")

        # Remove output shapefile if it already exists
        if os.path.exists(outShapefile):
            outDriver.DeleteDataSource(outShapefile)

        # Create the output shapefile
        outDataSource = outDriver.CreateDataSource(outShapefile)
        outLayer = outDataSource.CreateLayer("grid", geom_type=ogr.wkbPolygon)

        # Add an ID field
        idField = ogr.FieldDefn("road_count", ogr.OFTInteger)
        outLayer.CreateField(idField)

        # Create the feature and set values
        featureDefn = outLayer.GetLayerDefn()
        for tuple in out_features:
            poly = tuple[0]
            count = tuple[1]
            feature = ogr.Feature(featureDefn)
            feature.SetGeometry(poly)
            feature.SetField("road_count", count)
            outLayer.CreateFeature(feature)

        outDataSource.Destroy()

        print '\n\nsaved grid with %d zones' % (len(out_features))
        print 'to %s' % (out_f)
        
    
    
    
    
    
    # if raw_input('\nclip file created. type \'y\' to execute clipping: ') != 'y':
        # print '\nexiting without executing clip'
        # dataSource.Destroy()
        # sys.exit(0)
    
    # print '\nexecuting clip...'
    
    # clipFile = out_f
    # clipDataSource = driver.Open(clipFile, 0)
    # clipLayer = clipDataSource.GetLayer()
    # print str(len(clipLayer)), 'clip regions'
    
    # for index, clipFeature in enumerate(clipLayer):
        # clippedFileName = ''.join([f[:-4], '_part', padNum(index, 3), f[-4:]])
        # if os.path.exists(clippedFileName):
            # driver.DeleteDataSource(clippedFileName)
        # clippedDataSource = driver.CreateDataSource(clippedFileName)
        # clippedLayer = clippedDataSource.CreateLayer('roads', geom_type = ogr.wkbLineString)
        # feature  = layer.GetFeature(0)
        # [clippedLayer.CreateField(feature.GetFieldDefnRef(i)) for i in range(feature.GetFieldCount())]
        # print clippedLayer.GetLayerDefn().GetFieldCount()
        # # layer.Clip(clipFeature, 'new.shp')  # clippedLayer)
        # print 'saved', clippedFileName



# # set clipping shp path
# shpclip = "/home/thomas/git/python_scripts/clipping_area.shp"
# # set dir where searching shp to clip
# directory = os.getcwd()
# clip_shp_to_shp(directory, shpclip)


        # wkt = "POLYGON ((-103.81402655265633 50.253951270672125,-102.94583419409656 51.535568561879401,-100.34125711841725 51.328856095555651,-100.34125711841725 51.328856095555651,-93.437060743203844 50.460663736995883,-93.767800689321859 46.450441890315041,-94.635993047881612 41.613370178339181,-100.75468205106476 41.365315218750681,-106.12920617548238 42.564247523428456,-105.96383620242338 47.277291755610058,-103.81402655265633 50.253951270672125))"
    # layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))

    # for feature in layer:
        # print feature.GetField("STATE_NAME")

        
        # layer.Clip(poly, 'new.shp')
            
    
    
    
    
    
    
    
    
    
    
    # printable = ogr.CreateGeometryFromWkt(wkt)
    # print printable
    # print "Number of features in %s: %d \nExtent: %s" % (os.path.basename(f),featureCount, extent)    

    

    # left = extent[0]
    # midLR = (extent[0]+extent[1])/2
    # right = extent[1]
    
    # top = extent[3]
    # midTB = (extent[2]+extent[3])/2
    # bottom = extent[2]
    
    # ring = ogr.Geometry(ogr.wkbLinearRing)
    # ring.AddPoint(left, top)
    # ring.AddPoint(midLR, top)
    # ring.AddPoint(midLR, midTB)
    # ring.AddPoint(left, midTB)
    # ring.AddPoint(left, top)
    # poly = ogr.Geometry(ogr.wkbPolygon)
    # poly.AddGeometry(ring)
    
    
# from osgeo import ogr
# import os

# shapefile = "states.shp"
# shapefile = f
# driver = ogr.GetDriverByName("ESRI Shapefile")
# dataSource = driver.Open(shapefile, 0)
# layer = dataSource.GetLayer()

# wkt = "POLYGON ((-103.81402655265633 50.253951270672125,-102.94583419409656 51.535568561879401,-100.34125711841725 51.328856095555651,-100.34125711841725 51.328856095555651,-93.437060743203844 50.460663736995883,-93.767800689321859 46.450441890315041,-94.635993047881612 41.613370178339181,-100.75468205106476 41.365315218750681,-106.12920617548238 42.564247523428456,-105.96383620242338 47.277291755610058,-103.81402655265633 50.253951270672125))"
# layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))

# for feature in layer:
    # print feature.GetField("STATE_NAME")

    
    # layer.Clip(poly, 'new.shp')
    
# # clip_shp_to_shp.py
# import os
# import glob
