# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(
    name='bluffinmuffin.aiclient',
    version='0.0.1',
    packages=find_packages(),
    namespace_packages=['bluffinmuffin'],
    scripts=['scripts/poker_ai_client.py'],
    url='',
    license='LICENSE.txt',
    author='Mathieu Germain',
    author_email='mathieu.germain@gmail.com',
    description='',
    install_requires=['bluffinmuffin.protocol', 'numpy']
)
