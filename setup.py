# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='sipgateio-sendfax-python',
    version='0.1.0',
    description='A demonstration on how to send a fax using the sipgate REST API',
    long_description=readme,
    author='sipgate',
    author_email='',
    url='https://github.com/sipgate-io/sipgateio-sendfax-python',
    license=license,
    packages=find_packages(exclude=())
)
