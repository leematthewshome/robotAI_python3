"""
===============================================================================================
Sensor to listen for user input via Snowboy for hotword & activeListen for user command
Copyright: Lee Matthews 2016
Note that only one process at a time can use microphone. Need to ensure snowboy and active
listen are stopped for brain and phone to use microphone. ENVIRON["listen"] manages this.

TODO - Nothing atm
===============================================================================================
"""
import logging
import signal
import os
import time
# allow for running sensor directly for debug
if not __name__ == "__main__":
    import client.app_utils
    import client.snowboy.snowboydecoder


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
            config = app_utils.getConfigData(self.TOPDIR, "Listen")
            if "ERROR" in config:
                print("ListenLoop: Error getting Config: " + config["ERROR"])
            else:
                debugFlag = app_utils.getConfig(config, "Listen_2debug")
                self.hotword = app_utils.getConfig(config, "Listen_hotword")
                self.sense_desc = app_utils.getConfig(config, "Listen_sensitivity")
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
        if not self.ENVIRON["listen"]:
            self.interrupted = True
        return self.interrupted


    #Function Executed once the trigger keyword is received
    def startListenningActively(self):
        #Lee AutoLevel - display the current average noise level
        self.logger.debug("Current avg_noise is %s" % self.ENVIRON["avg_noise"] )

        if(not self.ENVIRON["listen"]):
            self.logger.debug("KEYWORD DETECTED. But ENVIRON listen is False so we ignore it")
        else:
            #flag that we are now busy with a process
            self.ENVIRON["listen"] = False
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
            if self.ENVIRON["listen"]:
                self.passiveListen()
            time.sleep(.3)


    # This function is called when keyword detected and self.ENVIRON["listen"] is True
    def activeListen(self):
        #Stop our robot and then begin listening actively
        self.SENSORQ.put(['snowboy', 'HALT ROBOT'])
        input = self.mic.activeListenToAllOptions()

        #active listen seems to return a list object, so convert to a string and comma separate
        input = ', '.join(input)
        #check whether a valid response was received from the API and send to brain for processing
        if 'APIERROR1' in input:
            self.mic.say('Sorry. There was a problem accessing the robot A I website to convert your speech into text')
            self.ENVIRON["listen"] = True
        elif 'APIERROR2' in input:
            self.mic.say('Sorry. I did not understand that. Please try again')
            self.ENVIRON["listen"] = True
        elif 'APIERROR3' in input:
            self.mic.say('Hmmn. A timely response was not received from the robot A I website to convert your speech into text. Perhaps try again.')
            self.ENVIRON["listen"] = True
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


    
# Allow to manually run the sensor in isolation using the below
#---------------------------------------------------------------
class Mic(object):
    def say(self, text):
        print(text)

    def activeListenToAllOptions(self):
        print("running activeListenToAllOptions")

if __name__ == "__main__":
    import app_utils
    import snowboy.snowboydecoder
    #set up ENVIRON object
    ENVIRON = {}
    ENVIRON["topdir"] = "/home/pi/robotAI3"
    #setup QUEUE object
    import Queue
    SENSORQ = Queue.Queue()
    #setup MIC object
    MIC = Mic()
    sensor = listenLoop(ENVIRON, SENSORQ, MIC)
    sensor.doListen()

