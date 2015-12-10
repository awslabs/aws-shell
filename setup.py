#!/usr/bin/env python
import re
import ast

from setuptools import setup, find_packages


requires = [
    'awscli>=1.8.9,<2.0.0',
    'prompt-toolkit==0.50',
    'boto3>=1.2.1',
]


with open('awsshell/__init__.py', 'r') as f:
    version = str(
        ast.literal_eval(
            re.search(
                r'__version__\s+=\s+(.*)',
                f.read()).group(1)))


setup(
    name='aws-shell',
    version=version,
    description='AWS Shell',
    long_description=open('README.rst').read(),
    author='James Saryerwinnie',
    url='https://github.com/jamesls/aws-shell',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    package_data={'awsshell': ['data/*/*.json']},
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'aws-shell = awsshell:main',
            'aws-shell-mkindex = awsshell.makeindex:main',
        ]
    },
    license="Apache License 2.0",
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ),
)
