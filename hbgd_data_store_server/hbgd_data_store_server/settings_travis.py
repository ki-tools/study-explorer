from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'hbgd_data_store_server',
        'USER': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
        }
}
