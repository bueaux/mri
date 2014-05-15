from setuptools import find_packages
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    version="0.1",
    description="Module for visualising files",
    name="mri",
    author="buo",
    packages=find_packages(),
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension(
    	"mri._entropy", 
    	["src/entropy.pyx"],
    	libraries=["m"])
    ]
)