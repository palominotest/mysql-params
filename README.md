#mysql-params

Utility for tracking mysql parameters

##Setup
1. Create virtualenv

        mkvirtualenv param_tracker

2. Install requirements

        pip install -r requirements.txt

3. Create Database

        Create database param_tracker;

4. Configure local_settings.py.

        cp local_settings.py.template local_settings.py
        # Make necessary changes

5. Run syncdb

        ./manage.py syncdb

6. Run migrations

        ./manage.py migrate

##Usage
1. param-collect - This is responsible for stat collection
    
        Usage: ./manage.py param-collect [options] 

        Options:
          -v VERBOSITY, --verbosity=VERBOSITY
                                Verbosity level; 0=minimal output, 1=normal output,
                                2=verbose output, 3=very verbose output
          --settings=SETTINGS   The Python path to a settings module, e.g.
                                "myproject.settings.main". If this isn't provided, the
                                DJANGO_SETTINGS_MODULE environment variable will be
                                used.
          --pythonpath=PYTHONPATH
                                A directory to add to the Python path, e.g.
                                "/home/djangoprojects/myproject".
          --traceback           Print traceback on exception
          --stat=STAT           Collect a single <statistic>. See --list-stats for
                                available statistics.
          --list-stats          List available statistics.
          --version             show program's version number and exit
          -h, --help            show this help message and exit
          
    Example Usage:
    
        ./manage.py param-collect

2. param-report - This is responsible for reporting change summaries

        Usage: ./manage.py param-report [options] 

        Options:
          -v VERBOSITY, --verbosity=VERBOSITY
                                Verbosity level; 0=minimal output, 1=normal output,
                                2=verbose output, 3=very verbose output
          --settings=SETTINGS   The Python path to a settings module, e.g.
                                "myproject.settings.main". If this isn't provided, the
                                DJANGO_SETTINGS_MODULE environment variable will be
                                used.
          --pythonpath=PYTHONPATH
                                A directory to add to the Python path, e.g.
                                "/home/djangoprojects/myproject".
          --traceback           Print traceback on exception
          --stat=STAT           Report a single <statistic>. See --list-stats for
                                available statistics.
          --list-stats          List available statistics.
          -o OUTPUT, --output=OUTPUT
                                Specifies an output formatter. One of: email, text
          -s SINCE, --since=SINCE
                                Where <since> is something like: last(since the last
                                collector run), 4h(4 hours), 1d(1 day), 1w(1 week)
          --version             show program's version number and exit
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

3. param-check - Sends email alert for the previous data collection

    Example Usage:
    
        ./manage.py param-check
        
4. param-compare - Compare parameter groups or db instances
    
        Usage: ./manage.py param-compare [options] 

        Options:
          -v VERBOSITY, --verbosity=VERBOSITY
                                Verbosity level; 0=minimal output, 1=normal output,
                                2=verbose output, 3=very verbose output
          --settings=SETTINGS   The Python path to a settings module, e.g.
                                "myproject.settings.main". If this isn't provided, the
                                DJANGO_SETTINGS_MODULE environment variable will be
                                used.
          --pythonpath=PYTHONPATH
                                A directory to add to the Python path, e.g.
                                "/home/djangoprojects/myproject".
          --traceback           Print traceback on exception
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
          --version             show program's version number and exit
          -h, --help            show this help message and exit

    Example Usage:
        
        # Compare parameter groups using default engine mysql5.5
        ./manage.py param-compare --names 'pg1,pg2'
        
        # Compare parameter groups using default engine mysql5.1
        ./manage.py param-compare --names 'pg1,pg2'
        
        # Compare db instances
        ./manage.py param-compare --names 'dbi1,dbi2' --stat db_instance
        
##Web GUI
To run the gui, execute the command below.
    
    ./manage.py runserver
