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
import time as tm

from utilities.utilities import utilities
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
    """
    cmd line passwd takes precedence. If none, the ENV variable IRODSPASSWORD is checked.
    if none, exit with failure status.
    """
    if args.passwd is not None:
        passwd = args.passwd
        utilities.log.info('Grabbed password from the cmd line')
    elif os.getenv('IRODSPASSWORD') is not None:
        passwd = os.getenv('IRODSPASSWORD')
        utilities.log.info('Grabbed password from the env: IRODSPASSWORD')
    else:
        utilities.log.error('No IRODS password was supplied: Abort')
        sys.exit(1)

    #Override defaults for finding the appropriatre json config
    if os.getenv('IRODS_ENVIRONMENT_FILE') is not None:
        irodsjson=os.getenv('IRODS_ENVIRONMENT_FILE')

    irodsjson=os.getenv('IRODS_ENVIRONMENT_FILE') if os.getenv('IRODS_ENVIRONMENT_FILE') is not None else './config/irods_environment.json'
    irodsjson='./config/irods_environment.json'

    utilities.log.info('iRODS config name to use is {}'.format(irodsjson))

# os.path.expanduser(yamlname)
    irods = irods_utilities(passwd, yamlname=irodsjson)

    # Print out some collection details
    irods.queryUsersAndGroups()

    # Get topdir
    topdir = irods.findTopdir()

    ## PUT a files into a new subcollection
    utilities.log.info('TEST a put')
    newirodsdir='/'.join([topdir,'TESTS','test1'])
    # Push a single file to the new subcollection
    localfilename=['TEST1234_archive.tar.gz']
    localdir='./DATA/SIMPLE'
    irodsColl = irods.createSubCollection(newcollection=newirodsdir) # If by-passing the putDir you must ensure the collection is created
    num = irods.putFile(localdir, newirodsdir, localfilename)
    utilities.log.info('Put {} files into irods coll {}'.format(num,newirodsdir))

    # GET back a files from q collection into a (potentially) diff filename 
    utilities.log.info('TEST a get')
    irodsdir='/'.join([topdir,'TESTS','test1'])
    irodsfilename=['TEST1234_archive.tar.gz']
    localdir='./SCRATCH/TEST'
    os.makedirs(localdir,mode = 0o777, exist_ok = True) # Again if by-passing the getDir do this specifically 
    num = irods.getFile(irodsdir, localdir, localfilename)
    utilities.log.info('Get {} files into localdir {}'.format(num,localdir))

    # Put an entire local tree to irods
    utilities.log.info('Test a tree copy to irods')
    localdir='./DATA/OBSMOD-TEST'
    # The following will create depth as needed sort of like mkdir -p
    irodsdir='/'.join([topdir,'TESTS','test2'])
    t1=tm.time()
    num = irods.putDir(localdir, irodsdir)
    utilities.log.info('Put {} files into irods coll at {}'.format(num,irodsdir))
    utilities.log.info('Put dir time is {}'.format(tm.time()-t1))

    # Get an entire tree from irods to a local dir
    utilities.log.info('Test a tree get from irods to local FS')
    t1=tm.time()
    outlocaldir='./SCRATCH/TEST2'
    inirodsdir='/'.join([topdir,'TESTS','test2'])
    num = irods.getDir(inirodsdir, outlocaldir )
    utilities.log.info('Get {} files from irods coll to {}'.format(num,outlocaldir))
    utilities.log.info('Put dir time is {}'.format(tm.time()-t1))

if __name__ == '__main__':
    from argparse import ArgumentParser
    import sys
    parser = ArgumentParser()
    parser.add_argument('--passwd', action='store', dest='passwd', default=None,
                        help='Service account tester')
    args = parser.parse_args()
    sys.exit(main(args))
