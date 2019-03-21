#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 14:06:58 2019

@author: juliengautier
"""

from setuptools import setup, find_packages
import visu

setup(name='visu',version=visu.__version__,packages=find_packages(),author='Julien Gautier',author_email='julien.gautier@ensta.fr',
      description='Data visualization',include_package_data=True,package_data={'visu': ['incons/*.*']},
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Free for non-commercial use",
        "Operating System :: OS Independent","Topic :: Scientific/Engineering :: Visualization"],
      long_description=open('README.md').read(),url='https://github.com/julienGautier77/visu')