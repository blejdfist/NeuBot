#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="NeuBot",
    version="0.1b1",
    description="NeuBot IRC Bot",
    author="Jim Persson",
    packages=find_packages(exclude=['*.tests']),
    test_suite='tests',
)
