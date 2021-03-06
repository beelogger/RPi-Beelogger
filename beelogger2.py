#!/usr/bin/env python
# =======================================================
# RPi-Beelogger Version 2.0, Code 1.0, February 27th 2017
# https://github.com/beelogger/RPi-Beelogger
#
# RPi-Beelogger is using:
#
#   - ABElectronics Delta-Sigma Pi 8-Channel ADC
#   - Integrated 4 x load cells CZL601-50kg to determine the total weight and distribution
#   - Integrated 8 x Temperature sensor D18B20 1-wire
#
# Setup: python setup.py install
# Run:   sudo rpi-beelogger &
# =======================================================

import os
import sys
import ow
import csv
import math
import time
import json
import numpy
import sched
import smbus
import logging
import datetime
import threading
import paho.mqtt.client as mqtt

# Add path to submodule at runtime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libraries/ABElectronics_Python_Libraries/ADCDifferentialPi'))
from ABE_ADCDifferentialPi import ADCDifferentialPi
from ABE_helpers import ABEHelpers


# -------------
# Configuration
# -------------

# Initialise the ADC device using the default addresses and sample rate 18
# Sample rate can be 12,14, 16 or 18
i2c_helper = ABEHelpers()
bus = i2c_helper.get_smbus()
adc = ADCDifferentialPi(bus, 0x68, 0x69, 16)
#set amplifier gain to 8
adc.set_pga(8)
#maximum weight of load cell in kg
capacity = 50
#used excitation voltage of load cell, external power supply
excitationVoltage = 5
# full scale calibration of the load cells, e.g. 2mV/V excitation voltage 1
# data 1-4 taken from load cell data sheet
fullscaleOutput = (0.001953, 0.001948, 0.001943, 0.001933, 0.002, 0.002, 0.002, 0.002)
# Zero Value in V of CZL601-50kg (including Unterboden of bee hive)
# zerovalue = (0.000258, 0.000438, 0.000453, 0.000429, 0.000,0.000, 0.000, 0.000)
zerovalue = (0.000, 0.000, 0.000, 0.000, 0.000,0.000, 0.000, 0.000)
# Number of measurements to get average value and deviation
# value could be integrated in function gewichtsmessung
messwerte = 10
# time between mesurement in second (set between 0.1 an 1 sec)
wartezeit = 1
a = range(messwerte)
# DS18B20 Sensors HW Addresses to use with OWFS
# Order of sensors: #1-7 in beehive, #8 below beehive
temp_sensor = ("/28.FFF85B501604", "/28.FFFB7B451603", "/28.FF8958501604", "/28.FF1F99511604", "/28.FFD7D3031502", "/28.FF884C451603" , "/28.FF0B2D511604", "/28.FF838C451603")
#
# alle Zeitangaben in UTC!!!!!!
#
# bsyslogdir is the directory for syslog messages of the beelogger program
BSYSLOGDIR = "/home/pi/beelogger2/syslog"
# DATADIR is the directory for the daily data files, created by the beelogger
DATADIR = "/home/pi/beelogger2/data"

# MQTT broker host
mqtt_broker = 'swarm.hiveeyes.org'

# MQTT bus topic
mqtt_topic = u'{realm}/{network}/{gateway}/{node}/data.json'.format(
    realm = 'hiveeyes',
    network = 'your identifier',     			  # Imker
    gateway = 'your site',                                # Standort
    node = 'your node'                                    # Bienenstock
)



# ------------
# Main program
# ------------

# Create MQTT client-id
pid = os.getpid()
client_id = '{}:{}'.format('client',str(pid))

# Function gewichtsmessung does return weight mean and weight std values
def gewichtsmessung(nr):
	for i in range(messwerte):
		#a[i] = adc.read_voltage(nr)
		a[i] = (adc.read_voltage(nr)-zerovalue[nr-1])*capacity/(excitationVoltage*fullscaleOutput[nr-1])
		time.sleep(wartezeit)
	gewicht = numpy.mean(a)
	gewichtabw = numpy.std(a)
	return (gewicht, gewichtabw)

# Function temperaturmessung does return temperature in degree C
def temperaturmessung(sensor_nr):
	# The power-on register value of DS18B20 is "85", which is considered a bad reading. Work around that.
	temperature = 85
	while temperature == 85:
		temperature = float(ow.Sensor(temp_sensor[sensor_nr]).temperature)
	return (temperature)

def measure():

	# Do measurement
	temperature_1 = temperaturmessung(0)
	temperature_2 = temperaturmessung(1)
	temperature_3 = temperaturmessung(2)
	temperature_4 = temperaturmessung(3)
	temperature_5 = temperaturmessung(4)
	temperature_6 = temperaturmessung(5)
	temperature_7 = temperaturmessung(6)
	temperature_8 = temperaturmessung(7)
	(gewicht1, gewichtabw1) = gewichtsmessung(1)
	(gewicht2, gewichtabw2) = gewichtsmessung(2)
	(gewicht3, gewichtabw3) = gewichtsmessung(3)
	(gewicht4, gewichtabw4) = gewichtsmessung(4)
	gewicht1 = round(gewicht1,6)
	gewichtabw1 = round(gewichtabw1,6)
	gewicht2 = round(gewicht2,6)
	gewichtabw2 = round(gewichtabw2,6)
	gewicht3 = round(gewicht3,6)
	gewichtabw3 = round(gewichtabw3,6)
	gewicht4 = round(gewicht4,6)
	gewichtabw4 = round(gewichtabw4,6)
	gewichttotal = round(gewicht1+gewicht2+gewicht3+gewicht4,6)
	gewichtabw = round(gewichtabw1+gewichtabw2+gewichtabw3+gewichtabw4,6)

	# Prepare data for MQTT
	measurement_data = {
	    'Temperature 1 Inside': temperature_1,
	    'Temperature 2 Inside': temperature_2,
	    'Temperature 3 Inside': temperature_3,
	    'Temperature 4 Inside': temperature_4,
	    'Temperature 5 Inside': temperature_5,
	    'Temperature 6 Inside': temperature_6,
	    'Temperature 7 Inside': temperature_7,
	    'Temperature 8 Outside': temperature_8,
	    'Weight Total': gewichttotal,
	    'Weight Total StdDev': gewichtabw,
	    'Weight 1': gewicht1,
	    'Weight 1 StdDev': gewichtabw1,
	    'Weight 2': gewicht2,
	    'Weight 2 StdDev': gewichtabw2,
	    'Weight 3': gewicht3,
	    'Weight 3 StdDev': gewichtabw3,
	    'Weight 4': gewicht4,
	    'Weight 4 StdDev': gewichtabw4
	}

	# Prepare data for CSV
	measurement_tuple = (
		temperature_1, temperature_2, temperature_3, temperature_4, temperature_5, temperature_6, temperature_7, temperature_8,
		gewicht1, gewichtabw1, gewicht2, gewichtabw2, gewicht3, gewichtabw3, gewicht4, gewichtabw4, gewichttotal, gewichtabw)

	return measurement_data, measurement_tuple

def run():
	logging.basicConfig(level=logging.INFO,
		filename=BSYSLOGDIR+'/beelogger2.log', #logfile
		format='%(asctime)s %(message)s') #include timestamp to log
	logging.info("Beelogger2 Program startet")
	# You can now start using OWFS to access your i2c devices and any connected sensors:
	# sudo /opt/owfs/bin/owfs --i2c=ALL:ALL --allow_other /mnt/1wire
	# for details check: https://www.abelectronics.co.uk/kb/article/3/owfs-with-i2c-support-on-raspberry-pi
	# starting owfs and logging sensors found to file
	ow.init('localhost:4304')
	sensorlist = ow.Sensor('/').sensorList()
	for sensor in sensorlist:
		logging.info("Device found: Type="+sensor.type+" Family="+sensor.family+" Address="+sensor.address+" ID="+sensor.id)
	# set start values heute and datum to loop until next day, new csv file created
	heute = datetime.datetime.utcnow().strftime("%Y-%m-%d")
	datum = datetime.datetime.utcnow().strftime("%Y-%m-%d")
	# loop forever until something in loop returns or breaks
	try:
		while True:
			heute = datetime.datetime.utcnow().strftime("%Y-%m-%d")
			with open(DATADIR+"/Beelogger2_"+heute+".csv","a+",0) as csvfile:
				writer = csv.writer(csvfile,delimiter=',')
				# check if file is empty: write headerrow, else continue with appending data
				first_char = csvfile.read(1)
				if not first_char:
					writer.writerow( ("Datum", "Uhrzeit", "Temp1", "Temp2","Temp3","Temp4","Temp5","Temp6","Temp7","Temp8","Gewicht1","Gewichtsabw1","Gewicht2", "Gewichtsabw2", "Gewicht3", "Gewichtsabw3", "Gewicht4", "Gewichtsabw4","Gesamtgewicht","Gewichtabw") )
					logging.info("Create new datafile Beelogger2_"+heute+".csv")
				else:
					logging.info ("Append to existing datafile Beelogger2_"+heute+".csv")
				while heute == datum:
					uhrzeit = datetime.datetime.utcnow().strftime("%H:%M:%S")

					# Perform measurement
                    measurement_data, measurement_tuple = measure()

					# Serialize data as JSON
					payload = json.dumps(measurement_data)

					# Publish data to MQTT Backend
					backend = mqtt.Client(client_id=client_id, clean_session=True)
					backend.connect(mqtt_broker)
					backend.publish(mqtt_topic, payload)
					backend.disconnect()

					# Write data to CSV file
					writer.writerow( (datum, uhrzeit) + measurement_tuple )

					# define sleeptime, round to full minute
					sleeptime = 600 - datetime.datetime.utcnow().second
					# run every 10 minutes, change sleeptime, see above
					time.sleep(sleeptime)
					# set new value for datum, to check if new csv file needs to be created
					datum = datetime.datetime.utcnow().strftime("%Y-%m-%d")

	except Exception as err:
		# Exit Routine, if something breaks write error-nr and line-nr to log file):
		logging.info("Beelogger SystemExit, something went wrong: "+str(err)+" at line "+sys.exc_traceback.tb_lineno)
	finally:
		logging.info("Stopping sensors!")
		logging.info("Program BeeLogger stopped!")
		sys.exit()

if __name__ == "__main__":
    run()
