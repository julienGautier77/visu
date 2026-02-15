#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 14:06:58 2019
open('README.md').read()
'PyQt6-sip== 13.5.2','PyQt6-qt6==6.5.1','PyQt6==6.5.1',
install_requires=['matplotlib','PyQt6-sip== 13.5.2','PyQt6-qt6==6.5.1','PyQt6==6.5.1','qdarkstyle','pyqtgraph','scipy','six','zmq',])
@author: juliengautier
"""

import re
from pathlib import Path
from setuptools import setup, find_packages

This_directory = Path(__file__).parent
long_description = (This_directory / "README.md").read_text()


def get_version():
    """Lit la version depuis visu/__init__.py"""
    init_file = This_directory / "visu" / "__init__.py"
    content = init_file.read_text(encoding='utf-8')
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    if match:
        return match.group(1)
    raise RuntimeError("Version non trouvée dans visu/__init__.py")


setup(
    name='visu',
    version=get_version(),
    packages=find_packages(),
    author='Julien Gautier',
    author_email='julien.gautier@ensta.fr',
    description='Data visualization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    package_data={'visu': ['icons/*.*']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Free for non-commercial use",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Visualization"
    ],
    url='https://github.com/julienGautier77/visu',
    install_requires=[
        'matplotlib',
        'PyQt6',
        'qdarkstyle',
        'pyqtgraph',
        'scipy',
        'six',
        'pyzmq',
    ],
)
