#!/usr/bin/env python

#############################################################
#
# Preliminary wrapping methods for managing the iRODS IO
# In this version, we reestablish a connecvtionm for each irods
# call. 
#
# RENCI 2020
#############################################################

import datetime as dt
import numpy as np
import pandas as pd
import sys,os
from utilities.irods_utilities import irods_utilities

# Part of rodsuser /EDSZone/home/jtilson
#{
#    "irods_host": "irods-eds.edc.renci.org",
#    "irods_port": 1247,
#    "irods_user_name": "jtilson",
#    "irods_zone_name": "EDSZone"
#}

# Using environment files (including any SSL settings) in ~/.irods/
# Use this one as it 

# Initiate - give it a reral password

def main(args):

    irods = irods_utilities(args.passwd)

    # Print out some collection details
    irods.queryUsersAndGroups()

    # Get topdir
    topdir = irods.findTopdir()

    ## PUT a file into a new subcollection
    print('TEST a put')
    newdir='/'.join([topdir,'test1','test2'])
    # Push a single file to the new subcollection
    localfilename='TEST1234_archive.tar.gz'
    #localfilename='maxwvel.63.10.10.mbtiles'
    localdir='/projects/sequence_analysis/vol1/prediction_work/DATA_APSVIZ_STAGEDATA_IRODS/irods/DATA'
    irods.putFile(localdir, localfilename, newdir, localfilename)

    ## GET back a single file into a (potentially) diff filename
    print('TEST a get')
    irodsdir='/'.join([topdir,'test1','test2'])
    irodsfilename='TEST1234_archive.tar.gz'
    localdir='.'
    localfilename='reread.tar.gz'
    irods.getFile(irodsdir, irodsfilename, localdir, localfilename)

    ## Can we put an entire directory. No According to Terrell we will need to walk the directory
    print('TEST a flat directory PUT')
    #Local dir. A previously downloaded namforecast
    #localdir='/projects/sequence_analysis/vol1/prediction_work/APSVIZ_STAGEDATA_IRODS/irods/DATA/namforecast'
    localdir='/projects/sequence_analysis/vol1/prediction_work/DATA_APSVIZ_STAGEDATA_IRODS/irods/DATA/namforecast'
    irodsdir=irodsdir='/'.join([topdir,'test1','flatnamforecast'])    
    irods.putFlatDir(localdir, irodsdir)

    ## Can we put an entire directory. No According to Terrell we will need to walk the directory
    print('TEST a hierarchical directory PUT')
    #localdir='/projects/sequence_analysis/vol1/prediction_work/APSVIZ_STAGEDATA_IRODS/irods'
    localdir='/projects/sequence_analysis/vol1/prediction_work/DATA_APSVIZ_STAGEDATA_IRODS/irods'
    irodsdir=irodsdir='/'.join([topdir,'test1','HIERTEST'])
    print(localdir)
    print(irodsdir)
    irods.putDir(localdir, irodsdir)

if __name__ == '__main__':
    from argparse import ArgumentParser
    import sys
    parser = ArgumentParser()
    parser.add_argument('--passwd', action='store', dest='passwd', default=None,
                        help='Service account tester')
    args = parser.parse_args()
    sys.exit(main(args))
