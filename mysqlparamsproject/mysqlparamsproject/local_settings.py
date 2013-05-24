DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'param_tracker',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': 'root',
        'PASSWORD': 'rodxavierbondoc',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

AWS_ACCESS_KEY_ID = 'AKIAINZOEB745CTTKS5A'
AWS_SECRET_ACCESS_KEY = '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'

AWS_REGIONS = (
    'us-east-1',
)

AWS_DB_INSTANCES = {
    'us-east-1': (
        {
            'name': 'rbondoc-test',
            'password': 'rodxavierbondoc'
        },
    ),
}
