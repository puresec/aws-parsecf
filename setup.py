#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='aws-parsecf',
    version='1.0.0',
    description="Parse AWS CloudFormation's intrinsic functions in the template",
    long_description=open('README.rst').read(),
    author='Oded Niv',
    url='https://github.com/puresec/aws-parsecf',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'PyYAML',
        'boto3',
    ],
    setup_requires=['nose', 'coverage'],
)

