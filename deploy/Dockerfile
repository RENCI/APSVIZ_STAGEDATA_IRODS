
# Docker file for the creation of the stagedata script
#
# to create image: docker build -t stagedata:latest .
# to push image:
#       docker tag stagedata:latest renciorg/stagedata:latest
#       docker push renciorg/stagedata:latest
##############

FROM continuumio/miniconda3

# set the logging level
ENV LOG_LEVEL=10

# get some credit
LABEL maintainer="jtilson@renci.org"

# make a directory for the repos and go there
RUN mkdir /repo
WORKDIR /repo

# make sure the container is up-to-date
RUN apt-get update

# Start off getting Python 3.7.3
RUN conda install  -y python=3.7.3

# update conda and set the download channel
RUN conda update conda && \
    conda config --add channels conda-forge

# tell conda what the shell is
RUN conda init bash

# get the repos
RUN git clone https://github.com/RENCI/APSVIZ_STAGEDATA_IRODS.git

# move to the install directory
WORKDIR APSVIZ_STAGEDATA_IRODS/deploy

# install the conda requirements
RUN conda install --yes --file conda_requirements.txt

# move to the install directory
WORKDIR /repo/APSVIZ_STAGEDATA_IRODS

# set the python path
ENV PYTHONPATH=/repo/APSVIZ_STAGEDATA_IRODS

# set the location of the output directory
ENV RUNTIMEDIR=/data

##########
# at this point the container is ready to accept the launch command.
# see stagedata_job.yaml for the job that launches this container.
##########
