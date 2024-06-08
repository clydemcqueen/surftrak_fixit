#!/usr/bin/env python3

import os
import ssl

from setuptools import setup

# Ignore ssl if it fails
if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
    ssl._create_default_https_context = ssl._create_unverified_context

setup(
    name='surftrak_fixit',
    version='0.0.1',
    description='Surftrak Fixit',
    license='MIT',
    install_requires=[
        'aiohttp == 3.9.5',
        'fastapi == 0.109.1',
        'loguru == 0.6.0',
        'pydantic == 2.7.2',
        'requests == 2.31.0',
        'uvicorn == 0.13.4',
    ],
)
