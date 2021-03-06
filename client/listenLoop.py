#!/usr/bin/env python
"""
===============================================================================================
Sensor to listen for user input via Snowboy for hotword & activeListen for user command
Author: Lee Matthews 2016
Note that only one process at a time can use microphone. Need to ensure snowboy and active
listen are stopped for brain and phone to use microphone. ENVIRON["listen"] manages this.

TODO - Nothing atm
===============================================================================================
"""
import logging
import signal
import os
import time
#allow for running listenloop either in isolation or via robotAI.py
try:
    from client.app_utils import getConfig, getConfigData, busyOn, busyOff, busyCheck
    from client.snowboy import snowboydecoder
except:
    from app_utils import getConfig, getConfigData, busyOn, busyOff, busyCheck
    from snowboy import snowboydecoder



#======================================================
# listenLoop class
#======================================================
class listenLoop(object):

    def __init__(self, ENVIRON, SENSORQ, MIC):
        self.ENVIRON = ENVIRON
        self.TOPDIR = ENVIRON["topdir"]
        #Lee AutoLevel - set initial value for background noise
        self.ENVIRON["avg_noise"] = 100
        filename = os.path.join(self.TOPDIR, "static/sqlite/robotAI.sqlite")
        #get the module configuration info
        if os.path.isfile(filename):
            config = getConfigData(self.TOPDIR, "Listen")
            if "ERROR" in config:
                print("ListenLoop: Error getting Config: " + config["ERROR"])
            else:
                debugFlag = getConfig(config, "Listen_2debug")
                self.hotword = getConfig(config, "Listen_hotword")
                self.sense_desc = getConfig(config, "Listen_sensitivity")
                self.sensitivty = getSensitivity(self.sense_desc)
        #Set debug level based on details in config DB
        self.logger = logging.getLogger(__name__)
        if debugFlag=='TRUE':
            self.logger.level = logging.DEBUG
        else:
            self.logger.level = logging.INFO
        self.SENSORQ = SENSORQ
        self.mic = MIC
        #set variable for snowboy
        self.interrupted = False



    #Snowboy signal_handler
    def signal_handler(self, signal, frame):
        self.logger.debug("Snowboy SIGNAL signal_handler tripped. Cleaning up.")
        self.interrupted = True


    #Snowboy interrupt callback function
    def interrupt_callback(self):
        if busyCheck(self.ENVIRON, self.logger) == True:
            self.interrupted = True
        return self.interrupted


    #Function Executed once the trigger keyword is received
    def startListenningActively(self):
        #Lee AutoLevel - display the current average noise level
        self.logger.debug("Current avg_noise is %s" % self.ENVIRON["avg_noise"] )

        if busyCheck(self.ENVIRON, self.logger) == True:
            self.logger.debug("KEYWORD DETECTED. But we are busy so ignore it")
        else:
            # set system to indicate things are busy
            busyOn(self.ENVIRON, self.logger)
            self.logger.debug("KEYWORD DETECTED. Beginning active listen ")
            self.activeListen()
        #go back to passive listening once ENVIRON["listen"] indicates it is OK
        self.waitUntilListen()


    # ---------------------------------------------------------------------------------------------------------------
    # This function is called in a loop to listen for user input
    # - if the Snowboy detector loop is stopped by an incoming call or by hearing the hotword, then waitUntilListen is
    #   called, which polls the ENVIRON Listen variable until we are ready to start passiveListen mode again
    # ----------------------------------------------------------------------------------------------------------------
    def passiveListen(self):
        partPath = "static/hotwords/" + self.hotword + ".pmdl"
        MODEL_FILE = os.path.join(self.TOPDIR, partPath)
        self.logger.debug("Hotword path = " + MODEL_FILE)

        #initialise Snowboy (Lee added debugLevel to inputs)
        signal.signal(signal.SIGINT, self.signal_handler)
        self.detector = snowboydecoder.HotwordDetector(MODEL_FILE, sensitivity=self.sensitivty,
                                                       debugLevel=self.logger.level, ENVIRON=self.ENVIRON)
        print('Snowboy is passively listening...')

        # Start the Main Snowboy listening loop
        self.detector.start(detected_callback=self.startListenningActively,
               interrupt_check=self.interrupt_callback,
               sleep_time=0.03)

        self.detector.terminate()
        self.waitUntilListen()


    # Snowboy cant run while the brain is busy doing stuff, in case brain needs pyaudio
    # So dont start snowboy until brain has indicated we are ready to begin listening again
    def waitUntilListen(self):
        self.logger.debug("waitUntilListen function is now monitoring the ENVIRON listen variable")
        self.interrupted = False
        while True:
            self.logger.debug("waitUntilListen - listen variable is %s" % str(self.ENVIRON['listen']))
            if busyCheck(self.ENVIRON, self.logger) == False:
                self.passiveListen()
            time.sleep(1)


    # This function is called when keyword detected and the system is not Busy
    def activeListen(self):
        #Stop our robot and then begin listening actively
        self.SENSORQ.put(['snowboy', 'HALT ROBOT'])
        input = self.mic.activeListenToAllOptions()

        #active listen seems to return a list object, so convert to a string and comma separate
        input = ', '.join(input)
        #check whether a valid response was received from the API and send to brain for processing
        if 'APIERROR1' in input:
            self.mic.say('Sorry. I did not understand that.')
            busyOff(self.ENVIRON, self.logger)
        elif 'APIERROR2' in input:
            self.mic.say('Sorry. There was a problem with the speech to text engine.')
            busyOff(self.ENVIRON, self.logger)
        elif 'APIERROR3' in input:
            self.mic.say('Hmmn. A timely response was not received from the speech to text engine. Perhaps try again.')
            busyOff(self.ENVIRON, self.logger)
        elif 'APIERROR4' in input:
            self.mic.say('Sorry. Something went wrong.')
            busyOff(self.ENVIRON, self.logger)
        else:
            self.SENSORQ.put(['brain', input])


#function to get sensitivity number from description
def getSensitivity(desc):
    sdict = {}
    sdict['7 Very High'] = .7
    sdict['6 High'] = .6
    sdict['5 Normal'] = .5
    sdict['4 Low'] = .4
    sdict['3 Very Low'] = .3
    if desc in sdict:
        return sdict[desc]
    else:
        return .5


# ==========================================================================
# Function called by main robotAI process to run this sensor
# ==========================================================================
def doListen(ENVIRON, SENSORQ, MIC):
    loop = listenLoop(ENVIRON, SENSORQ, MIC)
    loop.passiveListen()


    
# **************************************************************************
# This will only be executed when we run the sensor on its own for debugging
# **************************************************************************
if __name__ == "__main__":
    print("******** WARNING ********** Starting socketListener from __main__ procedure")
    from multiprocessing import Queue
    SENSORQ = Queue()

    import testSensor
    ENVIRON = testSensor.createEnviron()
    MIC = testSensor.createMic(ENVIRON, 'pico-tts')
    doListen(ENVIRON, SENSORQ, MIC)
