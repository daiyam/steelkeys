#!/usr/bin/env python

from os.path import dirname, join
from setuptools import setup

setup(
	name='steelkeys',
	version='0.1',
	description='Configuration tool for SteelSeries RGB keyboards.',
	long_description=open(join(dirname(__file__), 'README.md')).read(),
	url='',
	author='Baptiste Augrain',
	author_email='daiyam@zokugun.org',
	license='MIT',
	packages=['steelkeys'],
	package_dir={'steelkeys':'src'},
	entry_points={
		'console_scripts': [
			'steelkeys=steelkeys.main:main',
		],
	},
	package_data={'steelkeys': ['models.yaml', 'layouts/*.yaml','presets/*.yaml']},
	keywords=['steelseries', 'rgb', 'keyboard'],
	classifiers=[
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
	],
)
