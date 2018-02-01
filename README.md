# HBGDki Study Explorer

# Description
The Study Explorer is a tool that helps you to understand the contents of individual studies contributed to the HBGD knowledge base.

The Study Explorer tool, as known as the Data Store Explorer, presents information about the experimental design of the individual studies, such as whether a study is longitudinal or cross-sectional, interventional, or observational, and the ages, calendar years, and countries of study enrollment. The tool enables you to search for the presence of standardized data fields such as anthropometry measures, biomarkers, microbiology tests, and nutrient intake quantities.

# Setup

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
