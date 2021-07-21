#!/usr/bin/env python

# Simply perform the iinit on a fixed iRODS account
# The provided password must correspond to the user in the irods json file
# This only needs to be run ONCE to build a local encrypted passwd file 
#

import os, sys
from utilities.utilities import utilities as utilities

print('Attempt to initialize iRODS')

passwd = os.getenv('IRODS_PASSWD', 'jlt!1s0n2')
cmd='iinit '+passwd
os.system(cmd)

print('Attempt to perform a simple ils')
os.system('ils')

print('Attempt to perform a simple iget')
os.system('iget README')

print('Finished')
