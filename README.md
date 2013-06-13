# mysql-params

Utility for tracking mysql parameters

## Contents
1. Overview
2. Getting Started
3. Settings
4. Usage
5. Web GUI

## Overview

Mysql-params is a tool for tracking MySQL Parameters. Currently, the tool can collect parameters from four sources:

- Amazon RDS Parameter Group
- Amazon RDS DB Instance
- Non-RDS host my.cnf file
- Non-RDS DB Instance

## Getting Started
1. Setup pip, virtualenv and virtualenvwrapper. Refer to this guide(https://github.com/palominodb/PalominoDB-Public-Code-Repository/blob/master/doc/python_tools_installation_guide.txt) on how to setup these tools.

2. Create a virtual environment

        mkvirtualenv param_tracker
        
    For succeeding uses, you can activate the virtual environment by:
    
        workon param_tracker

3. Install the requirements

        cd <path/to/mysql-params>
        pip install -r requirements.txt

4. Create a database to use

        mysql -u <user> -p
        mysql> CREATE DATABASE param_tracker;

5. Configure local_settings.py. Mysql-params related settings are discussed thoroughly on the next section.

        cp local_settings.py.template local_settings.py
        # Make necessary changes

6. Run syncdb

        ./manage.py syncdb

7. Run migrations

        ./manage.py migrate

## Settings

1. Databases - database to be used by Mysql-params. Note that the name should be the name of the database you created.

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql', 
                'NAME': 'param_tracker',
                'USER': 'mysql_user',
                'PASSWORD': 'password',
                'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
                'PORT': '',                      # Set to empty string for default.
            }
        }

2. DEFAULT_FROM_EMAIL - email address where emails will be sent from

        DEFAULT_FROM_EMAIL = 'email@palominodb.com'

3. EMAIL_BACKEND - email backend to use. Currently supports smtp and sendmail backends. To use, uncomment the one that will be used and comment out the other.

        #EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        EMAIL_BACKEND = 'rds.backends.sendmail.EmailBackend'

4. SMTP email backend settings - settings used when the SMTP email backend is used

        EMAIL_HOST = 'smtp.gmail.com'
        EMAIL_HOST_PASSWORD = 'password'
        EMAIL_HOST_USER = 'example@gmail.com'
        EMAIL_PORT = 587
        EMAIL_SUBJECT_PREFIX = '[MySQL Parameter Tracker]'
        EMAIL_USE_TLS = True

5. Sendmail email backend settings - settings used when the sendmail email backend is used

        SENDMAIL_PATH = '/usr/sbin/sendmail'

6. AWS credentials - settings for giving Mysql-params access to AWS API.

        AWS_ACCESS_KEY_ID = ''
        AWS_SECRET_ACCESS_KEY = ''

7. AWS_REGIONS - A tuple of AWS regions where data will be collected

        AWS_REGIONS = (
            'us-east-1',
            #'eu-west-1',
            #'us-west-1',
            #'us-west-2',
            #'sa-east-1',
            #'ap-northeast-1',
            #'ap-southeast-1',
            #'ap-southeast-2'
        )

8. MySQL Credentials - MySQL username and password to connect to all db instances

        MYSQL_USER = ''
        MYSQL_PASSWORD = ''

9. NON_RDS_HOSTS - A tuple of dictionaries containing the keys; hostname, ssh_user, identity_file and mysql_port. The hostname, ssh_user and identity_file keys are used for accessing the my.cnf file over sftp. Moreover, the identity_file should be an absolute path.

        NON_RDS_HOSTS = (
            {
                'hostname': '',
                'ssh_user': '',
                'identity_file': '',
                'mysql_port': 3306,   # If no port is given, default will be 3306
            },
        )

10. MYSQL_CNF_FILE_PATH - Absolute path to the my.cnf file

        MYSQL_CNF_FILE_PATH = '/etc/mysql/my.cnf'

##Usage
1. param-collect - This is responsible for parameter collection
    
        Usage: ./manage.py param-collect [options] 

        Options:
          --stat=STAT           Collect a single <statistic>. See --list-stats for
                                available statistics.
          --list-stats          List available statistics.
          -h, --help            show this help message and exit
          
    Example Usage:
    
        ./manage.py param-collect

2. param-report - This is responsible for reporting change summaries

        Usage: ./manage.py param-report [options] 

        Options:
          --stat=STAT           Report a single <statistic>. See --list-stats for
                                available statistics.
          --list-stats          List available statistics.
          -o OUTPUT, --output=OUTPUT
                                Specifies an output formatter. One of: email, text, nagios
          -s SINCE, --since=SINCE
                                Where <since> is something like: last(since the last
                                collector run), 4h(4 hours), 1d(1 day), 1w(1 week)
          -h, --help            show this help message and exit
          
    Example Usage:
    
        # Report change summary for the last 24 hours.
        ./manage.py param-report --since 24h
        
        # Send email report
        ./manage.py param-report --since 24h -o email
        
        # Nagios output mode
        # Ignores the --since parameter.
        # This will return the Nagios exit code 1(Warning) if any DB instance needs to be restarted. Otherwise, returns 0(Ok).
        ./manage.py param-report -o nagios

3. param-check - This sends an email alert for the previous data collection. This command sends a detailed report about the last data collection. This sends new, deleted and changed objects. For changed objects, this command includes what parameters were changed. Moreover, this also sends which db instances needs to be restarted.

    Example Usage:
    
        ./manage.py param-check
        
4. param-compare - This compares parameter groups, db instances or config files.
    
        Usage: ./manage.py param-compare [options] 

        Options:
          --stat=STAT           Statistic to compare. See --list-stats for available
                                statistics.(Default: parameter_group)
          --list-stats          List available statistics.
          -n NAMES, --names=NAMES
                                A comma-separated string containing parameter group/db
                                instance names. If only one name is passed, previous
                                version will be used for comparison.
          -e ENGINE, --engine=ENGINE
                                MySQL Engine used for comparison for default values.
                                One of: mysql5.1, mysql5.5
          -h, --help            show this help message and exit

    Example Usage:
        
        # Compare parameter groups using default engine mysql5.5
        ./manage.py param-compare --names 'pg1,pg2'
        
        # Compare parameter groups using default engine mysql5.1
        ./manage.py param-compare --names 'pg1,pg2'
        
        # Compare db instances
        ./manage.py param-compare --names 'dbi1,dbi2' --stat db_instance
        
        # Compare config files
        ./manage.py param-compare --names 'cf1,cf2' --stat config_file
        
## Web GUI
To run the gui, execute the command below. Moreover, you can use apache or nginx to serve the project through an actual web server.
    
    ./manage.py runserver
