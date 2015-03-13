# Beelogger Version 1.0, March 12th 2015
#! /bin/bash
#!/usr/bin/python
from ABElectronics_DeltaSigmaPi import DeltaSigma
import time
import sched
import datetime
import csv
import os
import math
import numpy
import threading
import logging
import sys
# import pytz

# ================================================
# Beelogger is using ABElectronics Delta-Sigma Pi 8-Channel ADC
# integrated 4 x load cells to determine the total weight and distribution
# integrated 3 x Temperature sensor D18S20 1-wire
# run with: python beelogger-v-1-0.py &
# ================================================


# Initialise the ADC device using the default addresses and sample rate 18
# Sample rate can be 12,14, 16 or 18
adc = DeltaSigma(0x68, 0x69, 18)
#set amplifier gain to 8
adc.setPGA(8)
#maximum weight of load cell in kg
capacity = 50
#used excitation voltage of load cell
excitationVoltage = 5 
# full scale calibration of the 4 load cells, e.g. 1.998mV/V excitation voltage = 50 kg
fullscaleOutput = (0.001998, 0.002001, 0.001997, 0.002003)
# Number of measurements to get average value and deviation
# value could be integrated in function gewichtsmessung
messwerte = 10
# time between mesurement in second (0.1 sec)
# parameter could be integrated in function gewichtsmessung
wartezeit = 0.10
a = range(messwerte)
# tz = pytz.timezone('Europe/Berlin')
# alle Zeitangaben in UTC!!!!!! 
# bsyslogdir is the directory for syslog messages of the beelogger program
BSYSLOGDIR = "/home/pi/beelogger/syslog"
# DEVICEDIR is the directory for wire-1 devices, e.g. DS18S20
DEVICESDIR = "/sys/bus/w1/devices/"
# DATADIR is the directory for the daily data files, created by the beelogger
DATADIR = "/home/pi/beelogger/data"


# Function gewichtsmessung does return weight mean and weight std values
def gewichtsmessung(nr): 
	for i in range(messwerte):
		a[i] = adc.readVoltage(nr)*capacity/(excitationVoltage*fullscaleOutput[nr-1])
		time.sleep(wartezeit)
	gewicht = numpy.mean(a)
	gewichtabw = numpy.std(a)
	return (gewicht, gewichtabw)


# Temperatur des Sensor DS18S20 auslesen
# temp=`echo $temp_read | egrep -o '[\-0-9]+$'`
# temperatur_DS18S20=`echo "scale=2; $temp / 1000" | bc` 
# echo "Temperatur des Sensor DS18S20 in C" $temperatur_DS18S20
# code taken from: http://www.stuffaboutcode.com/2013/12/raspberry-pi-python-temp-sensor-ds18b20.html

#class for holding temperature values
class Temperature():
    def __init__(self, rawData):
        self.rawData = rawData
    @property
    def C(self):
        return float(self.rawData) / 1000
    @property
    def F(self):
        return self.C * 9.0 / 5.0 + 32.0

#class for controlling the temperature sensor
class TempSensorController(threading.Thread):
    def __init__(self, sensorId, timeToSleep):
        threading.Thread.__init__(self)
       
        #persist the file location
        self.tempSensorFile = DEVICESDIR + sensorId + "/w1_slave"

        #persist properties
        self.sensorId = sensorId
        self.timeToSleep = timeToSleep

         #update the temperature
        self.updateTemp()
       
        #set to not running
        self.running = False
       
    def run(self):
        #loop until its set to stopped
        self.running = True
        while(self.running):
            #update temperature
            self.updateTemp()
            #sleep
            time.sleep(self.timeToSleep)
        self.running = False
       
    def stopController(self):
        self.running = False
	logging.info("Temperature Controller stopped")

    def readFile(self):
        sensorFile = open(self.tempSensorFile, "r")
        lines = sensorFile.readlines()
        sensorFile.close()
        return lines

    def updateTemp(self):
        data = self.readFile()
        #the output from the tempsensor looks like this
        #f6 01 4b 46 7f ff 0a 10 eb : crc=eb YES
        #f6 01 4b 46 7f ff 0a 10 eb t=31375
        #has a YES been returned?
        if data[0].strip()[-3:] == "YES":
            #can I find a temperature (t=)
            equals_pos = data[1].find("t=")
            if equals_pos != -1:
                tempData = data[1][equals_pos+2:]
                #update temperature
                self.temperature = Temperature(tempData)
                #update success status
                self.updateSuccess = True
            else:
                self.updateSuccess = False
		logging.info("Can not extract a temperatur")
        else:
            self.updateSuccess = False
	    logging.info("can not find a temperatur sensor")


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO,
		filename=BSYSLOGDIR+'/beelogger.log', #logfile
		format='%(asctime)s %(message)s') #include timestamp to log
	logging.info("Beelogger Program startet")
	tempcontrol1 = TempSensorController("10-000802bd07be",1)
 	tempcontrol2 = TempSensorController("10-000802dc101e",1)
	tempcontrol1.start()
	logging.info("Temperature Sensor 10-000802bd07be started")
	tempcontrol2.start()	
	logging.info("Temperature Sensor 10-000802dc101e started")
	heute = datetime.datetime.utcnow().strftime("%Y-%m-%d")
	datum = datetime.datetime.utcnow().strftime("%Y-%m-%d")
	try:
		while (True):
			heute = datetime.datetime.utcnow().strftime("%Y-%m-%d")
			with open(DATADIR + "/Beelogger_"+heute+'.csv',"a+",0) as csvfile:
	       			writer = csv.writer(csvfile,delimiter=',')
				writer.writerow( ("Datum", "Uhrzeit", "Temperatur1", "Temperatur2","Gewicht1","Gewichtsabw1","Gewicht2", "Gewichtsabw2", "Gewicht3", "Gewichtsabw3", "Gewicht4", "Gewichtsabw4") )
				logging.info("Create new datafile Beelogger_"+heute+".csv")
				while heute == datum:
					uhrzeit = datetime.datetime.utcnow().strftime("%H:%M:%S")
					temperatur_DS18S20_1 = round(tempcontrol1.temperature.C,3)
					temperatur_DS18S20_2 = round(tempcontrol2.temperature.C,3)
					(gewicht1, gewichtabw1) = gewichtsmessung(1)
					(gewicht2, gewichtabw2) = gewichtsmessung(2)
					(gewicht3, gewichtabw3) = gewichtsmessung(3)
					(gewicht4, gewichtabw4) = gewichtsmessung(4)
					gewicht1 = round(gewicht1,3)
					gewichtabw1 = round(gewichtabw1,3)
					gewicht2 = round(gewicht2,3)
					gewichtabw2 = round(gewichtabw2,3)
					gewicht3 = round(gewicht3,3)
					gewichtabw3 = round(gewichtabw3,3)
					gewicht4 = round(gewicht4,3)
					gewichtabw4 = round(gewichtabw4,3)
					writer.writerow( (datum, uhrzeit, temperatur_DS18S20_1, temperatur_DS18S20_2, gewicht1, gewichtabw1, gewicht2, gewichtabw2, gewicht3, gewichtabw3, gewicht4, gewichtabw4) )
					# run every 1 minute 
					# sleeptime = 60 - datetime.datetime.utcnow().second
					# run every 10 minutes, change sleeptime, see above 
					sleeptime = 600 - datetime.datetime.utcnow().second
					time.sleep(sleeptime)
					datum = datetime.datetime.utcnow().strftime("%Y-%m-%d")
	except (KeyboardInterrupt, SystemExit):
		logging.info("Beelogger SystemExit")
	finally:
		logging.info("Stopping sensors!")
		tempcontrol1.stopController()
		tempcontrol2.stopController()
		tempcontrol1.join()
		tempcontrol2.join()
		logging.info("Program BeeLogger stopped!")
		sys.exit()



