#!/usr/bin/env python-sirius

"""Setup for install/uninstall Pynel package."""

 

from setuptools import setup

import os

# import pkg_resources

 

 

# def get_abs_path(relative):

#     return pkg_resources.resource_filename(__name__, relative)

version_path = os.path.join(os.path.dirname(__file__), "VERSION")

 

# with open(get_abs_path("README.md"), "r") as _f:

#     _long_description = _f.read().strip()

 

with open(version_path, "r") as _f:

    __version__ = _f.read().strip()

 

# with open(get_abs_path("requirements.txt"), "r") as _f:

#     _requirements = _f.read().strip().split("\n")

 

setup(

    name="touschek_pack",

    version=__version__,

    author="Thales Quadros",

    author_email="thales.bastos@lnls.br",

    description="touschek_pack is a package to study and get the most critical loss rate by touschek scattering",

    # long_description=_long_description,

    # long_description_content_type="text/markdown",

    url="",

    download_url="",

    license="MIT License",

    classifiers=[

        "Intended Audience :: Science/Research",

        "Programming Language :: Python",

        "Topic :: Scientific/Engineering",

    ],

    packages=["touschek_pack"],

    package_data={'touschek_pack': ['VERSION']},

    # include_package_data=True,

    # install_requires=_requirements,

    # test_suite="tests",

    python_requires=">=3.4",

    zip_safe=False,

)