from setuptools import setup, find_packages

setup(name='logwiz',
      version='0.0.1',
      author='fram',
      author_email='pavel.sht(gav-gav-gav)yandex.ru',
      packages=find_packages(),
      scripts=['logwiz/scripts/log_analyzer.py'],
      package_data={'logwiz': ['static/*.html']},
      test_suite='tests'
      )
