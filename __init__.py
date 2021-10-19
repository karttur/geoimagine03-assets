"""
assets
==========================================

Package belonging to Karttur´s GeoImagine Framework.

Author
------
Thomas Gumbricht (thomas.gumbricht@karttur.com)

"""

from .version import __version__, VERSION, metadataD

from .httpsdataaccess import AccessOnlineData

from geoimagine.assets.hdf_2_geotiff import ProjEASEgridHdf

__all__ = ['ProcessAncillary']