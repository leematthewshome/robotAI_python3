#!/usr/bin/python
"""
===============================================================================================
Main code module for RobotAI. Updated for Pythin3
Runs the various sensors, and feeds input to brain. 
Also talks to the Arduino for robot control if connected.
Author: Lee Matthews 2018
===============================================================================================
"""
#import essential python modules
import os
from multiprocessing import Process, Manager, Queue
import time
import logging
import socket

#import essential client modules
from client.app_utils import getConfig, getConfigData, uzbl_goto
from client import tts, stt, brain
from client import mic


#---------------------------------------------------------
# Get general configuration details and setup logging
#---------------------------------------------------------
logging.basicConfig()
logger = logging.getLogger("robotAI")
isConfig = False                            #set to false before we check for file
face_url = "http://localhost:5000"          #set default in case no General config
TOPDIR = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
# If config DB does not exist then assume its the first time code has been run and get starter DB
if not os.path.isfile(filename):
    starterDB = os.path.join(TOPDIR, "static/sqlite/starterDB.sqlite")
    from shutil import copyfile
    copyfile(starterDB, filename)
# Still allow for the fact that starter DB might be missing
if os.path.isfile(filename):
    cfg_general = getConfigData(TOPDIR, "General")
    if "ERROR" in cfg_general:
        debugFlag = "TRUE"
        logger.warning("ERROR accessing config: " + cfg_general["ERROR"])
    else:
        isConfig = True
        face_url = getConfig(cfg_general, "General_def_face")
        debugFlag = getConfig(cfg_general, "General_debug")
else:
    debugFlag = "TRUE"
    logger.warning("CONFIG ERROR Could not find file " + filename)
    cfg_general = None

# added verbal announcement if debug else pause few seconds
if debugFlag == 'TRUE':
    logger.setLevel(level=logging.DEBUG)
    logLevel = logging.DEBUG
    os.system('flite -voice awb -t "Robot configuration loaded"')
else:
    logger.setLevel(level=logging.INFO)
    logLevel = logging.INFO
    print("PAUSING FOR A MOMENT......THIS ALLOWS WIFI TO CONNECT")
    time.sleep(5)


#---------------------------------------------------------
# Open serial connection to talk to Arduino
# Loop through all com ports, but we should only have 1 anyway
# -----------------------------------------------------------------
serPort = ""
try:
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    for port_no, description, address in ports:
        #print port_no + " : " + description + " : " + address
        # we only want the USB port for Arduino
        if 'USB' in port_no:
            serPort = port_no
except:
    logger.debug("No Serial Port library to import")

if len(serPort) > 0:
    logger.debug("creating connection to serPort for ARDUINO")
    ARDUINO = serial.Serial(serPort, 9600)
else:
    logger.warning("Could not find serial port for ARDUINO")
    ARDUINO = None


#---------------------------------------------------------
# Other functions
#---------------------------------------------------------
#Function to stop our robot, usually called when hotword detected
def stopRobot():
    if ARDUINO is not None:
        ARDUINO.write('h')
    else:
        logger.debug("Could not send stop to robot. ARDUINO = None")
    if ENVIRON["screen"]:
        # wake up the screen and display the default page
        # command = 'sudo sh -c "echo 0 > /sys/class/backlight/rpi_backlight/bl_power"'
        # os.system(command)
        uzbl_goto(face_url)


# Check if we can access the internet
def check_internet(server="www.google.com"):
    logger.debug("Checking network connection to server '%s'...", server)
    try:
        # see if we can resolve the host name -- tells us if there is a DNS listening
        host = socket.gethostbyname(server)
        # connect to the host -- tells us if the host is actually reachable
        socket.create_connection((host, 80), 2)
    except Exception:
        logger.warning("Internet does not seem to be available")
        return False
    else:
        logger.debug("Internet connection working")
        return True

#Function to continuously check Queue and perform relevant actions
#-----------------------------------------------------------------
def sensorLoop(MIC, BRAIN, ENVIRON):
    while True:
        # check sensor queue for things to process. Dont block
        if not SENSORQ.empty():
            item = SENSORQ.get(False)
            proc = item[0]
            text = item[1]
            logger.debug('Received data from ' + proc + ' Command = ' + text)
            #work out what to do with the queue item we received
            if len(text) > 0:
                logger.debug("Text found in queue : %s" % text)
                # Stop robot moving if we heard the keyword
                if proc == 'snowboy':
                    stopRobot()
                # send the text to the brain to be processed. When complete set ENVIRON listen back to True
                elif proc == 'brain':
                    BRAIN.query(text)
                    ENVIRON["listen"] = True
                    logger.debug("Brain has finished working. Setting ENVIRON listen = True")
                # let the user know we received something but have no instructions
                else:
                    MIC.say("Unknown queue item from process " + proc)
            else:
                MIC.say("Pardon?")
                ENVIRON["listen"] = True
        # Check if a message received from the server or a command inserted in ENVIRON
        if ENVIRON.get("command"):
            msg = ENVIRON.pop('command', None)
            SENSORQ.put(['brain', msg.upper()]) 
        time.sleep(1)



#---------------------------------------------------------
#Kick off sensor functions in separate processes
#---------------------------------------------------------
if __name__ == '__main__':
    # added verbal announcement if debug else pause 2 seconds
    if debugFlag == 'TRUE':
        os.system('flite -voice awb -t "Setting up Robot environment"')
    else:
        print("PAUSING SOME MORE.....TO ALLOW WIFI TO CONNECT")
        time.sleep(5)

    # try to connect to internet a number of times
    tries = 5
    isWWWeb = False
    if debugFlag == 'TRUE':
        os.system('flite -voice awb -t "Checking for internet connectivity"')
    while tries > 0 and isWWWeb == False:
        isWWWeb = check_internet()
        if isWWWeb == False:
            tries = tries - 1
            time.sleep(3)

    #set values shared across processes (fetch Listen config as we need it for stt_api)
    cfg_listen = getConfigData(TOPDIR, "Listen")
    mgr = Manager()
    ENVIRON = mgr.dict()
    ENVIRON["listen"] = True                                                #flags whether listenLoop is able to 'listen' for inputs
    ENVIRON["screen"] = True                                                #flags whether screen view is able to be changed or not
    ENVIRON["motion"] = False                                               #flags whether to run motion sensor
    ENVIRON["security"] = False                                             #flags whether we are in security mode for motion sensor
    ENVIRON["topdir"] = TOPDIR                                              #master directory to work paths off
    ENVIRON["loglvl"] = logLevel                                            #store General config debug flag
    ENVIRON["stt_api"]   = getConfig(cfg_listen, "Listen_stt_api")          #speech to text API to use
    ENVIRON["version"]   = getConfig(cfg_general, "General_version")        #version of client code
    ENVIRON["api_token"] = getConfig(cfg_general, "General_api_token")      #token for access
    ENVIRON["api_login"] = getConfig(cfg_general, "General_api_login")      #subscriber login
    ENVIRON["api_url"]   = getConfig(cfg_general, "General_api_url")        #API root entry point

    #setup queue shared across functions
    SENSORQ = Queue()

    # Setup Text to Speech instance based on config
    if isConfig:
        tts_engine_class = tts.get_engine_by_slug(cfg_general["General_tts_api"])
    else:
        tts_engine_class = tts.get_engine_by_slug(tts.get_default_engine_slug())

    # Setup Speech to Text and MIC based on config and internet availability
    if isConfig and isWWWeb:
        stt_engine = stt.robotAI_stt(ENVIRON)
        MIC = mic.Mic(tts_engine_class.get_instance(), stt_engine, ENVIRON)
    else:
        MIC = mic.Mic(tts_engine_class.get_instance(), None, ENVIRON)
    
    # Brain is used to handle jobs that are taken from the SENSORQ
    BRAIN = brain.brain(MIC, ENVIRON)

    # Say hello or let the user know if there were problems
    #---------------------------------------------------------------------
    config = getConfigData(TOPDIR, "Listen")
    robotName = getConfig(config, "Listen_hotword")
    MIC.say("Hello. I am Your Robot A. I. ")
    salutation = "One moment while I start my sensors."
    if not isConfig or not isWWWeb:
        salutation = salutation + "Please note, speech to text is disabled. So I cannot accept voice commands. "
    if not isConfig:
        salutation = salutation + "This is because I could not find a configuration file."
    if not isWWWeb:
        salutation = salutation + " This is because I could not connect to the internet."
    MIC.say(salutation)

    #ToDo Check for connectivity to the RobotAI Website to determine if we have credentials / access

    
    # ---------------------------------------------------------------------------------------
    # Start web server to allow user to edit configuration
    # ---------------------------------------------------------------------------------------
    #MIC.say('Starting the web service.')
    #logger.info("STARTING WEB SERVER")
    #try:
    #    from webserver import webserver
    #    w = Process(target=webserver.doWebserver, args=(ENVIRON, SENSORQ, MIC, ))
    #    w.start()
    #except:
    #    MIC.say("There was an error starting the webserver. It will not be possible to setup the system.")

    # ---------------------------------------------------------------------------------------
    # kick off timer process based on enabled = TRUE
    # ---------------------------------------------------------------------------------------
    cfg_timer = getConfigData(TOPDIR, "Timer")
    if getConfig(cfg_timer, "Timer_1enable")=='TRUE':
        MIC.say('Starting my timer sensor, to process scheduled tasks and alerts.')
        logger.info("STARTING THE TIMER SENSOR")
        ENVIRON["timerCache"] = False   # flags whether the alert cache is up to date or not
        try:
            from client import timerLoop
            t = Process(target=timerLoop.doTimer, args=(ENVIRON, SENSORQ, MIC, ))
            t.start()
        except:
            MIC.say("There was an error starting the Timer sensor. No scheduled tasks or alarms will be possible.")
    cfg_timer = None
    
    # now call Queue loop to monitor results from remote sensor processes
    # NOTE: This should be the very last operation as it runs constantly
    # ---------------------------------------------------------------------
    sensorLoop(MIC, BRAIN, ENVIRON)