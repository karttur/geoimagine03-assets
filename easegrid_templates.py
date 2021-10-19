'''
Created on 25 Feb 2021

@author: thomasgumbricht
'''

'''
Created on 26 Oct 2018
Updated 19 feb 2021

@author: thomasgumbricht

Stand alone module for converting output from gdalinfo to the smap.template db table
'''


# Standard library imports

from os import path

import json

# Third party imports

import pyproj 

# Package application imports

from geoimagine.assets import ease2gridproj


def EpsgProj(fromEPSG,toEPSGL):
    
    epsg2proj4D = {}
    
    epsg2proj4D['6931'] = '+proj=laea +lat_0=90 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'

    epsg2proj4D['6932'] = '+proj=laea +lat_0=-90 +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'
    
    epsg2proj4D['6933'] = '+proj=cea +lon_0=0 +lat_ts=30 +x_0=0 +y_0=0 +ellps=WGS84 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'

    
    transfromtoD = {}
    
    ullat,ullon,lrlat,lrlon = 85.0445, -180, 45, 180
    
    corners = [(ullat,ullon),(lrlat,lrlon)]
    
    for toEPSG in toEPSGL:
        
        epsg_in = 'epsg:%s' %(fromEPSG)
        
        epsg_out = 'epsg:%s' %(toEPSG)
        
        transfromtoD[toEPSG] = pyproj.Transformer.from_crs(epsg_in, epsg2proj4D[toEPSG])
        
        for corner in corners:
        
            x,y = transfromtoD[toEPSG].transform(corner[0], corner[1])
            
            print ('epsg',toEPSG, corner, x,y)
            
            
        # EASE grid 2 N corners from EPSG.org -15725.34707351 9009951.03827368 974.37914072 558277.55721523
         
    # reproject coordinates
    for toEPSG in toEPSGL:
        
        epsg_in = 'epsg:%s' %(fromEPSG)
        
        inProj = pyproj.Proj(init=epsg_in)
            
            
        epsg_out = 'epsg:%s' %(toEPSG)
        
        #EASE GRID 2 = epsg:6933 DOES NOT WORK
        
        outProj = pyproj.Proj(init=epsg_out)
    
        #longitude,latitude = transform(inProj, outProj, longitude_masked, latitude_masked)
        
        for corner in corners:
        
            x,y = pyproj.transform(inProj, outProj, corner[1], corner[0])
            
            print ('epsg',toEPSG, corner, x,y)
           
    SNULLE
            

def ReadSubdatasets(srcL):
    '''ReadSubdatasets
    '''
    #Celltype translator from smap hdf metadata to kartturs GDAL based coding
   
    srcFPN, filetype, fromEPSG, toEPSGL, timestep = srcL
    
    jsonFPN = srcFPN.replace('txt','json')
                
    # dict to hold all layers found in the hdf metadata
    formatD = {}
   
    # open the textfile that is the output from gdalinfo
    
    with open(srcFPN) as f:
        content = f.readlines()
    
    #clean out whitespace and end of line
    content = [x.strip() for x in content]
    
    # The processing from here depends on filetype
    
    if filetype == 'hdf4':
        
        valsD = ProcessHdf4(content, formatD)
        
    elif filetype == 'h5':
        
        valsD = ProcessHdf5(content, formatD, fromEPSG, toEPSGL, timestep)
    
    
    WriteBandedJson(path.splitext(jsonFPN)[0], orderL, valsD, 'smap')
    
    #WriteJson(path.splitext(jsonFPN)[0],orderL,valsD,'modispolar')
    
def ProcessHdf4(content, formatD):
    '''
    '''
    
    # from product to source Dict
    
    prd2srcD = {'mod':'modis','myd':'modis','MOD':'modis','MYD':'modis'}
    
    hdffolder2contentD = {'MOD_Grid_Seaice_4km_North':'seaice','MOD_Grid_Seaice_4km_South':'seaice'}
    
    hdfgrid2layeridD = {'Sea_Ice_by_Reflectance_NP':'seaice', 'Ice_Surface_Temperature_NP':'icetemp',
                        'Sea_Ice_by_Reflectance_SP':'seaice', 'Ice_Surface_Temperature_SP':'icetemp'}
    
    hdfgrid2retrieveD = {'Sea_Ice_by_Reflectance_NP':'Y', 'Ice_Surface_Temperature_NP':'Y',
                        'Sea_Ice_by_Reflectance_SP':'Y', 'Ice_Surface_Temperature_SP':'Y'}
    
    hdfgrid2systemD = {'Sea_Ice_by_Reflectance_NP':'ease2n', 'Ice_Surface_Temperature_NP':'ease2n',
                        'Sea_Ice_by_Reflectance_SP':'ease2s', 'Ice_Surface_Temperature_SP':'ease2s'}

    hdfgrid2timestepD = {'Sea_Ice_by_Reflectance_NP':'1D', 'Ice_Surface_Temperature_NP':'1D',
                        'Sea_Ice_by_Reflectance_SP':'1D', 'Ice_Surface_Temperature_SP':'1D'}
    
    hdfgrid2measureD = {'Sea_Ice_by_Reflectance_NP':'N', 'Ice_Surface_Temperature_NP':'R',
                        'Sea_Ice_by_Reflectance_SP':'N', 'Ice_Surface_Temperature_SP':'R'}
    
    hdfgrid2latlonD = {'Sea_Ice_by_Reflectance_NP': [0,0,0,0], 'Ice_Surface_Temperature_NP':[0,0,0,0],
                        'Sea_Ice_by_Reflectance_SP':[0,0,0,0], 'Ice_Surface_Temperature_SP':[0,0,0,0]}
    # See https://nsidc.org/data/MOD29E1D/versions/6 for the EASE grid coordinetes defined here
    hdfgrid2xyD = {'Sea_Ice_by_Reflectance_NP': [-9058902.1345, 9058902.1845, 9058902.1845, -9058902.1345], 
                   'Ice_Surface_Temperature_NP':[-9058902.1345, 9058902.1845, 9058902.1845, -9058902.1345],
                        'Sea_Ice_by_Reflectance_SP':[-9058902.1345, 9058902.1845, 9058902.1845, -9058902.1345], 
                        'Ice_Surface_Temperature_SP':[-9058902.1345, 9058902.1845, 9058902.1845, -9058902.1345]}
    
    hdfgrid2labelD = {'Sea_Ice_by_Reflectance_NP': 'Sea Ice Extent Global 4km EASE-Grid 2.0 North', 
                   'Ice_Surface_Temperature_NP':'Sea Ice Temperature Global 4km EASE-Grid 2.0 North',
                    'Sea_Ice_by_Reflectance_SP':'Sea Ice Extent Global 4km EASE-Grid 2.0 South', 
                    'Ice_Surface_Temperature_SP':'Sea Ice Temperature Global 4km EASE-Grid 2.0 South'}
    
    hdfgrid2unitD = {'Sea_Ice_by_Reflectance_NP': 'class', 
                   'Ice_Surface_Temperature_NP':'kelvin',
                        'Sea_Ice_by_Reflectance_SP':'class', 
                        'Ice_Surface_Temperature_SP':'kelvin'}
    
    hdfgrid2systemD = {'Sea_Ice_by_Reflectance_NP': 'ease2n', 
                   'Ice_Surface_Temperature_NP':'ease2n',
                        'Sea_Ice_by_Reflectance_SP':'ease2s', 
                        'Ice_Surface_Temperature_SP':'ease2s'}
    
    hdfgrid2nullD = {'Sea_Ice_by_Reflectance_NP': 253, 
                   'Ice_Surface_Temperature_NP':8,
                        'Sea_Ice_by_Reflectance_SP':253, 
                        'Ice_Surface_Temperature_SP':8}

    epsgD = {'Sea_Ice_by_Reflectance_NP': 6931, 'Ice_Surface_Temperature_NP': 6931,
                        'Sea_Ice_by_Reflectance_SP':6932, 'Ice_Surface_Temperature_SP':6932}
    
    for line in content:
        
        #Identify layers 
        
        if '_NAME=' in line:
            # SUBDATASET_1_NAME=HDF4_EOS:EOS_GRID:"MOD29E1D.A2000356.006.2015042181022.hdf":MOD_Grid_Seaice_4km_North:Sea_Ice_by_Reflectance_NP
                        
            fpPartsL = line.split(':')
            
            hdfgrid = fpPartsL[len(fpPartsL)-1]
            
            hdffolder = fpPartsL[len(fpPartsL)-2]
            
            fpn = fpPartsL[len(fpPartsL)-3].replace('"','')
            
            filename = path.split(fpn)[1]
                     
            # split the filename
            fnparts = filename.split('.')
            
            # product
            product = fnparts[0]
            
            # version
            version = fnparts[2]

            #source
            source = '%s.%s' %(product, version)
            
            formatD[hdfgrid] = {}
            
            # daacid
            formatD[hdfgrid]['daacid'] = product
            
            # hdffolder
            formatD[hdfgrid]['hdffolder'] = hdffolder
            
            # hdfgrid
            formatD[hdfgrid]['hdfgrid'] = hdfgrid
            
            # band, always just 1 band in the modis polar data
            formatD[hdfgrid]['band'] = 1
            
            # version
            formatD[hdfgrid]['version'] = version
            
            #fileext
            formatD[hdfgrid]['fileext'] = 'tif'
            
            # timestep
            formatD[hdfgrid]['timestep'] = hdfgrid2timestepD[hdfgrid]
            
            #title and label
            title =  hdfgrid.replace('_',' ')
            
            if len(title) > 255:
                
                title = title[0:255]
            
            formatD[hdfgrid]['title']  = title
            
            formatD[hdfgrid]['label'] = hdfgrid2labelD[hdfgrid]
                      
            
            
            formatD[hdfgrid]['system'] = hdfgrid2systemD[hdfgrid]
            
            if formatD[hdfgrid]['system'] == 'ease2n':
                
                formatD[hdfgrid]['region'] = 'northpolar'
                
            elif formatD[hdfgrid]['system'] == 'ease2s':
                
                formatD[hdfgrid]['region'] = 'southpolar'
            
            # EPSG code -
            formatD[hdfgrid]['epsg'] = epsgD[hdfgrid]
            
            #retrieve defaulted to N
            formatD[hdfgrid]['retrieve'] = hdfgrid2retrieveD[hdfgrid]
            
            # source
            formatD[hdfgrid]['source'] = source
            
            # product
            formatD[hdfgrid]['product'] = product
            
            #content
            formatD[hdfgrid]['content'] = hdffolder2contentD[hdffolder]

            #layerid
            formatD[hdfgrid]['layerid'] = formatD[hdfgrid]['prefix'] = hdfgrid2layeridD[hdfgrid]

            #suffix 
            formatD[hdfgrid]['suffix'] = version
            
            #compid
            compid = '%(f)s_%(b)s' %{'f':formatD[hdfgrid]['content'].lower(), 'b':formatD[hdfgrid]['layerid'].lower()}
            
            formatD[hdfgrid]['compid'] = compid
            
            #masked
            formatD[hdfgrid]['masked'] = 'N'
                     
            #measure
            formatD[hdfgrid]['measure'] = hdfgrid2measureD[hdfgrid]
            
            #dataunit
            formatD[hdfgrid]['dataunit'] = hdfgrid2unitD[hdfgrid]
            
            #scalefac
            formatD[hdfgrid]['scalefac'] = 1
            
            #offsetadd
            formatD[hdfgrid]['offsetadd'] = 0
            
            #cellnull
            formatD[hdfgrid]['cellnull'] = hdfgrid2nullD[hdfgrid]
            
            #searchstring for identifying additional metadata further down
            formatD[hdfgrid]['searchcstring'] = '%s_%s' %( hdffolder, hdfgrid)
            
            # easeD is for resetting between north and sourh
            formatD[hdfgrid]['system'] = hdfgrid2systemD[hdfgrid]
                
            formatD[hdfgrid]['ullon'], formatD[hdfgrid]['ullat'],formatD[hdfgrid]['lrlon'], formatD[hdfgrid]['lrlat'] = hdfgrid2latlonD[hdfgrid]
 
            formatD[hdfgrid]['ulx'], formatD[hdfgrid]['uly'],formatD[hdfgrid]['lrx'], formatD[hdfgrid]['lry'] = hdfgrid2xyD[hdfgrid]
                        
        elif '_DESC=' in line:
            #identify celltype for the description (always follows the NAME field 
               
            partsL = line.split('(')
            
            celltype = partsL[1].split(')')[0]
            
            formatD[hdfgrid]['celltype'] = celltypeD[celltype]
            
    #With all the grids identified, loop again to find the unit, cellnull and long name (label)
    for key in formatD:
        
        for line in content:
            
            if formatD[key]['searchcstring'] in line:
                
                if '__FillValue' in line:
                    
                    if line.split('=')[1] != '?':
                        
                        formatD[key]['cellnull'] = line.split('=')[1]
                        
                elif '_units' in  line:
                    
                    formatD[key]['dataunit'] = line.split('=')[1]
                    
                elif '_long_name' in  line:
                    
                    label = line.split('=')[1]
                    
                    #remove comma
                    label = label.replace(',','')
                    
                    label = label.replace('&apos;s','s')
                    
                    if len(label) > 255:
                
                        label = label[0:255]
                    
                    formatD[key]['label'] = label

    return (formatD)
    
def ProcessHdf5(content, formatD, fromEPSG, toEPSGL, timestep):
    '''
    '''
    
    bandD = {}
    bandD['SPL3FTP'] = {}
    bandD['SPL3FTP']['freeze-thaw_freeze-thaw'] = {'1':{'region':'northpolar','system':'ease2n'},'2':{'region':'southpolar','system':'ease2n'}}
    
    bandD['SPL3FTP-E'] = {}
    bandD['SPL3FTP-E']['freeze-thaw_freeze-thaw'] = {'1':{'region':'northpolar','system':'ease2n'},'2':{'region':'southpolar','system':'ease2n'}}
    
    retrieveD = {}
    retrieveD['SPL3FTP'] = {}
    retrieveD['SPL3FTP']['freeze-thaw_freeze-thaw-northpolar'] = 'Y'
    retrieveD['SPL3FTP']['freeze-thaw_freeze-thaw-southpolar'] = 'Y'
    
    retrieveD['SPL3FTP-E'] = {}
    retrieveD['SPL3FTP-E']['freeze-thaw_freeze-thaw-northpolar'] = 'Y'
    retrieveD['SPL3FTP-E']['freeze-thaw_freeze-thaw-southpolar'] = 'Y'
    
    retrieveD['SPL3SMA'] = {}
    retrieveD['SPL3SMA']['soil-moisture_soil-moisture'] = 'Y'
    retrieveD['SPL3SMA']['soil-moisture_bare-soil-roughness'] = 'Y'
    retrieveD['SPL3SMA']['soil-moisture_soil-moisture-error'] = 'Y'
    retrieveD['SPL3SMA']['soil-moisture_soil-moisture-kvz'] = 'Y'
    retrieveD['SPL3SMA']['soil-moisture_soil-moisture-snapshot'] = 'Y'
    
    retrieveD['SPL3SMAP'] = {}
    retrieveD['SPL3SMAP']['soil-moisture_soil-moisture'] = 'Y'
    
    retrieveD['SPL3SMP'] = {}
    retrieveD['SPL3SMP']['soil-moisture-am_soil-moisture-am'] = 'Y'
    retrieveD['SPL3SMP']['soil-moisture-am_soil-moisture-pm'] = 'Y'
    retrieveD['SPL3SMP']['soil-moisture-am_vegetation-water-content'] = 'Y'
    retrieveD['SPL3SMP']['soil-moisture-pm_vegetation-water-content'] = 'Y'
    
    retrieveD['SPL3SMP-E'] = {}
    retrieveD['SPL3SMP-E']['soil-moisture-am_soil-moisture-am'] = 'Y'
    retrieveD['SPL3SMP-E']['soil-moisture-am_soil-moisture-pm'] = 'Y'
    retrieveD['SPL3SMP']['soil-moisture-am_vegetation-water-content-am'] = 'Y'
    retrieveD['SPL3SMP']['soil-moisture-pm_vegetation-water-content-pm'] = 'Y'
    
    # Create projection transofrmers for each to EPSG:
    
    transfromtoD = {}
    
    for toEPSG in toEPSGL:
        
        epsg_in = 'epsg:%s' %(fromEPSG)
        
        epsg_out = 'epsg:%s' %(toEPSG)
        
        transfromtoD[toEPSG] = pyproj.Transformer.from_crs(epsg_in, epsg_out)
        
        
    allBoundsD = {}
        
    allonlatItems = {'Metadata_Extent_eastBoundLongitude':'lrlon',
                   'Metadata_Extent_northBoundLatitude':'ullat',
                   'Metadata_Extent_westBoundLongitude':'ullon',
                   'Metadata_Extent_southBoundLatitude':'lrlat'}
    
    globalBoundsD = {}
        
    globallonlatItems = {'Metadata_Extent_Global_eastBoundLongitude':'lrlon',
                   'Metadata_Extent_Global_northBoundLatitude':'ullat',
                   'Metadata_Extent_Global_westBoundLongitude':'ullon',
                   'Metadata_Extent_Global_southBoundLatitude':'lrlat'}
    
    polarBoundsD = {}
    
    polarlonlatItems = {
        'Metadata_Extent_Polar_eastBoundLongitude':'lrlon',
                   'Metadata_Extent_Polar_northBoundLatitude':'ullat',
                   'Metadata_Extent_Polar_westBoundLongitude':'ullon',
                   'Metadata_Extent_Polar_southBoundLatitude':'lrlat'}
    
    for line in content:
        #Identify projection boundaries 
        
        for item in allonlatItems:

            if item in line:
                
                allBoundsD[ allonlatItems[item] ] = float( line.split('=')[1] )
        
        for item in globallonlatItems:

            if item in line:
                
                globalBoundsD[ globallonlatItems[item] ] = float( line.split('=')[1] )
                
        for item in polarlonlatItems:
            
            if item in line:
               
                polarBoundsD[ polarlonlatItems[item] ] = float( line.split('=')[1] )
  
    for line in content:
        #Identify layers 
        
        if 'NAME=HDF5' in line:
            
            print ('line',line)
            
            fpPartsL = line.split('/')
            
            hdfgrid = fpPartsL[len(fpPartsL)-1]
            
            hdffolder = fpPartsL[len(fpPartsL)-2]
            
            formatD[hdfgrid] = {}
            
            
            #layerid
            
            layerid  = hdfgrid.replace('_','-')
            
            layerid = layerid.replace('-retrieved','')
            
            layerid = layerid.replace('-vegetation-index','-vi')
            
            layerid = layerid.replace('normalized-difference-','nd-')
            
            if layerid == 'soil-moisture' and 'SPL3SMP' in fpPartsL[4]:
            
                if hdffolder == 'Soil_Moisture_Retrieval_Data_AM':
                
                    layerid = '%(b)s-am' %{'b':layerid}
                
                elif hdffolder == 'Soil_Moisture_Retrieval_Data_PM':
                
                    layerid = '%(b)s-pm' %{'b':layerid}
                
                else:
                
                    print (formatD[hdfgrid]['product'], hdffolder)
                    
                    exit("ERRORCHECK 1", hdffolder)
                    
            if len(layerid) > 32:
            
                exitstr =  'layerid name too long',layerid
                
                exit(exitstr)
            
            #region
            if 'polar' in hdffolder.lower():
                
                # polar region data always have two nbands
                formatD[hdfgrid][1] = {}
                
                formatD[hdfgrid][2] = {}
                
                formatD[hdfgrid][1]['layerid'] = '%s-northpolar' %(layerid)
                
                if len( formatD[hdfgrid][1]['layerid'] ) > 64:
                    
                    exitstr = 'layerid too long %s' %( formatD[hdfgrid][1]['layerid'] )
                    
                    exit(exitstr)
                
                formatD[hdfgrid][1]['prefix'] = layerid
                
                formatD[hdfgrid][1]['region'] = 'northpolar'
                
                formatD[hdfgrid][1]['system'] = 'ease2n'
                
                formatD[hdfgrid][1]['band'] = 1
                
                formatD[hdfgrid][1]['epsg'] = 6931
                
                
                
                for key in polarBoundsD:
                    
                    formatD[hdfgrid][1][key] = polarBoundsD[key]     
                
                #formatD[hdfgrid][1]['ulx'], formatD[hdfgrid][1]['uly'] = transfromtoD['6931'].transform(polarBoundsD['ullat'],polarBoundsD['ullon'])
                    
                #formatD[hdfgrid][1]['lrx'], formatD[hdfgrid][1]['lry'] = transfromtoD['6931'].transform(polarBoundsD['lrlat'],polarBoundsD['lrlon'])

                
                formatD[hdfgrid][1]['ulx'], formatD[hdfgrid][1]['uly'] = -9000000.0, 9000000.0
                
                formatD[hdfgrid][1]['lrx'], formatD[hdfgrid][1]['lry'] = 9000000.0, -9000000.0
                
                # LAYER 2 - soutn
                
                formatD[hdfgrid][2]['layerid'] = '%s-southpolar' %(layerid)
                
                formatD[hdfgrid][2]['prefix'] = layerid
                
                formatD[hdfgrid][2]['region'] = 'southpolar'
                
                formatD[hdfgrid][2]['system'] = 'ease2s'
                
                formatD[hdfgrid][2]['band'] = 2
                
                formatD[hdfgrid][2]['epsg'] = 6932
                
                for key in polarBoundsD:
                    
                    formatD[hdfgrid][2][key] = polarBoundsD[key]
                
                #formatD[hdfgrid][2]['ulx'], formatD[hdfgrid][2]['uly'] = transfromtoD['6932'].transform(polarBoundsD['ullat'],polarBoundsD['ullon'])
                    
                #formatD[hdfgrid][2]['lrx'], formatD[hdfgrid][2]['lry'] = transfromtoD['6932'].transform(polarBoundsD['lrlat'],polarBoundsD['lrlon'])
                
                formatD[hdfgrid][2]['ulx'], formatD[hdfgrid][2]['uly'] = -9000000.0, 9000000.0
                
                formatD[hdfgrid][2]['lrx'], formatD[hdfgrid][2]['lry'] = 9000000.0, -9000000.0
                
                #polar regions have two bands, the first is northpolar, the second soutpoarl
                
            else:

                formatD[hdfgrid][1] = {}
                
                formatD[hdfgrid][1]['layerid'] = layerid
                
                formatD[hdfgrid][1]['prefix'] = layerid
                
                formatD[hdfgrid][1]['region'] = 'global'
                
                formatD[hdfgrid][1]['system'] = 'ease2t'
                
                formatD[hdfgrid][1]['band'] = 1
                
                formatD[hdfgrid][1]['epsg'] = 6933
                
                
                
                if len(allBoundsD) > 0:
                    
                    for key in allBoundsD:
                    
                        formatD[hdfgrid][1][key] = allBoundsD[key]
                
                    formatD[hdfgrid][1]['ulx'], formatD[hdfgrid][1]['uly'] = transfromtoD['6933'].transform(allBoundsD['ullat'],allBoundsD['ullon'])
                        
                    formatD[hdfgrid][1]['lrx'], formatD[hdfgrid][1]['lry'] = transfromtoD['6933'].transform(allBoundsD['lrlat'],allBoundsD['lrlon'])
                
                else:
                    
                    for key in globalBoundsD:
                    
                        formatD[hdfgrid][1][key] = globalBoundsD[key]
                    
                    formatD[hdfgrid][1]['ulx'], formatD[hdfgrid][1]['uly'] = transfromtoD['6933'].transform(globalBoundsD['ullat'],globalBoundsD['ullon'])
                        
                    formatD[hdfgrid][1]['lrx'], formatD[hdfgrid][1]['lry'] = transfromtoD['6933'].transform(globalBoundsD['lrlat'],globalBoundsD['lrlon'])
   
            
                
            #source
            source = fpPartsL[4]
                
            for band in formatD[hdfgrid]: 
                       
                
                
                formatD[hdfgrid][band]['source'] = source
                
                formatD[hdfgrid][band]['daacid'],formatD[hdfgrid][band]['version'] = source.split('.')
                
                #product and version
                formatD[hdfgrid][band]['product'], formatD[hdfgrid][band]['version'] = source.split('.')
                            
                #hdfgrid and hdffolder
                formatD[hdfgrid][band]['hdfgrid'] = hdfgrid
                
                formatD[hdfgrid][band]['hdffolder'] = hdffolder
                
                #searchstring for identifying additional metadata further down
                formatD[hdfgrid][band]['searchcstring'] = '%s_%s' %( hdffolder, hdfgrid)
                
                
          
                #title
                title = hdfgrid.replace('_',' ')
                
                formatD[hdfgrid][band]['title'] = title
                
                # Set label to title, updated if infor found furhter down
                formatD[hdfgrid][band]['label'] = title
                
                #folder
                folder = hdffolder.lower()
                folder = folder.replace('_retrieval','')
                folder = folder.replace('_data','')
                folder = folder.replace('_polar','')
                folder = folder.replace('_global','')
                
                formatD[hdfgrid][band]['content'] = folder.replace('_','-')
                
                if len(formatD[hdfgrid][band]['content']) > 32:
                    
                    exitstr = 'content name too long',formatD[hdfgrid]['content']
                    
                    exit(exitstr)
                    
                #suffix 
                formatD[hdfgrid][band]['suffix'] = formatD[hdfgrid][band]['version']
                
                #fileext
                formatD[hdfgrid][band]['fileext'] = 'tif'
                
                #compid
                compid = '%(f)s_%(b)s' %{'f':formatD[hdfgrid][band]['content'].lower(), 'b':formatD[hdfgrid][band]['layerid'].lower()}
                
                formatD[hdfgrid][band]['compid'] = compid
                
                #retrieve defaulted to N
                formatD[hdfgrid][band]['retrieve'] = 'N'
                
                if formatD[hdfgrid][band]['product'] in retrieveD:
                    
                    if compid in retrieveD[ formatD[hdfgrid][band]['product'] ]:
                        
                        formatD[hdfgrid][band]['retrieve'] = 'Y'
                
                
                
                #dataunit
                formatD[hdfgrid][band]['dataunit'] = 'index'
                
                #scalefac
                formatD[hdfgrid][band]['scalefac'] = '1'
                
                #offsetadd
                formatD[hdfgrid][band]['offsetadd'] = '0'
                        
                #cellnull
                formatD[hdfgrid][band]['cellnull'] = '-1'
                
                #measure
                formatD[hdfgrid][band]['measure'] = 'R'
                
                #measure
                formatD[hdfgrid][band]['masked'] = 'N'
                
                # timestep
                formatD[hdfgrid][band]['timestep'] = timestep
                        
                
        elif 'DESC=' in line:
            #identify celltype for the description (always follows the NAME field   
            partsL = line.split('(')
            
            celltype = partsL[1].split(')')[0]
            
            for band in formatD[hdfgrid]:
                
                formatD[hdfgrid][band]['celltype'] = celltypeD[celltype]
                    
    #With all the grids identified, loop again to find the unit, cellnull and long name (label)
    for key in formatD:
        
        for line in content:
            
            if formatD[key][1]['searchcstring'] in line:
                
                if '__FillValue' in line:
                    
                    if line.split('=')[1] != '?':
                        
                        for band in formatD[key]:
                        
                            formatD[key][band]['cellnull'] = line.split('=')[1]
                        
                elif '_units' in  line:
                    
                    for band in formatD[key]:
                        
                        formatD[key][band]['dataunit'] = line.split('=')[1]
                    
                elif '_long_name' in  line:
                    
                    label = line.split('=')[1]
                    
                    #remove comma
                    label = label.replace(',','')
                    
                    label = label.replace('&apos;s','s')
                    
                    if len(label) > 255:
                        
                        for band in formatD[key]:
                            
                            formatD[key][band]['label'] = label[0:255]
                    
                    else:
                                              
                        for band in formatD[key]:
                            
                            formatD[key][band]['label'] = label

    return (formatD)

def WriteJsonEaseNS(jsonBaseFPN,cols,valsD):
    
    for ease in ["ease2n","ease2s"]:
        
        jsonFPN = '%(b)s_%(e)s.json' %{'b':jsonBaseFPN, 'e':ease}
    
        jsonObj = {'process':[]}
        
        jsonObj['process'].append({"processid": "tableinsert","overwrite": False})
        
        jsonObj['process'][0]['parameters'] = {"db": "karttur","schema": ease, "table": "template",'command': {}}
        
        jsonObj['process'][0]['parameters']['command']['columns'] = cols
        
        jsonObj['process'][0]['parameters']['command']['values'] = []
        
        y = -1
        
        for item in valsD:
            
            if valsD[item]['system'] == ease:
                
                y +=1
                
                jsonObj['process'][0]['parameters']['command']['values'].append([])
                
                for col in cols:
                    
                    #jsonObj['process'][0]['parameters']['command']['values'][y].append(valsD[item][col])
                    
                    jsonObj['process'][0]['parameters']['command']['values'][y].append( '"{}"'.format(valsD[item][col]) )
            
        
        with open(jsonFPN, 'w', encoding='utf-8') as f:
            
            json.dump(jsonObj, f, ensure_ascii=False, indent=2)
            
        print (jsonFPN)
            
def WriteJson(jsonBaseFPN,cols,valsD, schema):
       
    jsonFPN = '%(b)s.json' %{'b':jsonBaseFPN}

    jsonObj = {'process':[]}
    
    jsonObj['process'].append({"processid": "tableinsert","overwrite": False})
    
    jsonObj['process'][0]['parameters'] = {"db": "karttur","schema": schema, "table": "template",'command': {}}
    
    jsonObj['process'][0]['parameters']['command']['columns'] = cols
    
    jsonObj['process'][0]['parameters']['command']['values'] = []
    
    for y,item in enumerate(valsD):
            
        jsonObj['process'][0]['parameters']['command']['values'].append([])
        
        for col in cols:
            
            #jsonObj['process'][0]['parameters']['command']['values'][y].append(valsD[item][col])
            
            jsonObj['process'][0]['parameters']['command']['values'][y].append( '"{}"'.format(valsD[item][col]) )
        
    
    with open(jsonFPN, 'w', encoding='utf-8') as f:
        
        json.dump(jsonObj, f, ensure_ascii=False, indent=2)
        
    print (jsonFPN)
    
def WriteBandedJson(jsonBaseFPN,cols,valsD, schema):
       
    jsonFPN = '%(b)s.json' %{'b':jsonBaseFPN}

    jsonObj = {'process':[]}
    
    jsonObj['process'].append({"processid": "tableinsert","overwrite": False})
    
    jsonObj['process'][0]['parameters'] = {"db": "karttur","schema": schema, "table": "template",'command': {}}
    
    jsonObj['process'][0]['parameters']['command']['columns'] = cols
    
    jsonObj['process'][0]['parameters']['command']['values'] = []
    
    y = -1
    
    for layer in valsD:
    
        for band in valsD[layer]:
            
            y += 1
             
            # Add an empty list
            jsonObj['process'][0]['parameters']['command']['values'].append([])
            
            # Loop of all the columns
            for col in cols:
                
                print ('col',col)
                print ('layer',layer)
                print ('band', band)
                print (valsD[layer])
                print (valsD[layer][band])
                print ('')
                #jsonObj['process'][0]['parameters']['command']['values'][y].append(valsD[item][col])
                
                jsonObj['process'][0]['parameters']['command']['values'][y].append( '"{}"'.format( valsD[layer][band][col] ) )
        
    
    with open(jsonFPN, 'w', encoding='utf-8') as f:
        
        json.dump(jsonObj, f, ensure_ascii=False, indent=2)
        
    print (jsonFPN)
        
if __name__ == "__main__":
    
    ''' 
    testing for defining epsg
    EpsgProj('4326', ['6931','6932','6933'])
    
    epsg_proj4D = {}
    '''
    
    # Set some global dictionaries and lists
    
    
    
    celltypeD = {'16-bit unsigned integer': 'UINT16', '32-bit floating-point': 'FLOAT32', '8-bit unsigned character': 'BYTE'}
    
    celltypeD['64-bit floating-point'] = 'FLOAT64'
    
    celltypeD['32-bit unsigned integer'] = 'UINT32'
    
    celltypeD['8-bit unsigned integer'] = 'BYTE'
    
    #items that are inferred to the db table
    orderL = ['daacid','version','hdffolder', 'hdfgrid', 'band','fileext','timestep','title','label', 'region','system', 'epsg', 
              'ullat', 'ullon', 'lrlat','lrlon','ulx','uly','lrx','lry', 'retrieve',
                'source', 'product', 'content', 'layerid', 'prefix', 'suffix', 'compid','masked',
               'measure', 'dataunit', 'scalefac', 'offsetadd','cellnull', 'celltype']

    
    
        
    #srcL = ['/Volumes/SMAP/modispolar/hdfinfo/MOD29E1D_006.txt','hdf4','4326', ['4310'], '1D']
    
    srcL = ['/Volumes/SMAP/smap/hdfinfo/SPL3FTP_003.txt', 'h5', '4326', ['6931','6932','6933'],'1D']
    
    srcL = ['/Volumes/SMAP/smap/hdfinfo/SPL3FTP-E_003.txt', 'h5', '4326', ['6931','6932','6933'],'1D']
    
    srcL = ['/Volumes/SMAP/smap/hdfinfo/SPL3SMA_003.txt', 'h5', '4326', ['6931','6932','6933'],'1D']
    
    srcL = ['/Volumes/SMAP/smap/hdfinfo/SPL3SMAP_003.txt', 'h5', '4326', ['6931','6932','6933'],'1D']
    
    srcL = ['/Volumes/SMAP/smap/hdfinfo/SPL3SMP-E_004.txt', 'h5', '4326', ['6931','6932','6933'],'1D']
    
    srcL = ['/Volumes/SMAP/smap/hdfinfo/SPL3SMP_007.txt', 'h5', '4326', ['6931','6932','6933'],'1D']
    

    
    ReadSubdatasets(srcL)
    
    '''
    For SMAP: Run these sql commands to reset retrieval datasets
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'freeze-thaw_freeze-thaw-northpolar';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'freeze-thaw_freeze-thaw-southhpolar';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture_soil-moisture';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture_bare-soil-roughness';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture_soil-moisture-error';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture_soil-moisture-kvz';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture_soil-moisture-snapshot';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture-am_soil-moisture-am';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture-pm_soil-moisture-pm';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture-am_vegetation-water-content';
    UPDATE smap.template SET retrieve = 'Y' WHERE compid = 'soil-moisture-pm_vegetation-water-content';
    '''
    
    
 
            
