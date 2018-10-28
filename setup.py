#!/usr/bin/env python

import sys
from setuptools import setup


sys.stderr.write("""
==============================================================================
      The hypothesis-regex package was merged into Hypothesis in 2017.
                    Please just use the built-in version!
==============================================================================
""")


def read(path):
    with open(path) as f:
        return f.read()


setup(
    name='hypothesis-regex',
    version='0.4.0',
    description='Obseleted by merging as hypothesis.strategies.from_regex',
    long_description=read('README.rst'),
    author='Maxim Kulkin',
    author_email='maxim.kulkin@gmail.com',
    url='https://github.com/maximkulkin/hypothesis-regex',
    license='MIT',
    keywords=('hypothesis', 'regex'),
    py_modules=['hypothesis_regex'],
    install_requires=[
        'hypothesis>=3.8',
        'six>=1.10',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    classifiers=[
        'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
