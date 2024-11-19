FROM python:3.9

ENV WORKDIR /opt
# prequisite --- install python requests module
COPY requirements.txt ${WORKDIR}/
RUN pip3 install -r /opt/requirements.txt

# copy python and bash wrapper
COPY *py ${WORKDIR}/
##  COPY *sh ${WORKDIR}/

### add some dev tools
RUN apt-get update -y && \
    apt-get install -y emacs screen