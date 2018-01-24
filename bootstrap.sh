#!/usr/bin/env bash

# Use single quotes instead of double quotes to make it work with special-character passwords
USERNAME='hbgd'
PASSWORD='123456'
DBNAME='hbgd'

echo "-------------------- updating package lists"
sudo apt-get update
sudo apt-get -y upgrade

echo "-------------------- installing postgres"
sudo apt-get install -y postgresql

POSTGRE_VERSION=9.5

echo "-------------------- configure postgresql.conf to listen for localhost connections"
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/$POSTGRE_VERSION/main/postgresql.conf

# identify users via "md5", rather than "ident", allowing us to make postgres
# users separate from system users. "md5" lets us simply use a password
echo "-------------------- fixing postgres pg_hba.conf file"
echo "host    all             all             0.0.0.0/0               md5" | sudo tee -a /etc/postgresql/$POSTGRE_VERSION/main/pg_hba.conf

sudo service postgresql start

# create new user "$USERNAME" with defined password "$PASSWORD" via postgres user
sudo -u postgres psql -c "CREATE ROLE $USERNAME LOGIN UNENCRYPTED PASSWORD '$PASSWORD' NOSUPERUSER INHERIT CREATEDB NOREPLICATION;"

# create new database "$DBNAME"
sudo -u postgres psql -c "CREATE DATABASE $DBNAME"

sudo service postgresql restart
