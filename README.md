# hbgd-data-store-server
[![Build Status](https://travis-ci.com/ContinuumIO/hbgd-data-store-server.svg?token=e99xQta9RGMTxjpudRgm&branch=master)](https://travis-ci.com/ContinuumIO/hbgd-data-store-server)
[![Coverage Status](https://coveralls.io/repos/github/ContinuumIO/hbgd-data-store-server/badge.svg?t=NUhb53)](https://coveralls.io/github/ContinuumIO/hbgd-data-store-server)


A server for deploying the data catalogue

# Running locally
If you've already been through setup once

* T1 - ``$ postgres -D data``
* T2 - ``$ cd hbgd_data_store_server; ./manage.py runserver``

# Running tests
* ``$ ./manage.py test``

# Setup

### Conda environment

```sh
$ conda env create
$ source activate hbgd-data-store-server
```

If you want to install postgres in your conda environment
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
$ cd ..
$ ./manage.py migrate
```

Load the sampledata (optional)
```sh
$ ./manage.py loaddata ../sampledata.json
```

Make a superuser
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
 - the home page http://localhost:8000
 - or admin page localhost:8000/admin
