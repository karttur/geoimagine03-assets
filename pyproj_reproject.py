'''
Created on 1 Mar 2021

@author: thomasgumbricht
'''

# import the package
'''
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

# print out the transformed coordinate point
print ( point.ExportToWkt() )

'''

# import the package
from pyproj import Proj, transform

# Set the source projection (geographic coordinates)
srcProj = Proj('epsg:4326') # 4326 represents geographic coordinates
        
# Set the target projection (EASE-grid)
dstProj = Proj('epsg:6931') # 6933 represents the global/tropial EASE grid
       
# Transform the coordinate point 
x,y = transform(srcProj, dstProj, -45, 180)

# print out the transformed coordinate point
print ('EASE-grid', x, y)
