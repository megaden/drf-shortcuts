#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

import drf_shortcuts

setup(
    name='drf_shortcuts',
    version=drf_shortcuts.__version__,
    description="Common shortcuts for speeding up your development based on Django REST Framework (DRF).",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Daniel Ivanov',
    author_email='megaden4eg@gmail.com',
    url='https://github.com/megaden/drf-shortcuts',
    license='MIT',
    packages=['drf_shortcuts'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=['inflection>=0.3'],
)
