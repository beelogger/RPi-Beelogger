# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

requires = [
    'paho-mqtt==1.2',
]

setup(name='rpi-beeloger',
      version='2.0.0',
      description='Python Code for the Beelogger',
      long_description='Python Code for the Beelogger (RPi project to build a bee hive weight monitor below 100 Euro)',
      license="GPL 2.0",
      classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v2",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Internet :: MQTT",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Archiving",
        "Topic :: System :: Networking :: Monitoring",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Operating System :: MacOS"
        ],
      author='Markus Hies',
      author_email='markus@hies.de',
      url='https://github.com/beelogger/RPi-Beelogger',
      packages=find_packages(),
      include_package_data=True,
      package_data={
      },
      zip_safe=False,
      install_requires=requires,
      dependency_links=[
      ],
      entry_points={
        'console_scripts': [
            'rpi-beelogger       = beelogger2:run',
        ],
      },
)
