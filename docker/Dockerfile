# set the base image
FROM python:3.6

# File Author / Maintainer
MAINTAINER Preva

#add project files to the usr/src/app folder
ADD ../hbgd_data_store_server /srv/app

#set directoty where CMD will execute
WORKDIR /srv/app
#COPY requirements.txt ./

# Get pip to download and install requirements:
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install gunicorn

# Expose ports
EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=hbgd_data_store_server.settings SECRET_KEY=foobarbaz

# default command to execute
CMD exec gunicorn ../hbgd_data_store_server.wsgi:application --bind 0.0.0.0:8000 --workers 3
