=========
AWS Setup
=========

Register for an AWS account and pick a default region keeping note of it.

Setup a security key
++++++++++++++++++++

In order to work with AWS you will have to create some IAM credentials, which will give you
an "Access Key ID" and "Secret Access Key" by following the instructions at `Managing AWS Access Keys
<https://docs.aws.amazon.com/general/latest/gr/managing-aws-access-keys.html>`_.
Make sure to keep note of these credentials.


Setup an EC2 Key
++++++++++++++++

1. Navigate to the EC2 page on the AWS console.
2. Select Key pairs in Network & Security in the panel on the left.
3. Select **Create Key Pair**.
4. Give the key pair a name.
5. Once you click Create it will download a .pem file containing your credentials (**make sure to keep this**).


Setup an Elastic Beanstalk App
++++++++++++++++++++++++++++++

#. Go to the Elastic Beanstalk page on the AWS console.
#. Select **Create New Application** on the top-right.
#. Application Information:
    #. Give your application a name, e.g. ``study-explorer``.
#. New environment:
    #. Click Next and select the type of environment by clicking on **Create web server**.
#. Environment type:
	#. Select the Environment type, by selecting **Python** from the Predefined configuration dropdown. For now just leave **Single Instance** selected in the Environment Type dropdown (load balancing can be enabled later).
#. Application Version:
	#. Set up the initial application version by leaving **Sample Application** selected and clicking Next, we will deploy the actual Django App at a later stage.
#. Environment Information:
	#. Enter an Environment name and Environment URL, e.g., ``studyExplorer-env``.
#. Additional Resources:
	#. Add a database instance to the environment by enabling the **Create an RDS DB instance with this environment** option.
#. Configuration Details:
	#. Configure the size of the instance (start with a ``t2.xlarge``) and select the EC2 key pair we created earlier.
#. Environment Tags:
	#. Set up the required environment variables. These variables can be changed later in the Elastic Beanstalk console.

	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+
	| Key                    | Value                                                              | Required | Description                                                                                                  |
	+========================+====================================================================+==========+==============================================================================================================+
	| SECRET_KEY             | <generate this...>                                                 | Yes      | Declares the Django SECRET_KEY                                                                               |
	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+
	| DJANGO_SETTINGS_MODULE | hbgd_data_store_server.settings                                    | Yes      | Declares the settings module of the Django App.                                                              |
	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+
	| ALLOWED_HOSTS          | .studyexplorer.io,studyexplorer-env.us-west-2.elasticbeanstalk.com | Yes      | Comma separated list of domains to allow.                                                                    |
	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+
	| ADMINS                 | <admin names and emails>                                           | No       | Name and email for admins. Formatted in: "First1 Last1:admin1@my-app.com,First2 Last2:admin2@my-app.com"     |
	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+
	| EMAIL_ADDRESS          | <Gmail email address...>                                           | No       | Allows declaring an email to send server errors to. This must be a Gmail address.                            |
	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+
	| EMAIL_PASSWORD         | <Gmail password...>                                                | No       | Password for EMAIL_ADDRESS                                                                                   |
	+------------------------+--------------------------------------------------------------------+----------+--------------------------------------------------------------------------------------------------------------+

#. RDS Configuration:
	#. Configure the database, selecting ``Postgres`` as the DB engine and at minimum ``9.5.4`` as the DB engine version. Then declare a database superuser by setting a Username and Password. Start with a ``db.m3.large`` Instance class (can be scaled up and down later).
#. Permissions:
	#. Leave permissions set up as is and click Next.
#. Review:
	#. Review all the settings and click Launch.


Setup the EB CLI
++++++++++++++++

The simplest way to deploy an app to Elastic Beanstalk is to use their supplied command line interface (CLI).

1. Follow the `install instructions <https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html>`_. to download and install the EB CLI
2. Follow the `configuration instructions <https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-configuration.html>`_. to configure the EB CLI with your AWS account and access keys.
3. Now modify the ``hbgd_data_store_server/.elasticbeanstalk/.config.yaml`` in the ``hbgd-data-store-server`` repository to match the app and environment we set up above. 
4. Check that everything is set up correctly by running ``eb status`` in the ``hbgd_data_store_server`` directory of the repository.
5. Now you are ready to deploy the app.
6. Follow the deployment instructions to deploy the app.


SSH into the application and load the environment
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: bash

	$ eb ssh
	[ec2-user@...]$ source /opt/python/run/venv/bin/activate
	[ec2-user@...]$ source /opt/python/current/env
	[ec2-user@...]$ cd /opt/python/current/app/

Create a super user on the deployed Elastic Beanstalk application
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: bash

	[ec2-user@...]$ ./manage.py createsuperuser

Import the Domain Data
++++++++++++++++++++++

.. code:: bash

	[ec2-user@...]$ cat data/sql/001_import_studies_domain.sql | ./manage.py dbshell

Load the studies CSV file
+++++++++++++++++++++++++

1. From the admin console (http://www.studyexplorer.io/admin) click the "IMPORT STUDIES" button.
2. Click the "Choose File" button and select the ``data/csv/studyinfo.csv`` file.
3. This step might take a few minutes to complete. Do NOT close your browser window until this completes.


Import the default study configuration
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code:: bash

	[ec2-user@...]$ cat data/sql/002_update_studies_studyfield.sql | ./manage.py dbshell
	[ec2-user@...]$ cat data/sql/003_import_studies_filter.sql | ./manage.py dbshell


Load the IDX CSV files
+++++++++++++++++++++++++

1. From the admin console (http://www.studyexplorer.io/admin) click the "IMPORT IDX FILES" button.
2. Click the "Choose File" button and select the `data/csv/idx.zip` file.
3. This step might take a few minutes to complete. Do NOT close your browser window until this completes.