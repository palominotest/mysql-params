#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
setup(
    name='mysql-params',
    version='0.1b.dev',
    author='PalominoDB',
    author_email='oss@palominodb.com',
    packages=find_packages(),
    #data_files=[('docs', ['docs/args.sample.txt', 'docs/config_sample.yml', 'docs/logging.sample.cnf'])],
    url="http://pypi.python.org/pypi/mysql-params",
    license='GPLv2',
    description='Utility for tracking MySQL patterns',
    #install_requires=[
    #    'MySQL-python>=1.2',
    #    'argparse>=1.2',
    #],
#Django==1.5.1
#MySQL-python==1.2.4
#-e hg+https://bitbucket.org/andrewgodwin/south@bcaf2b10bc3dbad570169754cb0eaeab1f637909#egg=South-dev
#argparse==1.2.1
#-e git+https://github.com/rbondoc-palominodb/boto.git@68365dafdeb88f4f4aab06bf6f4e8f11064f169f#egg=boto-dev
#-e git+https://github.com/bradjasper/django-jsonfield.git@49e00d20c6ee9f10e14286e8d709b25f271d008f#egg=jsonfield-dev
#texttable==0.8.1
#colorama==0.2.5
#paramiko==1.10.1
#hurry.filesize==0.9
    install_requires=[
        'Django>=1.5.1',
        'MySQL-python>=1.2.4',
        #'South==dev',
        'South>=0.8.1',
        'argparse>=1.2.1',
        #'boto==dev',
        'boto>=2.9.9',
        #'jsonfield==dev',
        'jsonfield>=0.9.18',
        'texttable==0.8.1',
        'colorama>=0.2.5',
        'paramiko>=1.10.1',
        'hurry.filesize>=0.9'
    ],
    #dependency_links=[
    #    'hg+https://bitbucket.org/andrewgodwin/south@bcaf2b10bc3dbad570169754cb0eaeab1f637909#egg=South-dev',
    #    'git+https://github.com/rbondoc-palominodb/boto.git@68365dafdeb88f4f4aab06bf6f4e8f11064f169f#egg=boto-dev',
    #    'git+https://github.com/bradjasper/django-jsonfield.git@49e00d20c6ee9f10e14286e8d709b25f271d008f#egg=jsonfield-dev'
    #],
    #entry_points={
    #    'console_scripts': [
    #        'pdb_check_maxvalue = int_overflow_check.pdb_check_maxvalue:main',
    #    ]
    #}
)
