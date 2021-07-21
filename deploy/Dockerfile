
# Docker file for the creation of the stagedata script
#
# to create image: docker build -t stagedata:latest .
# to push image:
#       docker tag stagedata:latest renciorg/stagedata:latest
#       docker push renciorg/stagedata:latest
##############

FROM thinkwhere/gdal-python

# set the logging level
ENV LOG_LEVEL=10

# get some credit
LABEL maintainer="jtilson@renci.org"

# make a directory for the repos and go there
RUN mkdir /repo
WORKDIR /repo

# INstall iRODS
# RUN apt-get install irods-server irods-database-plugin-postgres

# get the repos
RUN git clone https://github.com/RENCI/APSVIZ_STAGEDATA_IRODS.git

# move to the install directory
WORKDIR /repo/APSVIZ_STAGEDATA_IRODS

# install the pip requirements
RUN pip install -r requirements.txt

##########
# at this point the container is ready to accept the launch command.
# see stagedata_job.yaml for the job that launches this container.
##########
