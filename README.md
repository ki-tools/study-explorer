# HBGDki Study Explorer

# Description
The Study Explorer is a tool that helps you to understand the contents of individual studies contributed to the HBGD knowledge base.

The Study Explorer tool, as known as the Data Store Explorer, presents information about the experimental design of the individual studies, such as whether a study is longitudinal or cross-sectional, interventional, or observational, and the ages, calendar years, and countries of study enrollment. The tool enables you to search for the presence of standardized data fields such as anthropometry measures, biomarkers, microbiology tests, and nutrient intake quantities.

## Instructions for installing with Docker

### Quickstart - Locally

The simplest way to evaluate StudyExplorer is to use docker-compose

    # download https://raw.githubusercontent.com/HBGDki/study-explorer/master/docker-compose.yml
    curl -O https://raw.githubusercontent.com/HBGDki/study-explorer/master/docker-compose.yml
    # or, alternatively, wget https://raw.githubusercontent.com/HBGDki/study-explorer/master/docker-compose.yml
    # or git clone https://github.com/HBGDki/study-explorer.git && cd study-explorer

Start studyexplorer and a database server with docker-compose up

    docker-compose up -d

Initialize various settings including database migrations, usernames, passwords and then populate the data.

    # Initialize database
    docker-compose exec web /usr/local/bin/python manage.py migrate
    docker-compose exec web /usr/local/bin/python manage.py createsuperuser --username admin --email aelgert@prevagroup.com
    psql -h localhost -U postgres postgres -f hbgd_data_store_server/data/sql/000_reset_db.sql
    psql -h localhost -U postgres postgres -f hbgd_data_store_server/data/sql/001_import_studies_domain.sql
    docker-compose exec web /usr/local/bin/python manage.py load_studies data/csv/studyinfo.csv
    psql -h localhost -U postgres postgres -f hbgd_data_store_server/data/sql/002_update_studies_studyfield.sql
    docker-compose exec web /usr/local/bin/python manage.py load_idx data/csv/idx.zip
    psql -h localhost -U postgres postgres -f hbgd_data_store_server/data/sql/003_import_studies_filter.sql

Navigate to http://localhost:8000 and you will see the study explorer application running.

Note that this is best for development, testing and demonstrations from a local machine.

### Run StudyExplorer Docker container directly

Pull from Docker Hub & Run

    docker pull prevagroup/studyexplorer.io
    docker run -it -p 8000:8000 -e SECRET_KEY=foobar prevagroup/studyexplorer.io

Note that the application is running, but will be unable to connect to a database. If you pass in the following environment vars corresponding to a valid postgres server that the docker container can access, you can connect to a database. However, please note that a Docker container is set up in a private network bridged to the host machine, so you may have to do some digging to find the correct IP address for connections.

* RDS_PORT
* RDS_DB_NAME
* RDS_USERNAME
* RDS_PASSWORD
* RDS_HOSTNAME

To run in a production environment, either consult your cloud hosting provider's documentation for installing an application from a Docker image, or set up a server running docker and mapping the host's port 80 to the docker container's port 8000 (you will need admin/root privileges).

# Setup (Legacy)

### Conda environment

```sh
$ conda env create
$ source activate hbgd-data-store-server
```

If you want to install postgres in your conda environment:
```sh
$ conda install postgresql
$ mkdir data
$ initdb -D data
# Launch postgres
$ postgres -D data
# In a new terminal
$ createuser -s hbgd --pwprompt --createdb --no-superuser --no-createrole
# setup a password for the user
$ createdb -U hbgd --locale=en_US.utf-8 -E utf-8 -O hbgd hbgd -T template0
```

Alternatively, you can use vagrant on your development machine (available via
brew cask install vagrant). Then run the command:

```sh
$ vagrant up
```

This creates a development database with the user/password of hbgd/123456. You
may change this inside of bootstrap.sh.

### Django

Setup your environment variables:
```sh
export DEBUG=True
export DB_PASSWORD='your db password'
export MY_SECRET_KEY='your secret key'
```

Migrate the database:

```sh
$ ./manage.py migrate
```

Load the sample data (optional):
```sh
$ ./manage.py loaddata ../sampledata.json
```

Make a superuser:
```
$ ./manage.py createsuperuser
```

### Assets

* Install compass  ``gem install compass``
* Use compass to build css from scss
* Edit scss not stylesheets directory
* Check in built css.

### Run it

```sh
$ ./manage.py runserver
```

Now go to:
 - Home page http://localhost:8000
 - Admin page http://localhost:8000/admin
 - User & Developer Documentation http://localhost:8000/docs

# Running locally
If you've already been through setup once:

```sh
$ postgres -D data
$ cd hbgd_data_store_server; ./manage.py runserver
```

# Running tests
```sh
$ ./manage.py test
```
