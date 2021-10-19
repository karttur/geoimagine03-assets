'''
Created on 19 Feb 2021

@author: thomasgumbricht
'''

# Standard library imports

import os

from sys import exit

from shutil import move

import urllib.request

from html.parser import HTMLParser

# Third party imports

import h5py

import numpy as np

from osgeo import gdal, osr

# Package application imports

from geoimagine.params import Composition, Layer, LayerCommon

#from ancillary import ancillary_import

import geoimagine.support.karttur_dt as mj_dt 

from geoimagine.assets.hdf_2_geotiff import ProjEASEgridHdf

def ParseHtml(FPN, dataset):
    ''' Parse html file and exract <a> tags identifying hdf files
    '''
    
    tmpFP = os.path.split(FPN)[0]
    
    tmpFP = os.path.split(tmpFP)[0]
    
    tmpFP = os.path.join(tmpFP,'tmpcsv')
    
    if not os.path.exists(tmpFP):
    
        os.makedirs(tmpFP)

    FPN = 'file://%(fpn)s' %{'fpn':FPN}
    
    req = urllib.request.Request(FPN)
    
    with urllib.request.urlopen(req) as response:
        
        html = response.read()
        
    if dataset == 'modisdatapool':  
        
        parser = ModisDataPoolParser()
        
    elif dataset == 'modispolar':  
        
        parser = ModisPolarParser()
        
    elif dataset == 'smap':
        
        parser = SmapParser()
        
    elif dataset == 'ASTGTM':
        
        parser = AstgtmParser()
        
    elif dataset == 'CopernicusDEM':
        
        parser = CopernicusDEMParser()

    parser.queryD = {}
    
    parser.feed(str(html)) 
    
    return (parser.queryD)

def ReadMODIShtml(session,srcFPN,acqdate):
    '''
    '''
    
    queryD = ParseHtml(srcFPN, 'modisdatapool')
            
    for item in queryD:
        
        queryD[item]['acqdate'] = acqdate
        
        session._InsertDaacData(queryD[item])

def ReadMODISPolarhtml(session,srcFPN,acqdate):
    '''
    '''
    
    queryD = ParseHtml(srcFPN, 'modispolar')
        
    queryD['acqdate'] = acqdate
    
    session._InsertModisPolarData(queryD)
    
def ReadASTGTMhtml(session,srcFPN,acqdate):
    '''
    '''
    
    queryD = ParseHtml(srcFPN,'ASTGTM')
        
    return (queryD)

def ReadCopernicusDEMhtml(srcFPN):
    '''
    '''
    
    queryD = ParseHtml(srcFPN,'CopernicusDEM')
        
    return (queryD)
     
def ReadSMAPhtml(session,srcFPN,acqdate):
    '''
    '''
    
    queryD = ParseHtml(srcFPN,'smap')
        
    queryD['acqdate'] = acqdate
    
    session._InsertDaacData(queryD)
    
class ModisDataPoolParser(HTMLParser):
    ''' For parsing downloaded index files of tiled MODIS online content
    '''
            
    def handle_starttag(self, tag, attrs):
        ''' parse <a> tags to find files for downloading
        '''
        
        if tag == "a":
            
            # Check the list of defined attributes.
            for name, value in attrs:
                
                # identify the tag with the filename
                if name == "href" and value.endswith('.hdf'):
                    
                    # Split the filename into parts
                    # MCD43A4.A2000061.h35v10.006.2016101212455.hdf 

                    fnParts = value.split('.')
                    
                    # Gef product from filename
                    daacid = fnParts[0]
                    
                    # Gef acqusition from filename
                    yyyydoy = fnParts[1][1:8] 
                    
                    # Get tile from filenmae
                    hvtile = fnParts[2]
                    
                    htile = int(hvtile[1:3])
                    
                    vtile = int(hvtile[4:6])
                    
                    # Gef version from filename
                    version = fnParts[3]
                    
                    # Create the tilid
                    tileid = '%(prod)s-%(v)s-%(yyyydoy)s-%(hv)s' %{'prod':daacid,'v':version, 'yyyydoy':yyyydoy,'hv':hvtile }
                    
                    self.queryD[hvtile] = { 'hvtile':hvtile,'htile':htile,'vtile':vtile,
                                           'daacid':daacid, 'version':version, 'filename':value,
                                           'doy':int(yyyydoy[4:7]), 'tileid':tileid }
                                             
class ModisPolarParser(HTMLParser):
    ''' For parsing downloaded index files of MODIS polar online content
    '''
            
    def handle_starttag(self, tag, attrs):
        ''' parse <a> tags to find files for downloading
        '''
        
        if tag == "a":
            
            # Check the list of defined attributes.
            for name, value in attrs:
                
                # identify the tag with the filename
                if name == "href" and value.endswith('.hdf'):
                    
                    # Spelit the filename into parts
                    # MOD29E1D.A2000055.006.2015040211331.hdf
                    fnParts = value.split('.')
                    
                    # Gef product from filename
                    daacid = fnParts[0]
                    
                    # Gef acqusition from filename
                    yyyydoy = fnParts[1][1:8] 
                    
                    # Gef version from filename
                    version = fnParts[2]
                    
                    # Set the query items required for database registering of this product
                    self.queryD['daacid'] = daacid; self.queryD['version'] = version 
                    
                    self.queryD['filename'] = value; self.queryD['doy'] = int(yyyydoy[4:7])
                    
class SmapParser(HTMLParser):
    ''' For parsing downloaded index files of SMAP online content
    '''
            
    def handle_starttag(self, tag, attrs):
        ''' parse <a> tags to find hdf files
        '''

        # Only parse the 'anchor' tag.
        if tag == "a":
            
            # Check the list of defined attributes.
            for name, value in attrs:
   
                if name == "href" and 'SMAP' in value:
                    
                    if value[0:6] == '/SMAP/':
                    
                        source = value.split('/')[2]
                        
                        product,version = source.split('.')
                        
                        self.queryD['daacid'] = product.replace('_','-')
                        
                        self.queryD['version'] = version
                    
                    elif value[0:4] == 'SMAP' and os.path.splitext(value)[1] == '.h5':
                        
                        smapfilename = value
                        
                        fnParts = value.split('_')
                        
                        if len(fnParts) == 8 and '_E_' in smapfilename:
                        
                            sensor, level, type, code, enhanced,  acqdatestr, Rcode, vext = value.split('_')
                        
                        elif len(fnParts) == 7:
                        
                            sensor, level, type, code, acqdatestr, Rcode, vext = value.split('_')
                        
                        else:
                        
                            exit('Error in assets.httpsdataacsess.SmapParser')
                        
                        acqdate = mj_dt.yyyymmddDate(acqdatestr)
                        
                        self.queryD['acqdate'] = acqdate
                                                
                        self.queryD['filename'] = smapfilename
                        
                        self.queryD['doy'] = mj_dt.DateToDOY(acqdate)
                        
class AstgtmParser(HTMLParser):
    ''' For parsing downloaded index files of USGS online content
    '''
            
    def handle_starttag(self, tag, attrs):
        ''' parse <a> tags to find zip files
        '''

        # Only parse the 'anchor' tag.
        if tag == "a":
            
            # Check the list of defined attributes.
            for name, value in attrs:

                
                if value.endswith('.zip'):
                        
                    id = os.path.splitext(value)[0]
                    
                    self.queryD[id] = value
   
class CopernicusDEMParser(HTMLParser):
    ''' For parsing downloaded index files of Copernicus DEM online content
    '''
            
    def handle_starttag(self, tag, attrs):
        ''' parse <a> tags to find zip files
        '''

        # Only parse the 'anchor' tag.
        if tag == "a":
            
            # Check the list of defined attributes.
            for name, value in attrs:

                
                if value.endswith('.zip'):
                        
                    id = os.path.splitext(value)[0]
                    
                    self.queryD[id] = value
                                                        
class SimplComposition:
    '''
    class for simplified compositions
    '''
    
    def __init__(self, compD):  
        for key in compD:
            if '_' in compD[key]:
                exitstr = 'the "%s" parameter can not contain underscore (_): %s ' %(key, compD[key])
                exit(exitstr) 
            setattr(self, key, compD[key])
        if not hasattr(self, 'content'):
            exitstr = 'All compositions must contain a content'
            exit(exitstr)

class ktLayer(LayerCommon):
    '''Class for sentinel tiles'''
    def __init__(self, daacid, composition, locusD, datumD, filepath, FN): 
        """The constructor expects an instance of the composition class."""
        
        LayerCommon.__init__(self)
        
        self.dataid = daacid
        
        self.comp = composition
        
        self.locus = locusD['locus']
        
        self.locuspath = locusD['path']

        self.path = filepath
        
        self.FN = FN

        self.datum = lambda: None
        
        for key, value in datumD.items():
            
            setattr(self.datum, key, value)
            
        if self.datum.acqdate:
            
            self._SetDOY()
            
            self._SetAcqdateDOY()
        
        if self.comp.division == 'tiles':
            
            self._SetTilePath()
            
        else:
            
            self._SetRegionPath()
        
        self._SetQuery()
        
    def _SetTilePath(self):
        """Sets the complete path to region dataset"""
        
        self.FP = os.path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.content, self.locuspath['pstr'], self.locuspath['rstr'], self.datum.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING FPN contains space %s' %(self.FPN)
            exit(exitstr)
        
    def _SetRegionPath(self):
        """Sets the complete path to region dataset"""
        
        self.FP = os.path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.content, self.locuspath, self.datum.acqdatestr)
        self.FPN = os.path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING FPN contains space %s' %(self.FPN)
            exit(exitstr)
            
    def _SetQuery(self):
        '''
        '''
        self.query = {'dataid':self.dataid, 'filename':self.FN,'source':self.comp.source,'product':self.comp.product,
                 'version':self.comp.version,'acqdate':self.datum.acqdate, 'doy':self.datum.doy, 'content':self.comp.content}
      
class FileUtility:  
    ''' Common File utilities for AccessOnlineData
    '''
       
    def __init__(self):
        '''
        ''' 
        pass
    
    def _SetPaths(self,dataset):
        ''' Set local and url paths
        '''
        # Hardcoded product to onlineSource dict  
        self.dataset = dataset
        
        prod2onlineSourceD = {'MOD':'MOST','MYD':'MOSA','SMA':'SMAP', 'SPL':'SMAP', 'MCD':'MOTA', 'TDM':'TDM90',
                              'AST':'ASTER_B/ASTT','CopernicusDem90':'dem/copernicus/outD'}
        
        # Hardcoded product to local Source dict
        prod2localSourceD = {'MOD':'modis','MYD':'modis','SMA':'smap', 'SPL':'smap', 'MCD':'modis', 'TDM':'TDM90',
                             'AST':'aster','CopernicusDem90':'copernicusDEM90'}
        
        cookiefileD = {'MOD':'modis','nsidc_cookies':'modis','nsidc_cookies':'smap', 'SPL':'nsidc_cookies', 'MCD':'nsidc_cookies', 'TDM':'TDM90',
                             'AST':'aster','CopernicusDem90':'copernicusDEM90'}
        
        # get the product, note the conflict between kartturs (hyphen) and some DAAC datanamining convention (underscore)
        self.product = self.pp.process.parameters.product.replace('-','_')
        
        try:
        
            self.source = prod2localSourceD[self.product[0:3]]
            
            self.cookie = cookiefileD[self.product[0:3]]
            
        except:
            
            self.source = prod2localSourceD[self.product]
            
            self.cookie = cookiefileD[self.product]
            
        self.version = self.pp.process.parameters.version
        
        if self.version == "":
            
            self.prodPath = self.product
            
        else:
        
            self.prodPath ='%s.%s' %(self.product,self.version)
        
        '''
        if not self.product[0:3] in prod2onlineSourceD:
            
            exitstr = 'EXITING The product %s is not defined in assets.httpsdataaccess.AccessOnLineData._SetPaths' %(self.product)
        
            exit(exitstr)
        '''
         
        try:   
            
            self.onlineSource = prod2onlineSourceD[self.product[0:3]]
            
        except:
            
            self.onlineSource = prod2onlineSourceD[self.product]
                    
        # Create the localpath where the search data (html) will be saved
        self.localPath = os.path.join('/volumes',self.pp.dstPath.volume,'DOWNLOADS',self.prodPath)
        
        if not os.path.exists(self.localPath):
            
            os.makedirs(self.localPath)
            
        if self.verbose:
            
            infostr = '            Product %s local metadata path: %s' %(self.product,self.localPath)
            
            print (infostr) 
            
    def _AccessUrl(self):   
        ''' Access files to download, and either download or write to script
        '''

        for file in self.downloadL:
            
            # Define the complete url to the online data
            url = os.path.join(self.pp.process.parameters.serverurl,self.onlineSource,self.prodPath,file['datedir'],file['fn'])
            
            home = os.path.expanduser("~")
            
            cookieFPN = os.path.join(home,'.urs_cookies')
            
            cmd = "curl -n -L -c %(c)s -b %(c)s  %(r)s --output %(l)s;" %{'u':self.pp.process.parameters.remoteuser, 'c':cookieFPN, 'r':url, 'l':file['tempFPN']}
            
            cmd = "%(cmd)s mv %(output)s %(dstFPN)s;" %{'cmd':cmd,'output':file['tempFPN'], 'dstFPN':file['dstFPN']}
            
            if self.downloadasscript:
                
                cmdL = cmd.split(';')
                
                for c in cmdL:
                
                    if len(c) > 1:
                    
                        writeln = '%(c)s;\n' %{'c':c}
                        
                        self.downloadScriptF.write(writeln)
                        
            else:
                
                os.system(cmd)
                                
    def _IniFileDownload(self,statusD,region,dateL):
        '''
        '''
        self.downloadL = []
                    
        # If asscript, the whole downloading will be written as a shell script
        if self.downloadasscript:
            
            shFN = 'download_%(prod)s_%(region)s.sh' %{'prod':self.pp.process.parameters.product, 'region':region}
            
            shFP = os.path.join(self.localPath, 'script')
            
            if not os.path.exists(shFP):
            
                os.makedirs(shFP)
            
            self.downloadShFPN = os.path.join(shFP,shFN)
            
            self.downloadScriptF = open(self.downloadShFPN,'w')
           
            cmd = 'mkdir -p %(fp)s;\n' %{'fp':shFP}
            
            self.downloadScriptF.write(cmd)
        
        # Get the files to download
        
        recs = self.session._SelectDaacData(self.pp.srcPeriod, self.pp.process.parameters, statusD,self.pp.procsys.srcsystem)
        
        return [rec for rec in recs if rec[3] in dateL]
        
        #return self.session._SelectDaacData(self.pp.srcPeriod, self.pp.process.parameters, statusD,self.pp.procsys.srcsystem)
      
        '''
        if self.pp.procsys.srcsystem == 'modis':
            
            if self.pp.procsys.srcsystem == 'modis':
                
                return self.session._SelectModisSin(self.pp.srcPeriod, self.pp.process.parameters, statusD)


        if self.pp.procsys.srcsystem == 'modispolar':
            
            if self.pp.procsys.srcsystem == 'ease2n':
                
                return self.session._SelectModisEase2n(self.pp.srcPeriod, self.pp.process.parameters, statusD)
            
            elif self.pp.procsys.srcsystem == 'ease2s':
                
                return self.session._SelectModisEase2s(self.pp.srcPeriod, self.pp.process.parameters, statusD)
        
        elif self.pp.procsys.srcsystem == 'smap':
            
            return self.session._SelectDaacData(self.pp.srcPeriod, self.pp.process.parameters, statusD)
  
        else:
            
            exitstr = 'EXITING - Add system %s for download in assets.AcccessOnlineData._IniFileDownload' %(self.pp.procsys.srcsystem)
            
            exit(exitstr)
        '''
                    
    def _DownloadExtractRegion(self, file, sdpath):
        '''
        '''
        
        def _Extract(layerFile):
            
            if self.pp.srcPath.hdr.lower() == 'hdf':
            
                nrExtracted = self._ExtractH4(layerFile.FPN, self.extractLayerLD, acqdate)
                
            elif self.pp.srcPath.hdr.lower() == 'h5':
            
                nrExtracted = self._ExtractH5(layerFile, self.extractLayerLD, acqdate)
                
            if self.verbose > 2:
                    
                print ('        nrExtracted', nrExtracted, layerFile.FPN)

            if nrExtracted == len(self.extractLayerLD): 
                   
                statusD = {'filename':layerFile.FN,'column':'organized', 'status': 'Y'}
                
                self.session._UpdateDaacStatus(statusD)
                
                statusD = {'filename':layerFile.FN,'column':'exploded', 'status': 'Y'}
                
                self.session._UpdateDaacStatus(statusD)
                
        # Construct the destination path

        filename, daacid, version, acqdate = file
        
        # Set the source daacid.version
        source = daacidVersion = '%s.%s' %(daacid,version)
        
        content = 'original'
        
        layerFile = self._ConstructOrignalLayer(file,source, content, sdpath)
        
        # replace the hyphen to an underscore 
        #source = self.source.replace('-','_')
        
        # Add the layerFile to the db
        self.session._InsertDaacData(layerFile.query)
        
        # Check if the file is stil in the downloadfolder, it so move in place
        
        if os.path.exists( os.path.join(self.localPath,filename) ):
            
            if not layerFile._Exists():
                
                move( os.path.join(self.localPath,filename), layerFile.FPN )
                
                statusD = {'filename': layerFile.FN,'column':'downloaded', 'status': 'Y'}
            
                self.session._UpdateDaacStatus(statusD)
            
            elif os.path.exists(layerFile.FPN):
                
                DUPLICATEFIX
        
        # if the file is already downloaded
        if os.path.exists(layerFile.FPN) and self.extract: 
                        
            _Extract(layerFile)
                
        # Recheck if file exists as it can be deleted if erronous in the _Ecxtract process
        if os.path.exists(layerFile.FPN): 
            
            statusD = {'filename': layerFile.FN,'column':'downloaded', 'status': 'Y'}
            
            self.session._UpdateDaacStatus(statusD)
            
        else: # file is not downloaded
            
            statusD = {'filename': layerFile.FN,'column':'downloaded', 'status': 'N'}
            
            self.session._UpdateDaacStatus(statusD)

            # Create the target directory 
            if not os.path.exists(layerFile.FP):
                
                os.makedirs(layerFile.FP)
                
            # Add the file  to the download list                   
            datedir = mj_dt.DateToStrPointDate(acqdate)
            
            localTempFPN = os.path.join(self.localPath,layerFile.FN)
            
            self.downloadL.append({'query':layerFile.query,'productversion':daacidVersion,'datedir':datedir,'fn':filename,'dstFPN':layerFile.FPN,'tempFPN':localTempFPN})
          
    def _ConstructOrignalLayer(self, file, source, content, sdpath):
        '''
        '''
        
        filename, product, version, acqdate = file

        #construct the composition
        
        compD = {'source':source, 'product':product, 'version':version, 'content':content, 'system':self.pp.procsys.srcsystem, 'division':self.pp.procsys.srcdivision}
        
        #Invoke the composition
        comp = SimplComposition(compD)
        
        #Set the datum
        datumD = {'acqdatestr': mj_dt.DateToStrDate(acqdate), 'acqdate':acqdate}
        
        #Set the filename
        FN = filename
        
        locusD = self.pp.dstLocations.locusD[self.locus]
        '''
        if compD['division'] == 'tiles':
            
        else:
            #Set the locus         
            loc = 'global'
            
            #Set the locuspath
            locusPath = 'global'
        
        #Construct the locus dictionary
        locusD = {'locus':loc, 'path':locusPath}
        '''
        
        #Invoke and return a Layer             
        return ktLayer(product, comp, locusD, datumD, sdpath, FN)
    
    def _ConstructDstLayer(self, layerD, acqdate):
        '''
        '''

        #construct the composition
        
        #compD = {'source':source, 'product':product, 'version':version, 'content':content, 'system':self.pp.procsys.dstsystem, 'division':self.pp.procsys.dstivision}
        
        compD = dict((k, layerD[k]) for k in ('source', 'product', 'content','layerid','prefix','suffix','masked','measure','celltype','dataunit','cellnull','scalefac','offsetadd'))
        
        #Invoke the composition
        #comp = Composition(compD, self.pp.process.parameters, self.pp.procsys.dstsystem, self.pp.procsys.dstdivision, self.pp.dstPath)
        
        comp = Composition(compD, self.pp.process.parameters, layerD['system'], self.pp.procsys.dstdivision, self.pp.dstPath)
  
        
        #Set the datum
        datumD = {'acqdatestr': mj_dt.DateToStrDate(acqdate), 'acqdate':acqdate}
                      
        #Construct the locus dictionary
        locusD = {'locus':layerD['region'], 'path':layerD['region']}
        
        # Create a standard layer
        return Layer(comp, locusD, datumD)

    def _WriteCsvDownload(self,queryD,prodpath):
        '''
        '''
        # Loop over the dates defined in process
        for datum in self.pp.srcPeriod.datumD:
                        
            if datum in ['0',0]:
                
                dateStr = False
                
            else:
                # Convert date to pointed string used on the server
                dateStr = mj_dt.DateToStrPointDate( self.pp.srcPeriod.datumD[datum]['acqdate'] )
            
            # Set the name of the lcal html file that will contain the available data
            csvFN = '%s-%s.csv' %(self.prodPath,dateStr)
            
            # Set the local file name path
            csvFPN = os.path.join(self.localPath,csvFN)
            
            csvF = open(csvFPN,'w')
            
            # Define the complete url to the online data
            urlFP = os.path.join(self.pp.process.parameters.serverurl,self.onlineSource)
            
            if prodpath:
                
                urlFP = os.path.join(urlFP,prodpath)
                
            if dateStr:
                
                urlFP = os.path.join(urlFP,dateStr)
         
            for key in queryD:
                
                url = os.path.join(urlFP,queryD[key])
                
                writestr = '%s\n' %(url)
                
                csvF.write(writestr)
               
            csvF.close()
            
            infostr = "Download %s with aria2 from the terminal with the commands :\n" %(self.prodPath)  
            
            infostr += "cd %s;\n" %(self.localPath) 
            
            infostr += "aria2c -i %s --http-user '%s' --http-passwd '%s'"  %(csvFN, 
                            self.pp.process.parameters.remoteuser,self.pp.process.parameters.password) 
            
            print (infostr)
class AccessTandemX(FileUtility):
    '''
    '''
    
    def __init__(self,pp):
        ''' 
        ''' 
        
        FileUtility.__init__(self)
        
        self.pp = pp
        
        self.verbose = self.pp.process.verbose
        
    def _DowloadProducts(self, dataset):
        '''IMPORTANT the user credentials must be in a hidden file in users home directory called ".netrc"
        '''
        
        # Set the path for this product
        self._SetPaths(dataset)
                            
        # Check the existence of already processed data
        doneFP = os.path.join(self.localPath,'done')
        
        done = True
            
        if not os.path.exists(doneFP):
            
            done = False
            
        # Change to the local directory
        cmd ='cd %s;' %(self.localPath)
        
        os.system(cmd)
        
        # Loop over the hiearchical data structure
        # see
        
        '''
        Hierarchical Directory Structure
    
        The 3 main directories DEM, ANNOTATION and the KMZ contain subdirectories. 
        The first subdirectory level is based on latitudes, one separate directory for 
        each latitude value; each latitude subdirectory is subdivided into further 
        subdirectories for the longitude spaced by 10 degree. Only subdirectories actually 
        containing DEM tiles are visible.
        '''
        
        for lat in range(-90,84,1):
            
            if lat >= 0:
                
                if lat == 0:
                    
                    latdir = 'N00'
                
                if lat > 10:
                    
                    latdir = 'N%(lat)d' %{'lat':lat}
                    
                else:
                    
                    latdir = 'N0%(lat)d' %{'lat':lat}
                    
            else:
                                    
                if lat <10:
                    
                    latdir = 'S%(lat)d' %{'lat':abs(lat)}
                    
                else:
                    
                    latdir = 'S0%(lat)d' %{'lat':abs(lat)}
            
            for lon in range(-180,180,10):
                
                if lon >= 0:
                    
                    if lon == 0:
                        
                        londir = 'E000'
                
                    if lon > 100:
                        
                        londir = 'E%(lon)d' %{'lon':lon}
                        
                    elif lon > 10:
                        
                        londir = 'E0%(lon)d' %{'lon':lon}
                        
                    else:
                        
                        londir = 'E00%(lon)d' %{'lon':lon}
                        
                else:
                                            
                    if lon <-100:
                        
                        londir = 'N%(lon)d' %{'lon':abs(lon)}
                        
                    elif lon < -10:
                        
                        londir = 'N0%(lon)d' %{'lon':abs(lon)}
                
                    else:
                        
                        londir = 'N00%(lon)d' %{'lon':abs(lon)}
                

                #serverulr ='https://download.geoservice.dlr.de/TDM90/files/'
            
                # Set the name of the local html file that will contain the available data
                htmlFN = '%s-%s.html' %(latdir,londir)
                
                # Set the local file name path
                localFPN = os.path.join(self.localPath,htmlFN)
                
                # Define the complete url to the online data
                url = os.path.join(self.pp.process.parameters.serverurl,self.onlineSource,'files',latdir,londir)
                
                url ='https://download.geoservice.dlr.de/TDM90/files/N22/E020/'
    
                print ('url',url)
                
                print (localFPN)
                #https://download.geoservice.dlr.de/TDM90/files/N22/E020/
                
                # If the local destination html file exists and not overwrite, continue
                if os.path.exists(localFPN) and not self.pp.process.overwrite:
                    
                    continue
                
                # It the local destiantion file is int done directorye and not overwrite, continue 
                if done and os.path.exists( os.path.join(doneFP,htmlFN) ) and not self.pp.process.overwrite:
                    
                    continue
                
                # Set a temporary path for index.html 
                indexFPN = os.path.join(self.localPath,'index.html')
                  
                # construct the wget command to retireve the online content as "index.html" - Updated in Feb 2021
                #cmdwget ='%(cmd)s /usr/local/bin/wget -L --load-cookies ~/.tandemx_cookies --save-cookies ~/.tandemx_cookies --auth-no-challenge=on --keep-session-cookies --content-disposition %(url)s' %{'cmd':cmd, 'url':url}
    
                cmdwget ="%(cmd)s /usr/local/bin/wget --auth-no-challenge --user='thomas.gumbricht@gmail.com' password='o5-l4G-67a-tIR' --content-disposition %(url)s" %{'cmd':cmd, 'url':url}


    
                # Execute the wget command
                os.system(cmdwget)
                
                # Rename the retrieved index.html to the designated filename
                cmdmv = 'mv %s %s' %(indexFPN, localFPN)
                
                # Execute the renaming
                os.system(cmdmv)

class AccessCopernicusDEM(FileUtility):
    '''
    '''
    
    def __init__(self,pp):
        ''' 
        ''' 
        
        FileUtility.__init__(self)
        
        self.pp = pp
        
        self.verbose = self.pp.process.verbose
        
    def _SearchOnlineProducts(self, dataset):
        '''IMPORTANT the user credentials must be in a hidden file in users home directory called ".netrc"
        '''
        
        # Set the path for this product
        self._SetPaths(dataset)
        
        # Set todays date 
        #today = mj_dt.Today()
                    
        # Check the existence of already processed data
        doneFP = os.path.join(self.localPath,'done')
        
        done = True
            
        if not os.path.exists(doneFP):
            
            done = False
            
        # Change to the local directory
        cmd ='cd %s;' %(self.localPath)
        
        os.system(cmd)
        
        # Set the name of the local html file that will contain the available data
        htmlFN = 'copernicusDEM90.html' 
  
        # Set the local file name path
        localFPN = os.path.join(self.localPath,htmlFN)
            
        # Define the complete url to the online data
        url = os.path.join(self.pp.process.parameters.serverurl,self.onlineSource)

        # If the local destination html file exists and not overwrite, continue
        if os.path.exists(localFPN) and not self.pp.process.overwrite:
                
            return
            
        # It the local destiantion file is int done directorye and not overwrite, continue 
        if done and os.path.exists( os.path.join(doneFP,htmlFN) ) and not self.pp.process.overwrite:
                
            return
            
        # Set a temporary path for index.html 
        indexFPN = os.path.join(self.localPath,'index.html')
              
        # construct the wget command to retireve the online content as "index.html" - Updated in Feb 2021
        #cmdwget ='%(cmd)s /usr/local/bin/wget -L --load-cookies ~/.nsidc_cookies --save-cookies ~/.nsidc_cookies --auth-no-challenge=on --keep-session-cookies --content-disposition %(url)s' %{'cmd':cmd, 'url':url}

        cmdwget ='%(cmd)s /usr/local/bin/wget -L --load-cookies ~/.%(cookie)s --save-cookies ~/.%(cookie)s --auth-no-challenge=on --keep-session-cookies --content-disposition %(url)s' %{'cmd':cmd, 'url':url,'cookie':self.cookie}

        # Execute the wget command
        os.system(cmdwget)
            
        # Rename the retrieved index.html to the designated filename
        cmdmv = 'mv %s %s' %(indexFPN, localFPN)
            
        # Execute the renaming
        os.system(cmdmv)
        
    def _SearchToListFile(self, dataset):
        '''Load search holdings from _SearchOnlineProducts to local list for download     
        '''
        
        # Set the paths for this  product
        self._SetPaths(dataset)
        
        #Set todays date
        today = mj_dt.Today()
                 
        #Create a sub-folder called done, when the search results are transferred to the db the html will be moved into the done folder
        doneFP = os.path.join(self.localPath,'done')
            
        if not os.path.exists(doneFP):
            
            os.makedirs(doneFP)
               
        # Set the name of the local html file that will contain the available data
        htmlFN = 'copernicusDEM90.html' 
  
        # Set the local file name path
        localFPN = os.path.join(self.localPath,htmlFN)
        

        # Create a sub-folder called done, when the search results are transferred to the db the html will be moved into the done folder
        dstFPN = os.path.join(doneFP,htmlFN)
            
        # If the process parameter searchdone is set to true, move the html file from done to access and read it
        if self.pp.process.parameters.searchdone:
                
            if not os.path.exists(localFPN) and os.path.exists(dstFPN):
                    
                move(dstFPN, localFPN)
                       
        if os.path.exists(localFPN): 
                
            print (self.dataset)
            
            if self.dataset == 'CopernicusDem90': 
                  
                queryD = ReadCopernicusDEMhtml(localFPN)
                
                self._WriteCsvDownload(queryD, False)
                    
            else:
                
                exitstr = 'html parser for dataset %s missing in assets.AccesCopernicusDEM' %(self.dataset)
                
                exit(exitstr)
                
        if os.path.exists(dstFPN) and self.pp.process.overwrite:
            
            os.remove(dstFPN)
         
        if not os.path.exists(dstFPN):      
            
            move(localFPN, dstFPN)
            
        else:
            
            os.remove(localFPN)
        
class AccessOnlineData(FileUtility): 
    ''' class for accessing USGS EOSDIS online data
    '''
    
    def __init__(self):
        ''' 
        ''' 
        
        FileUtility.__init__(self)
           
    def _SearchOnlineProducts(self, dataset):
        '''IMPORTANT the user credentials must be in a hidden file in users home directory called ".netrc"
        '''
        
        # Set the path for this product
        self._SetPaths(dataset)
        
        # Set todays date 
        today = mj_dt.Today()
                    
        # Check the existence of already processed data
        doneFP = os.path.join(self.localPath,'done')
        
        done = True
            
        if not os.path.exists(doneFP):
            
            done = False
            
        # Change to the local directory
        cmd ='cd %s;' %(self.localPath)
        
        os.system(cmd)
        
        # Loop over the dates defined in process
        for datum in self.pp.srcPeriod.datumD:
            
            if self.verbose > 1:
            
                print ('         date:', datum)
                
            
            # Search for the data
            if self.pp.srcPeriod.datumD[datum]['acqdate'] > today:
                
                #skip all dates later than today (there can be no images from the future)
                continue
            

            # Convert date to pointed string used on the server
            dateStr = mj_dt.DateToStrPointDate( self.pp.srcPeriod.datumD[datum]['acqdate'] )
                
            # Set the name of the local html file that will contain the available data
            htmlFN = '%s.html' %(dateStr)
                            
            # Set the local file name path
            localFPN = os.path.join(self.localPath,htmlFN)
            
            # Define the complete url to the online data
            url = os.path.join(self.pp.process.parameters.serverurl,self.onlineSource,self.prodPath,dateStr)

            # If the local destination html file exists and not overwrite, continue
            if os.path.exists(localFPN) and not self.pp.process.overwrite:
                
                continue
            
            # It the local destiantion file is int done directorye and not overwrite, continue 
            if done and os.path.exists( os.path.join(doneFP,htmlFN) ) and not self.pp.process.overwrite:
                
                continue
            
            # Set a temporary path for index.html 
            indexFPN = os.path.join(self.localPath,'index.html')
              
            # construct the wget command to retireve the online content as "index.html" - Updated in Feb 2021
            #cmdwget ='%(cmd)s /usr/local/bin/wget -L --load-cookies ~/.nsidc_cookies --save-cookies ~/.nsidc_cookies --auth-no-challenge=on --keep-session-cookies --content-disposition %(url)s' %{'cmd':cmd, 'url':url}

            cmdwget ='%(cmd)s /usr/local/bin/wget -L --load-cookies ~/.%(cookie)s --save-cookies ~/.%(cookie)s --auth-no-challenge=on --keep-session-cookies --content-disposition %(url)s' %{'cmd':cmd, 'url':url,'cookie':self.cookie}


            # Execute the wget command
            os.system(cmdwget)
            
            # Rename the retrieved index.html to the designated filename
            cmdmv = 'mv %s %s' %(indexFPN, localFPN)
            
            # Execute the renaming
            os.system(cmdmv)
            
    def _SearchToDB(self, dataset):
        '''Load search holdings from _SearchOnlineProducts to local db     
        '''
        
        # Set the paths for this  product
        self._SetPaths(dataset)
        
        #Set todays date
        today = mj_dt.Today()
                 
        #Create a sub-folder called done, when the search results are transferred to the db the html will be moved into the done folder
        doneFP = os.path.join(self.localPath,'done')
            
        if not os.path.exists(doneFP):
            
            os.makedirs(doneFP)
        
        #Loop over the dates
        for datum in self.pp.srcPeriod.datumD:
            
            acqdate = self.pp.srcPeriod.datumD[datum]['acqdate']
            
            if self.pp.srcPeriod.datumD[datum]['acqdate'] > today:
                
                #skip all dates later than today (there can be no images from the future)
                continue
                        
            # Convert date to pointed string used on the server
            dateStr = mj_dt.DateToStrPointDate( self.pp.srcPeriod.datumD[datum]['acqdate'] )
            
            # Set the name of the lcal html file that contains the available data
            htmlFN = '%s.html' %(dateStr)
            
            # Set the local path the th ehtml file
            localFPN = os.path.join(self.localPath,htmlFN)
            
            # Create a sub-folder called done, when the search results are transferred to the db the html will be moved into the done folder
            dstFPN = os.path.join(doneFP,htmlFN)
            
            # If the process parameter searchdone is set to true, move the html file from done to access and read it
            if self.pp.process.parameters.searchdone:
                
                if not os.path.exists(localFPN) and os.path.exists(dstFPN):
                    
                    move(dstFPN, localFPN)
                       
            if os.path.exists(localFPN): 
                
                if self.dataset == 'modisdatapool': 
                  
                    ReadMODIShtml(self.session, localFPN, acqdate)
                
                elif self.dataset == 'modispolar': 
                  
                    ReadMODISPolarhtml(self.session, localFPN, acqdate)
                    
                elif self.dataset == 'smap':
                
                    ReadSMAPhtml(self.session, localFPN, acqdate)
                    
                elif self.dataset == 'ASTGTM':
                
                    queryD = ReadASTGTMhtml(self.session, localFPN, acqdate)
                    
                    self._WriteCsvDownload(queryD, self.prodpath)
                    
                else:
                    
                    exitstr = 'html parser for dataset %s missing in assets.httpdataaccess' %(self.dataset)
                    
                    exit(exitstr)
                    
                if os.path.exists(dstFPN) and self.pp.process.overwrite:
                    
                    os.remove(dstFPN)
                 
                if not os.path.exists(dstFPN):      
                    
                    move(localFPN, dstFPN)
                    
                else:
                    
                    os.remove(localFPN)
                                        
                    
    def _DownloadRegionTileProduct(self, dataset, asscript):
        ''' Download DAAC data products
        '''
        
        # Set the paths for this product
        self._SetPaths(dataset)
        
        if asscript:
            
            scriptScriptFN = 'all-downloads_%(prod)s.sh' %{'prod':self.pp.process.parameters.product}
            
            shFP = os.path.join(self.localPath, 'script')
            
            if not os.path.exists(shFP):
            
                os.makedirs(shFP)
            
            scriptScriptFPN = os.path.join(shFP,scriptScriptFN)
            
            self.scriptScriptF = open(scriptScriptFPN,'w')
            
            self.nMultiTiles = 0
        
        self._DownloadTileProduct(dataset, asscript, True)
        
        if asscript:

            self.scriptScriptF.close()
                        
            infostr = '        Execute all download scripts with the script file:\n    %s' %( scriptScriptFPN )
            
            print (infostr)
            
            infostr = '        Totalnr of downloads: %s' %(self.nMultiTiles)
                
            print (infostr)
              
    def _DownloadTileProduct(self, dataset, asscript, multitiles=False):
        ''' Download DAAC data products
        '''
        
        dateL = [self.pp.srcPeriod.datumD[key]['acqdate'] for key in self.pp.srcPeriod.datumL]
        
        # Only download, no extract
        self.extract = False
        
        # Set downloadasscrip
        # self.downloadasscript = self.pp.process.parameters.asscript
        self.downloadasscript = asscript
        
        # Set the paths for this product
        self._SetPaths(dataset)
                
        statusD = {}
               
        # parameter "searchdone" defaulted to False
        if not self.pp.process.parameters.searchdone:
            
            statusD['downloaded'] = 'N'
            
        for hvtile in self.pp.dstLocations.locusL:
            
            statusD['hvtile'] = hvtile
            
            self.locus = hvtile
            
            tiles = self._IniFileDownload(statusD, hvtile, dateL)
                    
            for tile in tiles:
                                
                self._DownloadExtractRegion(tile, self.pp.dstPath)
                                
            self._AccessUrl()
            
            if self.downloadasscript:
                
                if multitiles:
                    
                    self.nMultiTiles += len(self.downloadL)
                    
                    writestr = '\nchmod 755 %s\n' %(self.downloadShFPN)
                    
                    self.scriptScriptF.write(writestr)
                    
                    self.scriptScriptF.write(self.downloadShFPN)
                
                self.downloadScriptF.close()
                
                if len(self.downloadL) == 0:
                    
                    infostr = '        No files to download for %s' %(self.product)
                    
                else:
                
                    infostr = '        Download %s products for %s with the script file:\n    %s' %(len(self.downloadL), self.product, self.downloadShFPN)
                
                print (infostr)
                                                         
    def _DownLoadProduct(self, dataset, asscript):
        ''' Download DAAC data products
        '''
        
        # Only download, no extract
        self.extract = False
        
        # Set downloadasscrip
        # self.downloadasscript = self.pp.process.parameters.asscript
        self.downloadasscript = asscript
        
        # Set the paths for this product
        self._SetPaths(dataset)
                
        statusD = {}
                
        # parameter "searchdone" defaulted to False
        if not self.pp.process.parameters.searchdone:
            
            statusD['downloaded'] = 'N'
        
        files = self._IniFileDownload(statusD,'global')
        
        for file in files:
            
            self._DownloadExtractRegion(file, self.pp.dstPath) 
                                 
        self._AccessUrl()
        
        if self.downloadasscript:
            
            self.downloadScriptF.close()
            
            if len(self.downloadL) == 0:
                
                infostr = '        No files to download for %s' %(self.product)
                
            else:
            
                infostr = '        Download %s products for %s with the script file:\n    %s' %(len(self.downloadL), self.product, self.downloadShFPN)
            
            print (infostr)
            
    def _ExtractGlobalHdf(self, dataset):
        '''Extract hdf file
        '''
        
        # Set the paths for this  product
        self._SetPaths(dataset)
        
        self.errorFP = os.path.join(self.localPath,'erroneous')
        
        if not os.path.exists(self.errorFP):
            
            os.makedirs(self.errorFP)
            
        # Run _DownLoadProduct to update the db on downloaded data
        
        self._DownLoadProduct(True)
        
        self.extract = True
        
        # Download is force to false when extracting 
        self.downloadasscript = True
        
        shFP = os.path.join(self.localPath, 'script')
                
        if self.pp.process.parameters.asscript:
                
            shFN = 'extract_%(prod)s.sh' %{'prod':self.pp.process.parameters.product}
            
            extractShFPN = os.path.join(shFP,shFN)
            
            self.extractScriptF = open(extractShFPN,'w')
            
        #Get the hdf files to download
        
        statusD = {}
        
        statusD['downloaded'] = 'Y'
        
        if not self.pp.process.overwrite:
            
            statusD['exploded'] = 'N'
            
        files = self._IniFileDownload(statusD,'global')

        #Search template for layers to extract
        #Get the layers to extract for this product + version
        
        self.paramL = ['system', 'region', 'band', 'source', 'product', 'content', 'layerid', 'prefix', 'suffix','masked', 'measure', 'celltype', 'dataunit', 'cellnull', 'scalefac', 'offsetadd', 'region', 'fileext', 'hdffolder', 'hdfgrid', 'timestep','epsg','ulx','uly','lrx','lry']
        
        queryD = {'product': self.pp.process.parameters.product, 'version':self.pp.process.parameters.version, 'retrieve':'Y'}
        
        #extractLayerLD = self.session._SelectTemplateLayersOnProdVer(queryD, self.paramL)
        self.extractLayerLD = self.session._SelectHdfTemplate(queryD, self.paramL)

        if len(self.extractLayerLD) == 0:
            
            exitstr = 'No layers to extract for smap', queryD
            
            exit(exitstr)
            
        # set counter for nr of files to extract
        self.nToExtract = 0

        for file in files:
                        
            self._DownloadExtractRegion(file, self.pp.dstPath)
            
        self._AccessUrl()
        
        self.downloadScriptF.close()
        
        if len(self.downloadL) == 0:
                
            infostr = '        No files to download for %s' %(self.product)
            
        else:
        
            infostr = '        Download %s products for %s with the script file:\n        %s' %(len(self.downloadL), self.product, self.downloadShFPN)
        
        print (infostr)
        
        if self.pp.process.parameters.asscript:
            
            self.extractScriptF.close()
            
            if self.nToExtract == 0:
                
                infostr = '        No files to extract for %s' %(self.product)
            
            else:
            
                infostr = '        Extract %s products for %s with the script file:\n        %s' %(self.nToExtract, self.product, extractShFPN)
            
            print (infostr)
                 
    def _ExtractH4(self, hdfFPN, extractLayerL, acqdate):
        '''
        '''  
        nrExtracted = 0 
        
        for layerD in extractLayerL:
            
            dstLayer = self._ConstructDstLayer(layerD, acqdate)
            
            if not dstLayer._Exists():
                          
                hdffolder = layerD['hdffolder']
                
                hdfgrid = layerD['hdfgrid']
                
                if self.pp.process.parameters.asscript:
                    
                    self.nToExtract +=1
                
                    cmd = 'gdal_translate '
                    
                    cmd = '%(cmd)s -a_srs epsg:%(epsg)s' %{'cmd':cmd,'epsg':layerD['epsg']}
                                        
                    cmd = '%(cmd)s -a_ullr %(ulx)f %(uly)f %(lrx)f %(lry)f' %{'cmd':cmd, 'ulx':layerD['ulx'], 'uly':layerD['uly'], 'lrx':layerD['lrx'], 'lry':layerD['lry']}
                    
                    cmd = '%(cmd)s HDF4_EOS:EOS_GRID:"%(hdf)s":%(folder)s:%(band)s %(dst)s\n' %{'cmd':cmd,'hdf':hdfFPN,'folder':hdffolder,'band':hdfgrid, 'dst':dstLayer.FPN}
        
                    if self.verbose > 1:
                        
                        print (cmd)
                                        
                    self.extractScriptF.write(cmd)
                                            
                else:   
                    
                    pass
                
        return nrExtracted
    
    def _ExtractH5(self, srcLayerFile, extractLayerL, acqdate):
        '''
        '''  
        
        nrExtracted = 0 
        
        for layerD in extractLayerL:
            
            dstLayer = self._ConstructDstLayer(layerD, acqdate)
                        
            if dstLayer._Exists():
  
                nrExtracted += 1
            
            else:
                
                if self.pp.process.parameters.asscript:
                    
                    self.nToExtract += 1
                     
                    cmd = 'gdal_translate -b %(band)s' %{'band':layerD['band']}
                    
                    cmd = '%(cmd)s -a_srs epsg:%(epsg)s' %{'cmd':cmd,'epsg':layerD['epsg']}
                                        
                    cmd = '%(cmd)s -a_ullr %(ulx)f %(uly)f %(lrx)f %(lry)f' %{'cmd':cmd, 'ulx':layerD['ulx'], 'uly':layerD['uly'], 'lrx':layerD['lrx'], 'lry':layerD['lry']}

                    cmd = '%(cmd)s  -a_nodata %(null)d -stats' %{'cmd':cmd, 'null':layerD['cellnull']}
                    
                    cmd = '%(cmd)s HDF5:"%(hdf)s"://%(folder)s/%(grid)s %(dst)s\n' %{'cmd':cmd,'hdf':srcLayerFile.FPN,
                             'folder':layerD['hdffolder'],'grid':layerD['hdfgrid'], 'dst':dstLayer.FPN}
                      
                    if self.verbose > 1:
                        
                        print ('            ',cmd)
                                        
                    self.extractScriptF.write(cmd)
                    
                else:  
                     
                    if self.verbose > 1:
                        
                        infostr = '        Extracting %s to\n            %s' %(srcLayerFile.FPN, dstLayer.FPN)
                        
                        print (infostr)
                        
                    # It is not uncommon that files are corrupted when downloading
                    try:
                        with h5py.File(srcLayerFile.FPN, mode="r") as f:
                            
                            datagrid = '/%(hdffolder)s/%(hdfgrid)s' %{'hdffolder':layerD['hdffolder'],'hdfgrid':layerD['hdfgrid']}
    
                            data = f[datagrid][:]
                            
                            ncols = data.shape[1]
            
                            nrows = data.shape[0]
                            
                            xmin, ymax, xmax, ymin = layerD['ulx'],layerD['uly'],layerD['lrx'],layerD['lry']
                            
                            xres = yres = ((xmax-xmin)/ncols + (ymax-ymin)/nrows)/2
                                   
                            geotransform = (layerD['ulx'], xres, 0, layerD['uly'], 0, -yres)
            
                            # create geotiff
                            driver = gdal.GetDriverByName("Gtiff")
                            
                            if layerD['celltype'].lower() == 'float32':
                                
                                raster = driver.Create(dstLayer.FPN, int(ncols), int(nrows), 1, gdal.GDT_Float32)
                            
                            else:
                                
                                exitstr = 'EXIGING, cellytpe %s missing in assets.httpsdataaccess.AccessOnlineData._ExtractH5' %(layerD['celltype'])
                                
                                exit(exitstr)
                    
                            # set geotransform and projection
                            
                            srs = osr.SpatialReference()
                            
                            srs.ImportFromEPSG(layerD['epsg'])
                            
                            raster.SetGeoTransform(geotransform)
                            
                            raster.SetProjection(srs.ExportToWkt())
                            
                            # write data array to raster
                            data[np.isnan(data)]=layerD['cellnull']
                    
                            raster.GetRasterBand(layerD['band']).WriteArray(data)
                            
                            raster.GetRasterBand(layerD['band']).SetNoDataValue(layerD['cellnull'])
                            
                            raster.FlushCache()
                            
                            raster = None
                            
                    except:
                        
                        errorFPN = os.path.join(self.errorFP, os.path.split(srcLayerFile.FPN)[1])
                        
                        infostr = '    WARNING, hdf5 file error\n        %s' %(srcLayerFile.FPN)
                        
                        print (infostr)
                        
                        infostr = '        moving erronous file to %s' %(errorFPN)
                        
                        print (infostr)
                        
                        # Move the file to the errordirectory               
                        move(srcLayerFile.FPN, errorFPN) 
                                                
        return nrExtracted
    