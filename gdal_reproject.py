'''
Created on 1 Mar 2021

@author: thomasgumbricht
'''

# import the package
from osgeo import osr, ogr

# Set the source projection (geographic coordinates)
source = osr.SpatialReference()
source.ImportFromEPSG(4326) # 4326 represents geographic coordinates

# Set the target projection (EASE-grid)
target = osr.SpatialReference()
target.ImportFromEPSG(6931) # 6931 represents the global/tropial EASE grid

# Set the transformation
transform = osr.CoordinateTransformation(source, target)

# Create a coordinate point
point = ogr.CreateGeometryFromWkt("POINT (45 180 )")

# Transform the coordinate point
point.Transform(transform)

# proint out the transformed coordinate point
print ( point.ExportToWkt() )
