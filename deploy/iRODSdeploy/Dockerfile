FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y apt-transport-https telnet wget openssh-client lsb-release

RUN wget -qO - https://packages.irods.org/irods-signing-key.asc | apt-key add - && \
    echo "deb [arch=amd64] https://packages.irods.org/apt/ $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/renci-irods.list && \
    apt-get update && \
    apt-get install -y irods-icommands

# Cleanup
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV IRODS_PASSWD=

COPY docker-entrypoint.sh /
RUN chmod u+x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]

# This sewt of copies allows ROOT to do thew initialization 
COPY ../iRODS/irods_environment.json /
COPY init_irods.py /

EXPOSE 1247
CMD ["ihelp"]

RUN adduser --quiet --disabled-password --shell /bin/bash --home /home/jtilson --gecos "User" jtilson
RUN install -d -m 0755 -o jtilson -g jtilson /home/jtilson/.irods
COPY irods_environment.json /home/jtilson/.irods

# Here the user does the initialization
# NOTE if you change usernames, you must rerun iinit
RUN su - jtilson
COPY init_irods.py /home/jtilson
RUN python /home/jtilson/init_irods.py

