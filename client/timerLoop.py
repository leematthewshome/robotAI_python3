"""
===============================================================================================
Sensor for timed functions and operations, such as alerts and reminders
Relies on online APIs at ThisRobotAI.com 

TODO - Nothing atm
===============================================================================================
"""
import json
import logging
import requests
import os
import datetime
import time
#allow for running listenloop either in isolation or via robotAI.py
try:
    from client.app_utils import sendToRobotAPI, getConfigData, getConfig
except:
    from app_utils import sendToRobotAPI, getConfigData, getConfig
import pickle

class timerLoop(object):

    def __init__(self, ENVIRON, SENSORQ, MIC):
        self.Mic = MIC
        self.ENVIRON = ENVIRON
        self.SENSORQ = SENSORQ
        self.TOPDIR = ENVIRON["topdir"]
        self.api_url = ENVIRON["api_url"]
        self.api_token = ENVIRON["api_token"]
        self.api_login = ENVIRON["api_login"]
        filename = os.path.join(self.TOPDIR, "static/sqlite/robotAI.sqlite")
        #get the module configuration info
        if os.path.isfile(filename):
            config = getConfigData(self.TOPDIR, "Timer")
            if "ERROR" in config:
                print("TimerLoop: Error getting Config: " + config["ERROR"])
                debugFlag = 'TRUE'
            else:
                debugFlag = getConfig(config, "Timer_2debug")
                ignoreMins = getConfig(config, "Timer_ignore")
                if ignoreMins is None or not isinstance(ignoreMins, int):
                    self.ignoreMins = 10
                else:
                    self.ignoreMins = ignoreMins

        #Set debug level based on details in config DB
        self.logger = logging.getLogger(__name__)
        logging.basicConfig()
        if debugFlag=='TRUE':
            self.logger.level = logging.DEBUG
        else:
            self.logger.level = logging.INFO
        self.alertCache = {}                    #list of alerts that we need to monitor for exipry
        self.expiryCache = {}                   #list containing last run of expiry alerts
        self.curDate = datetime.date.today()    #used to compare to now() to determine if day has changed

             
    # Function used to fetch alerts and jobs from cache
    #============================================================================================
    def initCache(self, filename=None):
        self.logger.debug("Refreshing cache for Timer Loop from DB")
        #clear cache of all entries and get current day
        self.alertCache = {}

        #Fetch list of events for the local system date and day using API
        #-------------------------------------------------------------------------
        now = datetime.datetime.now()
        day = now.strftime("%a")
        dte = now.strftime("%Y") + now.strftime("%m") + now.strftime("%d")
        api_url = os.path.join(self.api_url, 'event')
        jsonpkg = {"subscriberID": self.api_login,
                  "token": self.api_token,
                  "day": day,
                  "dte": dte
                  }
        response = sendToRobotAPI('POST', api_url, jsonpkg, self.Mic, self.logger)
        try:
            rows = response["events"]
        except:
            rows = None
        if rows is None:
            self.logger.warning("There was an error getting data from the RobotAI server.")
            return True
        elif len(rows)==0:
            self.logger.warning("No scheduled alerts or jobs found for today.")
            return True
        else:
            filename = os.path.join(self.TOPDIR, "static/alerts.p")
            #save our list for access by the handle function 
            with open(filename, 'wb') as f:
                pickle.dump(rows, f)
            

        # loop through rows and enter values into cache.
        # NOTE THAT ORDER OF VALUES IN LIST RETURNED BY API MATTERS  ***********
        #===============================================
        for row in rows:
            #try to get time value
            try:
                t = row[1].split(":")
                myTime = datetime.time(hour=int(t[0]), minute=int(t[1]))
            except:
                myTime = None
            #Create Cache Entries for Once Off Alerts
            #-----------------------------------------
            if row[4] == "Once":
                try:
                    myDate = self.makeDate(row[2])
                    self.alertCache[row[0]] = datetime.datetime.combine(myDate, myTime)
                    self.logger.debug(str(row[0]) + " will expire at " + str(datetime.datetime.combine(myDate, myTime)))
                except:
                    self.logger.warning("Failed to add Once Off %s" % str(row[0]))
            #Create Cache Entries for Daily Alerts
            #-----------------------------------------
            if row[4] == "Daily":
                try:
                    myDate = datetime.date.today()
                    self.alertCache[str(row[0])] = datetime.datetime.combine(myDate, myTime)
                    self.logger.debug(str(row[0]) + " will expire at " + str(datetime.datetime.combine(myDate, myTime)))
                except:
                    self.logger.warning("Failed to add Daily alert %s" % row[0])
            #Create Cache Entries for Expiry Alerts
            #-----------------------------------------
            if row[4] == "Expiry":
                try:
                    #if we have a last run in the expiry cache then use that, else use now
                    if str(row[0]) in self.expiryCache:
                        data = self.expiryCache[str(row[0])]
                        myDate = data[0] + datetime.timedelta(minutes=data[1])
                        self.alertCache[str(row[0])] = myDate
                    else:
                        myDate = datetime.datetime.today() + datetime.timedelta(minutes=int(row[3]))
                        self.alertCache[str(row[0])] = myDate
                        data = [myDate, row[3]]
                        self.expiryCache[str(row[0])] = data
                        self.logger.debug(str(row[0]) + " will expire at " + str(myDate))
                except:
                    self.logger.warning("Failed to add Expiry alert %s" % row[0])
            #Create Cache Entries for Interaction Alerts
            #-----------------------------------------
            if row[4] == "Interact":
                try:
                    myDate = ENVIRON["lastInteract"] + datetime.timedelta(minutes=int(row[3]))
                    self.alertCache[str(row[0])] = myDate
                    self.logger.debug(str(row[0]) + " will expire at " + str(myDate))
                except:
                    self.logger.warning("Failed to add Interact alert %s" % row[0])

        #Set environment variable to indicate cache is now up to date
        self.ENVIRON["timerCache"] = True
        return True


    # Endless timer loop function, used to check for alerts that need to be fired
    #============================================================================================
    def runLoop(self):
        self.logger.debug("Starting Timer Loop")
        while True:
            curDTime = datetime.datetime.today()
            # If it is a new day or if external action invalidated cache (eg. DB update) then reload it
            if self.curDate < datetime.date.today():
                self.ENVIRON["timerCache"] = False
                self.curDate = datetime.date.today()
            if self.ENVIRON["timerCache"] == False:
                self.initCache()

            # Check for alerts and then loop through for alerts to fire
            if not self.alertCache:
                self.logger.debug("No scheduled alerts in cache.")
            else:
                self.logger.debug("Checking for expired alerts...")
                for id, dTime in self.alertCache.copy().items():
                    diff = dTime - curDTime
                    self.logger.debug("Alert %s expires in %s" % (id, diff))
                    # check if alert is due to be fired
                    if curDTime >= dTime:
                        # ignore events older than configured...so we dont repeat expired events when refresh cache
                        diff = curDTime - dTime
                        if (diff.seconds/60) > self.ignoreMins:
                            self.logger.warning("Ignoring alert %s as it expired over %s mins ago." % (id, self.ignoreMins))
                            self.handleAlert(id, 0)
                        else:
                            self.handleAlert(id, 1)
                        # if an Expiry alert then increment datetime by duration for next loop. Otherwise delete from cache
                        if id in self.expiryCache:
                            self.expiryCache[id][0] = curDTime
                            self.alertCache[id] = self.expiryCache[id][0] + datetime.timedelta(minutes=self.expiryCache[id][1])
                        else:
                            del self.alertCache[id]
            # sleep for one minute until the next loop
            # ToDo need to align sleep time to the exact minute end time, not just 60 seconds away
            self.logger.debug("Sleeping for 1 minute.")
            time.sleep(60)


    #Function executed when an event needs to be processed. if handle <> 1 then just expire it
    #============================================================================================
    def handleAlert(self, alertID, handle=1):
        # flag that we are now busy with a process so passive listen must stop
        self.ENVIRON["listen"] = False
        if handle == 1:
            sText = 'TIMER ALERT:' + str(alertID)
        else:
            sText = 'TIMER EXPIRE:' + str(alertID)
        self.logger.debug("Passing %s to Brain to handle" % sText)
        if self.SENSORQ is not None:
            self.SENSORQ.put(['brain', sText])


    def makeDate(self, dte):
        dte = str(dte)
        return datetime.datetime(int(dte[:4]), int(dte[4:6]), int(dte[-2:]))


# Function called by main robotAI procedure to start this sensor
def doTimer(ENVIRON, SENSORQ, MIC):
    loop = timerLoop(ENVIRON, SENSORQ, MIC)
    loop.runLoop()


# **************************************************************************
# This will only be executed when we run the sensor on its own for debugging
# **************************************************************************
if __name__ == "__main__":
    print("******** WARNING ********** Starting socketListener from __main__ procedure")
    from multiprocessing import Queue
    SENSORQ = Queue()

    import testSensor
    ENVIRON = testSensor.createEnviron()
    ENVIRON["timerCache"] = False
    MIC = testSensor.createMic(ENVIRON, 'pico-tts')

    doTimer(ENVIRON, SENSORQ, MIC)
