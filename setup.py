#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 14:06:58 2019

@author: juliengautier
"""

from setuptools import setup, find_packages
import visu

setup(name='visu',version=visu.__version__,author='Julien Gautier',author_email='julien.gautier@ensta.fr',description='Data visualization',
      long_description=open('README.md').read(),python_requires='<4')