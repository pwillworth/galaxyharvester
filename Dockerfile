FROM ubuntu:22.04

# install server and app dependencies
RUN apt update
RUN apt install -y apache2 apache2-utils
RUN apt install -y python3 python3-pip
RUN apt clean

# enable CGI mods for apache2 server
RUN a2enmod cgi
RUN a2enmod cgid
COPY .docker/apache2.conf /etc/apache2/apache2.conf
RUN service apache2 restart

# set working directory to apache2 default location
WORKDIR /var/www

# install required python3 libraries
COPY requirements.txt ./requirements.txt
RUN python3 -m pip install -r ./requirements.txt

# copy app files
COPY database ./database
COPY html ./html
COPY scripts ./scripts
COPY *.py ./

# allow temp folder to be written to (blog, etc.)
RUN chmod 777 /var/www/html/temp

# use container name as mysql host
RUN sed -i 's/localhost/galaxyharvester-db/g' ./dbInfo.py

# update base URL for blog to use port 8888
RUN sed -i 's/localhost\/blog.py/localhost:8888\/blog.py/g' ./kukkaisvoima_settings.py

EXPOSE 80
COPY .docker/run.sh ./run.sh
CMD [ "/var/www/run.sh" ]
