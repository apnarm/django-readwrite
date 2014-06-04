#!/usr/bin/env python

from setuptools import setup

setup(
    name='django-readwrite',
    version='0.0.1',
    description='Read/write database splitting for Django, based on the HTTP request method.',
    author='Raymond Butcher',
    author_email='randomy@gmail.com',
    url='https://github.com/apn-online/django-readwrite',
    license='MIT',
    packages=(
        'django_readwrite',
    ),
    install_requires=(
        'django',
    ),
)
