#import shlex
#import sys

from setuptools import setup, find_packages
#from setuptools.command.test import test as TestCommand


setup(name='logwiz',
      version='0.0.1',
      author='fram',
      author_email='pavel.sht(gav-gav-gav)yandex.ru',
      packages=find_packages(),
      scripts=['logwiz/scripts/log_analyzer.py']
)
