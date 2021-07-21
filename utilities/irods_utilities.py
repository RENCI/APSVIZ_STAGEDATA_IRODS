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
import yaml
import logging
import json
import ssl
from utilities.utilities import utilities
from argparse import ArgumentParser
from irods.session import iRODSSession
from irods.meta import iRODSMeta
from irods.meta import iRODSMeta, AVUOperation
from irods.models import Collection, DataObject
from irods.query import SpecificQuery
from pprint import pprint
from irods.models import User, UserGroup
from irods.user import iRODSUser, iRODSUserGroup
import irods.keywords as kw
# import utilities.irods_utilities as irods
# from utilities.irods_utilities import irods_utilities

# Part of rodsuser /EDSZone/home/jtilson
#{
#    "irods_host": "irods-eds.edc.renci.org",
#    "irods_port": 1247,
#    "irods_user_name": "jtilson",
#    "irods_zone_name": "EDSZone"
#}

# Using environment files (including any SSL settings) in ~/.irods/
# Use this one as it 

#session.connection_timeout = 300

class irods_utilities:

#TODO what is the right exception to track on?
    def __init__(self, passwd, yamlname='./config/irods_environment.json', config=None): # Passwd is in the clear so be careful
        """
        Simply grab the available config and passed in passwd to pass 
        to subsequent irods calls
    
        passwd: A string of clear text to use as a password
        yamlname: Json full path to irods_environment.json. Defaults to a file in our usual config location
        config. A dict of the irods irods_environment.json infomration
        """
        if config is not None:
            self.config = config
            utilities.log.info('Processed passed dict data {}'.format(self.config))
        else:
            try:
                env_file = os.environ['IRODS_ENVIRONMENT_FILE']
                utilities.log.info('Found ENV for irods config at {}'.format(env_file))
            except Exception as ex:
                #env_file = os.path.expanduser('~/.irods/irods_environment.json')
                #env_file = os.path.expanduser('./config/irods_environment.json')
                env_file = os.path.expanduser(yamlname)
                utilities.log.info('Found passed file for irods config at {}'.format(env_file))
            self.config = utilities.load_config(env_file)
        self.passwd = passwd
        utilities.log.info('Found passwd and stored it')

    def  _open_connection(self):
        """
        Since connection timeout are generally in the hundreds of seconds
        Let's not simply force themn to stayt open for a long time and reconnect whenever
        we need to
        """
        ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None)
        ssl_settings = {'ssl_context': ssl_context}
        try:
            session =iRODSSession(host=self.config['irods_host'], port=self.config['irods_port'],
                user=self.config['irods_user_name'], password=self.passwd, zone=self.config['irods_zone_name'],**ssl_settings)
            utilities.log.info('Opened an irods connection')
        except Exception as ex:
            utilities.log.info('Could not start a connection to irods config at {}'.format(config))
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            utilities.log.info('IRODS open: {}'.format(message))
            sys.exit(1)
        return session

    def queryUsersAndGroups(self):
        """
        Simple printout of selected data from the main iRODS collection
        """
        with self._open_connection() as session:
            #List Users
            pprint(list( [ (x[User.id], x[User.name]) for x in session.query(User) ] ))
            # List groups
            groups = session.query(User).filter( User.type == 'rodsgroup' )
            [x[User.name] for x in groups]
            #More detailed listings
            grp_usr_mapping = [ (iRODSUserGroup ( session.user_groups, result), iRODSUser (session.users, result)) \
                     for result in session.query(UserGroup,User) ]
            pprint( [ (x,y) for x,y in grp_usr_mapping if x.id != y.id ] )

    def findTopdir(self):
        """
        Find the top collection (root dir) from which all data will be saved
        """
        #session = self._open_connection()
        with self._open_connection() as session:
            topCollection="/{0.zone}/home/{0.username}".format(session)
        coll = session.collections.get(topCollection)
        print('Top Collection is {} {}'.format(coll.id,coll.path))
        return coll.path

#TODO what is the subcollection already exists?
    def createSubCollection(self, newcollection='/EDSZone/home/jtilson/testdir'):
        """
        Establish a new subcollection into which a file will be stored
        We expect that the stored file is an aggregate (such as a tar)
        The chosen poath should already have been specified and basedf off the topdir
    
        It is okay to have a recursive request (ie multiple depth path)
        """
        with self._open_connection() as session:
            try: 
                coll = session.collections.create(newcollection)
                utilities.log.info('Created a subcollection with id {} and path {}'.format(coll.id, coll.path))
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                utilities.log.warn('IRODS subcollection: {}'.format(message))
        #        # sys.exit(1)
        print(coll.path)
        return coll.path

    def getFile(self, inirodsdir, irodsfilename, inlocaldir, localfilename):
        """
        The path must be full and can be generated, in part, as:
        logical_path = "/{0.zone}/home/{0.username}/{1}".format(session,filename)
        As a GET, the collection must already exist
        """
        localfile="{0}/{1}".format(inlocaldir,localfilename)
        irodsfile="{0}/{1}".format(inirodsdir,irodsfilename)
        options = {kw.FORCE_FLAG_KW: ''}
        with self._open_connection() as session:
            session.data_objects.get( irodsfile, localfile, **options )
        utilities.log.info('Grabbed irods file {}'.format(irodsfilename))

#TODO add a FORCE assertion
    def putFile(self, inlocaldir, localfilename, inirodsdir, irodsfilename):
        """
        The path must be full and can be generated, in part, as:
        logical_path = "/{0.zone}/home/{0.username}/{1}".format(session,filename)
        iRodsdirs (collections) will be created here if needed
        """
        #logical_path='/'.join([collection,filename])
        print('start put')
        irodsdir=self.createSubCollection(newcollection=inirodsdir)
        localfile="{0}/{1}".format(inlocaldir,localfilename)
        irodsfile="{0}/{1}".format(irodsdir,irodsfilename)
        print('local {} irods {}'.format(localfile, irodsfile))
        with self._open_connection() as session:
            session.data_objects.put(localfile, irodsfile )
        utilities.log.info('Put irods file {}'.format(localfilename))
        

#TODO de-clumsify
# Putting a whole directory 
# NOTE: No subdirectories are expected and so are not properly handled here
# localdir='/projects/sequence_analysis/vol1/prediction_work/APSVIZ_STAGEDATA_IRODS/irods'
# irodsdirname is the TARGET collection name
    def putFlatDir(self, inlocaldir, inirodsdir):
        """
        This version requires localdir to be only of one level
        """
        # Ensure the main dir exists or build it
        irodsdir = self.createSubCollection(newcollection=inirodsdir)
        print('irods dir {}'.format(irodsdir))
        for root, directories, filenames in os.walk(inlocaldir):
            if len(directories) is not 0:
                utilities.log.warn('Local directory structure is not flat. That is a req')
                sys.exit(1)
            print(len(directories))
            for filename in filenames:
                print('xxxxxxxx')
                print( filename)
                #Then move to irods using this
                self.putFile(inlocaldir, filename, irodsdir, filename) 
        utilities.log.info('Finished copying dir {} to {} '.format(inlocaldir,inirodsdir))

# TODO revisit the construction of the iRODS target directory. Eg currently if 
#      inlocaldir is /home/user/data with subdirs of a,b, and c then if the irods
#      rootdir is /EDZone/irods/rootdir, then the fginal filenames will be:
#      /EDZone/irods/rootdir/data/a
#      /EDZone/irods/rootdir/data/b
#      /EDZone/irods/rootdir/data/c
    def putDir(self, inlocaldir, inirodsdir):
        """
        This version is being constructed to handle arbitrary depths
        """
        # Ensure the main dir exists or build it
        # irodsdir = self.createSubCollection(newcollection=inirodsdir)
        # print('irods dir {}'.format(irodsdir))
        for dirpath, dirnames, filenames in os.walk(inlocaldir):
            for filename in filenames:
                # Build and create the irods final file name
                localdir=os.path.join(os.path.abspath(dirpath))
                irodsdir="{0}/{1}".format(inirodsdir,os.path.join(os.path.relpath(dirpath,'')))
                #print('final {}, {}, {}, {}'.format(localdir, filename, irodsdir, filename))
                self.putFile(localdir, filename, irodsdir, filename)
        utilities.log.info('Finished copying dir {} to {} '.format(inlocaldir,inirodsdir))




