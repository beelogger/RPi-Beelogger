#############
RPi-Beelogger
#############


************
Introduction
************
Python Code for the Beelogger, a RaspberryPi-based project to build a bee hive weight monitor below 100 Euro.
For further details, please have a look at http://blog.hies.de/?cat=18.


*****
Setup
*****

Dependencies
============
::

    apt install python-smbus python-ow python-numpy

::

    git clone --recursive https://github.com/beelogger/RPi-Beelogger.git
    cd RPi-Beelogger
    python setup.py install

.. seealso::

    - https://www.abelectronics.co.uk/kb/article/3/owfs-with-i2c-support-on-raspberry-pi
    - https://www.abelectronics.co.uk/kb/article/1/i2c--smbus-and-raspbian-linux


Run
===
::

    rpi-beelogger


***********
Development
***********
::

    virtualenv .venv27
    source .venv27/bin/activate
    python setup.py develop


Run
===
::

    rpi-beelogger

