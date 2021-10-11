#!/usr/bin/env python

#############################################################
#
# Preliminary wrapping methods for managing the iRODS IO
# For ADDA, Reanalysis, and APSVIZ2
#
# Some of this derived from the README.rst for the irods python client github. 
#
# RENCI 2020,2021
#############################################################

import datetime as dt
import numpy as np
import pandas as pd
import sys,os
import yaml
import logging
import json
import ssl

# Keep all the following for future ref. Eg needing to replicate

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

# Part of rodsuser /EDSZone/home/jtilson
#{
#    "irods_host": "irods-eds.edc.renci.org",
#    "irods_port": 1247,
#    "irods_user_name": "jtilson",
#    "irods_zone_name": "EDSZone"
#}

# Using environment files (including any SSL settings) in ~/.irods/

# If gets/puts are taking too long, then either increase this OR open a connection for individual gets/puts
#session.connection_timeout = 300

class irods_utilities:

#TODO what is the right exception to track on?
    def __init__(self, passwd=None, yamlname=None): # Passwd is in the clear so be careful
        """
        Simply grab the named config and passed in passwd to pass 
        to subsequent irods calls
    
        passwd: A string of clear text to use as a password
        """
        if yamlname is None:
            utilities.log.error('No json configuration was provided for iRODS: Abort')
            sys.exit(1)
        if passwd is None:
            utilities.log.error('No passwd was provided for iRODS: Abort')
            sys.exit(1)
        self.config=utilities.load_config(yamlname)
        self.passwd = passwd

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

#TODO what if the subcollection already exists?
    def createSubCollection(self, newcollection='/EDSZone/home/jtilson/testdir'):
        """
        Establish a new subcollection into which a file will be stored
        We expect that the stored file is an aggregate (such as a tar)
        The chosen poath should already have been specified and basedf off the topdir
    
        It is okay to have a recursive request (ie multiple depth path)
        """
        with self._open_connection() as session:
            utilities.log.info('Attempt to create the collection {}'.format(newcollection))
            try: 
                coll = session.collections.create(newcollection)
                utilities.log.info('Created a subcollection with id {} and path {}'.format(coll.id, coll.path))
            except Exception as ex:
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                utilities.log.warn('IRODS subcollection: {}'.format(message))
                #sys.exit(1)
        print(coll.path)
        return coll.path

# irodsdir is only the subdirname
    def getFile(self, irodsdir, inlocaldir, filenames):
        """
        The [dirs] names should be FQ and the Collection must exist 
        """
        utilities.log.debug('Begin subdirectory GET from iRODS at {}'.format(irodsdir))
        options = {kw.FORCE_FLAG_KW: ''}
        num=0
        with self._open_connection() as session:
            for fn in filenames: # Irods filenames are OBJECT. Get string name using .name
                localfile="{0}/{1}".format(inlocaldir,fn)
                irodsfile="{0}/{1}".format(irodsdir,fn)
                #print('Get iRODS file {} to local file {}'.format(irodsfile, localfile))
                session.data_objects.get(irodsfile, localfile, **options )
                num+=1
                utilities.log.debug('Get iRODS file {} to local file {}'.format(irodsfile, localfile))
        return num

#TODO add a FORCE assertion
    def putFile(self, inlocaldir, irodsdir, filenames):
        """
        The dirs names should be FQ and the Collection must be created
        """
        utilities.log.debug('Begin subdirectory PUT to iRODS at {}'.format(irodsdir))
        num=0
        with self._open_connection() as session:
            for fn in filenames:
                #print('final {}, {}, {}'.format(inlocaldir,irodsdir, fn))
                localfile="{0}/{1}".format(inlocaldir,fn)
                irodsfile="{0}/{1}".format(irodsdir,fn)
                session.data_objects.put(localfile, irodsfile )
                num+=1
                utilities.log.debug('Put local file {} to irods file {}'.format(localfile, irodsfile))
        return num

# TODO Fix this uglyness
    def assembleIRODScollectionName(self, root, inlocaldir, irodsbase):
        """ Need to construct an irodsDir that begins at the base and is extended by
            possible extra subdirs
        """
        subdir=root.replace(inlocaldir,'')
        subdir=subdir.replace('/','')
        irodsdir=irodsbase if not subdir else '/'.join([irodsbase,subdir])
        return irodsdir

# TODO Fix this uglyness (again)
    def assembleLocalDirName(self, root, inlocaldir, inirodsdir):
        """ 
        """
        subdir=root.replace(inirodsdir,'')
        subdir=subdir.replace('/','')
        ilocaldir=inlocaldir if not subdir else '/'.join([inlocaldir,subdir])
        return ilocaldir


# TODO fix this later
    def getIRODSdir(self, inirodsdir, subname):
        """
        iRODS walk behaves differently than a typical os.walk. 
        So if the inirodsdir to copy is /EDSZone/home/user/DATA
        and if subname is 'DATA' then return inirodsdir.
        If subdir is something other than DATA ( such as 'MOREDATA'
        then return /EDSZone/home/user/DATA/MOREDATA. 

        """
        tokens = inirodsdir.split('/')
        irodsdir=inirodsdir if tokens[-1]==subname else '/'.join([inirodsdir,subname])
        return irodsdir

    def putDir(self, inlocaldir, inirodsdir):
        """
        We expect input dirs to not have trailing shashes and to point to the 
        topdir of the data sources. Found subdirectories will be build beneath.
        iRODS collections (dirs) will be constructed as needed

        putDir( /home/user/userid_datarun, /EDSZone/home/user/ARBITRARY
        This will create an iRODS tree of:
            /EDSZone/home/user/ARBITRARY/datarun
            /EDSZone/home/user/ARBITRARY/datarun/sub1
            /EDSZone/home/user/ARBITRARY/datarun/sub2
            etc
        """
        num=0
        utilities.log.info('putDir: Local tree {} into iRODS tree {}'.format(inlocaldir, inirodsdir))
        for root, dirnames, filenames in os.walk(inlocaldir):
            irodsdir = self.assembleIRODScollectionName(root, inlocaldir, inirodsdir)
            irodsColl = self.createSubCollection(newcollection=irodsdir)
            num += self.putFile(root, irodsColl, filenames)
        utilities.log.info('Copied a total of {} files to iRODS'.format(num))
        utilities.log.info('Finished copying dir {} to {} '.format(inlocaldir,inirodsdir))
        return num

# iRODS coll.walk() retunrns relative values instead of full values like os.walk() 
# SO for now we must do some silly string manips to get this to work.
    def getDir(self, inirodsdir, inlocaldir):
        """
        Here we take the CONTENTS of inirodsdir inclouding all subdirs and copy them to 
        inlocaldir maintaining the subdir structure
        
        num = irods.getDir(/EDSZone/home/user/ARBITRARY, /home/user/userid_get )
        This will create an local tree of:
            /home/user/userid_get
            /home/user/userid_get/sub1/
            /home/user/userid_get/sub2
            etc
        """
        # Ensure the main dir exists or build it
        # irodsdir = self.createSubCollection(newcollection=inirodsdir)
        # print('irods dir {}'.format(irodsdir))
        num=0
        with self._open_connection() as session:
            print('Open session')
            print(inirodsdir)
            print('get data lists')
            coll = session.collections.get(inirodsdir)
            # Here root is just a single subdir name including the root dir
            # Removed training dir if on the first iteration
            for root, directories, irfilenames in coll.walk(): # roor fromirods is ONLY the subdir name
                filenames=[fn.name for fn in irfilenames] # We want to pass strings to getFile
                rootfull = self.getIRODSdir(inirodsdir,root.name) # If rootname is the final dir in the inirodsdir then return inirdsdir
                localdir=self.assembleLocalDirName(rootfull, inlocaldir, inirodsdir) # '/'.join([inlocaldir,root.name])
                print('make dir {}'.format(localdir))
                os.makedirs(localdir,mode = 0o777, exist_ok = True)
                num+=self.getFile(rootfull, localdir, filenames)
        utilities.log.info('Fetched a total of {} files to local'.format(num))
        utilities.log.info('Finished copying dir {} to {} '.format(inirodsdir, inlocaldir))
        return num

