Deployment
==========

Deployment Steps
----------------

User-facing deploy:
+++++++++++++++++++

* Take snapshot of current data
* We create a new server
* Deploy the app with a helpful name
* Check it's running
* Swap the urls
* Destroy the old server

Create a Snapshot:
++++++++++++++++++

* Go to running beta env
* Configuration
* RDS Database
* Click View in RDS Console link
* Instance Actions - Take Snapshot

Create a new server:
++++++++++++++++++++

* Actions: Create New Environment: Create Web Server
* Select Saved configuration (currently beta_server_20170216_conf)
* Pick latest approprate existing application version (should be same as currently deployed on main url)
* Pick a new environment name e.g. studyExplorer-env-TMP
* Set environment url to studyExplorer-env-tmp
* Add billingProject and Owner tags under Environment Tags
* In RDS Configuration pick snapshot
* Enter user / pass
* Click Launch

Deploy the app:
+++++++++++++++

* Note down name of newly created environment e.g. studyExplorer-env-TMP
* In hbgd_data_store_server directory clean out all non-git files:

.. code:: bash

	$ git clean -xfdi .

* Collect static: ./manage.py collectstatic

.. code:: bash

	$ ./manage.py collectstatic

* Build the documentation

.. code:: bash

	$ pushd ./docs
	$ make html
	$ popd

* Deploy app to CORRECT ENV WITH LABEL. Label should be beta_commitID:

.. code:: bash

	$ eb deploy studyExplorer-env-TMP -l beta_459d32a

Check it's running:
+++++++++++++++++++
* Go to tmp url: http://studyExplorer-env-tmp.us-west-2.elasticbeanstalk.com/
* Check all new features are running as expected

Swap the URLs:
++++++++++++++
* Actions Swap URLs
* After a couple of minutes confirm that all new features are on main url: http://studyExplorer-env.us-west-2.elasticbeanstalk.com/

Destroy the server:
+++++++++++++++++++
* Actions: Terminate Environment
* To do a dev deploy, it doesn't matter if we trash the server temporarily. Follow "Deploy the app" steps. MAKE SURE THAT YOU DEPLOY TO THE CORRECT ENVIRONMENT. Still pick a helpful label like master_a2291d4