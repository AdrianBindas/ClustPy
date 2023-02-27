from setuptools import setup, find_packages, Extension
import clustpy
import numpy as np


def _load_requirements():
    with open("requirements.txt", "r") as file:
        requirements = [line.rstrip() for line in file]
    return requirements


def _load_readme():
    with open("README.md", "r") as file:
        readme = file.read()
    return readme


dip_extension = Extension('clustpy.utils.dipModule',
                          include_dirs=[np.get_include()],
                          sources=['clustpy/utils/dip.c'])

setup(
    name='clustpy',
    version=clustpy.__version__,
    packages=find_packages(),
    package_data={'clustpy': ['data/datasets/*.data']},
    url='https://github.com/collinleiber/ClustPy',
    license='BSD-3-Clause License',
    author='Collin Leiber',
    author_email='leiber@dbs.ifi.lmu.de',
    description='Clustering in python',
    long_description=_load_readme(),
    long_description_content_type="text/markdown",
    python_requires='>=3.7',
    install_requires=[_load_requirements()],
    ext_modules=[dip_extension]
)
