.. role:: bash(code)
   :language: bash


Setup Instruction
=================

Run development server
----------------------

If you've already been through setup once:

* :bash:`$ postgres -D data`
* :bash:`$ cd hbgd_data_store_server; ./manage.py runserver`


Developer Setup
---------------

Conda environment
+++++++++++++++++

.. code:: bash

  $ conda env create
  $ source activate hbgd-data-store-server

If you want to install postgres in your conda environment

.. code:: bash

   $ conda install postgresql
   $ mkdir data
   $ initdb -D data
   # Launch postgres
   $ postgres -D data
   # In a new terminal
   $ createuser -s hbgd --pwprompt --createdb --no-superuser --no-createrole
   # setup a password for the user
   $ createdb -U hbgd --locale=en_US.utf-8 -E utf-8 -O hbgd hbgd -T template0

Alternatively, you can use vagrant on your development machine (available via
brew cask install vagrant). Then run the command:

.. code:: bash

	$ vagrant up

This creates a development database with the user/password of hbgd/123456. You
may change this inside of bootstrap.sh.

Django
++++++

Setup your environment variables
********************************

.. code:: bash

	export DEBUG=True
	export DB_PASSWORD='your db password'
	export MY_SECRET_KEY='your secret key'

Migrate the database
********************

.. code:: bash

	$ cd ..
	$ ./manage.py migrate

.. _create_superuser:

Define a superuser
******************

.. code:: bash

	$ ./manage.py createsuperuser

Assets
++++++

* Install compass :bash:`gem install compass`
* Use compass to build css from scss
* Edit scss not stylesheets directory
* Check in built css.

Run it
++++++

.. code:: bash

	$ ./manage.py runserver

Now go to:
 - the home page http://localhost:8000
 - or admin page localhost:8000/admin


Running tests
+++++++++++++

* :bash:`$ ./manage.py test --driver Firefox -v`
