# HBGDki Study Explorer

# Description

The Study Explorer is a tool that helps you to understand the contents of individual studies contributed to the HBGD
knowledge base.

The Study Explorer tool, as known as the Data Store Explorer, presents information about the experimental design of the
individual studies, such as whether a study is longitudinal or cross-sectional, interventional, or observational, and
the ages, calendar years, and countries of study enrollment. The tool enables you to search for the presence of
standardized data fields such as anthropometry measures, biomarkers, microbiology tests, and nutrient intake quantities.

## Instructions for installing with Docker

### Quickstart - Locally

The simplest way to evaluate StudyExplorer is to use docker-compose

    # download https://raw.githubusercontent.com/HBGDki/study-explorer/master/docker/docker-compose.yml
    curl -O https://raw.githubusercontent.com/HBGDki/study-explorer/master/docker/docker-compose.yml
    # or, alternatively, wget https://raw.githubusercontent.com/HBGDki/study-explorer/master/docker/docker-compose.yml
    # or git clone https://github.com/HBGDki/study-explorer.git && cd study-explorer

Start studyexplorer and a database server with docker-compose up

    docker-compose up -d

Initialize various settings including database migrations, usernames, passwords and then populate the data.

    # Initialize database
    docker-compose exec web /usr/local/bin/python manage.py migrate
    docker-compose exec web /usr/local/bin/python manage.py createsuperuser --username admin --email you@yourdomain.com
    psql -h localhost -U postgres postgres -f data/sql/000_reset_db.sql
    psql -h localhost -U postgres postgres -f data/sql/001_import_studies_domain.sql
    docker-compose exec web /usr/local/bin/python manage.py load_studies data/csv/studyinfo.csv
    psql -h localhost -U postgres postgres -f data/sql/002_update_studies_studyfield.sql
    docker-compose exec web /usr/local/bin/python manage.py load_idx data/csv/idx.zip
    psql -h localhost -U postgres postgres -f data/sql/003_import_studies_filter.sql

Navigate to http://localhost:8000 and you will see the study explorer application running.

Note that this is best for development, testing and demonstrations from a local machine.

### Run StudyExplorer Docker container directly

Pull from Docker Hub & Run

    docker pull prevagroup/studyexplorer.io
    docker run -it -p 8000:8000 -e SECRET_KEY=foobar prevagroup/studyexplorer.io

Note that the application is running, but will be unable to connect to a database. If you pass in the following
environment vars corresponding to a valid postgres server that the docker container can access, you can connect to a
database. However, please note that a Docker container is set up in a private network bridged to the host machine, so
you may have to do some digging to find the correct IP address for connections.

* RDS_PORT
* RDS_DB_NAME
* RDS_USERNAME
* RDS_PASSWORD
* RDS_HOSTNAME

OR

* DATABASE_URL (`postgres://{user}:{password}@{hostname}:{port}`)

To run in a production environment, either consult your cloud hosting provider's documentation for installing an
application from a Docker image, or set up a server running docker and mapping the host's port 80 to the docker
container's port 8000 (you will need admin/root privileges).

# Development Setup

Python Version: 3.7.16

- Create or have a Postgresql instance running and accessible.
- Create virtual environment: `make venv` or `python3.7 -m venv .venv`
- Activate virtual environment: `source .venv/bin/activate`
- Install packages: `make pip_install` or `pip install -r requirements.txt` and `pip install -r requirements-dev.txt`

Setup your environment variables:

```sh
export DEBUG=True
export DB_PASSWORD='your db password'
export SECRET_KEY='your secret key'
```

Create the database:
`createdb --locale=en_US.utf-8 -E utf-8 -O hbgd hbgd -T template0`

Migrate the database:
`make migrate`

Create a super user:
`make createsuperuser`

Load Test Data:

```shell
psql -h localhost hbgd -f data/sql/000_reset_db.sql
psql -h localhost hbgd -f data/sql/001_import_studies_domain.sql
python manage.py load_studies data/csv/studyinfo.csv
psql -h localhost hbgd -f data/sql/002_update_studies_studyfield.sql
python manage.py load_idx data/csv/idx.zip
psql -h localhost hbgd -f data/sql/003_import_studies_filter.sql
```

## Running locally

If you've already been through setup once:

```sh
$ make devserve
```

Now go to:

- Home page http://localhost:8000
- Admin page http://localhost:8000/admin
- User & Developer Documentation http://localhost:8000/docs

## Migrations

Locally: `make migrate`

On Dokku Server: `dokku run se-<name> make migrate` (e.g., `dokku run se-staging make migrate`)

## Documentation

Generate the docs: `make docs`

## Running tests

```shell
make test
```

# Dokku Hosting

## Server Configuration

- Increase nginx timeout. Update `/etc/nginx/conf.d/dokku.conf` add the following lines:

```text
proxy_connect_timeout   3600;
proxy_send_timeout      3600;
proxy_read_timeout      3600;
```

- Restart nginx: `sudo systemctl restart nginx`


- Install the Lets Encrypt Plugin: `sudo dokku plugin:install https://github.com/dokku/dokku-letsencrypt.git`
- Globally set the Lets Encrypt email address: `dokku config:set --global DOKKU_LETSENCRYPT_EMAIL=your@email.tld`
- Schedule cron job to auto update SSL certificates: `dokku letsencrypt:cron-job --add`

## Create New App Instance

Execute these commands on the Dokku server:

- Create the app: `dokku apps:create se-<name>` (e.g., `dokku apps:create se-www`)
- Create the database: `dokku postgres:create se-<name>-db`
- Link the database to the app: `dokku postgres:link se-<name>-db se-<name>`
- Set the ENV
  variables: `dokku config:set se-<name> WEB_CONCURRENCY=4 ALLOWED_HOSTS=".kiglobalhealth.org,.hbgdki.org,.studyexplorer.io" SECRET_KEY="<your-secret-key> GTM_CONTAINER_ID=<your-google-tag-container-id>"`
- Set the Buildpack:
    - `dokku config:set se-<name> BUILDPACK_URL=https://github.com/ki-tools/heroku-buildpack-python-3.7.17.git`
- Set the domain: `dokku domains:add se-<name> <name>.studyexplorer.io`
- Set the nginx read timeout:: `dokku nginx:set se-<name> proxy-read-timeout 30m`
- Import the database export: `dokku postgres:import se-<name>-db < se-<name>.dump`
- Install the SSL Certificates: `dokku letsencrypt se-<name>`

Execute these commands on your local system:

- Add git remotes: `git remote add se-<name> dokku@dokku.studyexplorer.io:se-<name>`
- Add your SSH key: `ssh-add -k ~/.ssh/dokku-study-explorer.pem`

## Deployment

- `git push se-<name> master` (e.g., `git push se-staging master`)

Or via Make:

- `make deploy <name>` (e.g., `make deploy staging`)

To deploy your currently checked out branch:

- `make deploy_current_branch <name>` (e.g., `make deploy_current_branch staging`)

---

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

Alternatively, you can use vagrant on your development machine (available via brew cask install vagrant). Then run the
command:

```sh
$ vagrant up
```

This creates a development database with the user/password of hbgd/123456. You may change this inside of bootstrap.sh.

### Django

Setup your environment variables:

```sh
export DEBUG=True
export DB_PASSWORD='your db password'
export SECRET_KEY='your secret key'
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
