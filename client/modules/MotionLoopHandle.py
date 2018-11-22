#!/usr/bin/env python2
# -*- coding: utf-8-*-
import logging
import re
import os
import time
from datetime import datetime
from client.app_utils import getConfig, getConfigData, sendToRobotAPI
import base64

"""
===============================================================================================
Module to handle motion detection events raised by the MotionLoop Sensor. Also used to turn
motion detection on or off by voice command. Note that actual filming is handled by the sensor
itself.
Usage: Triggered by motion detection events submitting entries to the Queue...also:
  You Say "Turn motion detection On (or Off)"
  You say "Turn security camera On (or Off)"
Author: Lee Matthews 2017
===============================================================================================
"""

# Set priority to high as it should come before 
# -----------------------------------------------------------------------------
PRIORITY = 3


# default function to handle the requests for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    logLevel = ENVIRON["loglvl"]
    logger = logging.getLogger(__name__)
    logger.level = logLevel
    # note that motion will trigger the chatbot module if not in security cam mode 
    if "SECURITYWARN" in text.upper() or "SECURITYVIDEO" in text.upper():
        logger.debug("Something to do with a security event was requested")
        if "SECURITYWARN" in text.upper():
            logger.debug("Need to warn someone of event. Triggering securityWarn() function")
            securityWarn(text, mic, ENVIRON, logger)
        if "SECURITYVIDEO" in text.upper():
            logger.debug("Need to handle new video. Triggering securityVideo() function")
            securityVideo(text, mic, ENVIRON, logger)
    elif "OFF" in text.upper() or "STOP" in text.upper():
        logger.debug("Seems to be request to turn OFF motion. Calling motionOff()")
        motionOff(text, mic, ENVIRON)
    elif "ON" in text.upper() or "START" in text.upper():
        logger.debug("Seems to be request to turn ON motion. Calling motionOn()")
        motionOn(text, mic, ENVIRON)
    else:
        logger.debug("Module MotionLoopHandle unable to determine what was requested")
        mic.say("I think you want to do something about my motion sensor, but I am not sure what.")
        mic.say("Can you be more specific?")


# returns true if the stated command contains the right keywords
# -------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\bmotion|security|camera|securitywarn|securityvideo\b', text, re.IGNORECASE))


# function to turn off the motion sensor (also turns off security mode)
# -------------------------------------------------------------------------
def motionOff(text, mic, ENVIRON):
    mic.say("Turning my motion sensor off")
    ENVIRON["motion"] = False
    ENVIRON["security"] = False


# function to turn on the motion sensor and security mode if requested
# -------------------------------------------------------------------------
def motionOn(text, mic, ENVIRON):
    ENVIRON["motion"] = True
    if "SECURITY" in text.upper():
        mic.say("Turning on my security system. I will alert you if I detect any motion.")
        ENVIRON["security"] = True
    else:
        mic.say("Turning on my motion sensor")


# function to handle motion sensor security alert (initial detection)
#-------------------------------------------------------------------------
def securityWarn(text, mic, ENVIRON, logger):
    # get variables required for sending the email
    TOPDIR = ENVIRON["topdir"]
    api_token = ENVIRON["api_token"]
    api_login = ENVIRON["api_login"]
    version = ENVIRON["version"]
    api_url = ENVIRON["api_url"]
    config = getConfigData(TOPDIR, "Motion")
    if "ERROR" in config or config == None:
        mic.say("Sorry, I could not access the motion sensor configuration. I cannot complete the task")
        return
    else:
        """ *******************************************************
        Sync the images folder to a cloud location for security
        - insert your own code into function synchFolder() below
        ****************************************************** """
        res = synchFolder(ENVIRON, logger)
        
        # send notification(s) on chosen channel(s)
        motion_email = config["Motion_notifyEmail"]
        motion_phone = config["Motion_notifyPhone"]
        motion_message = config["Motion_notifyText"]
        # if am email has been configured then send an email
        if len(motion_email) > 0:
            jsonpkg = {"subscriberID": api_login,
                  "token": api_token,
                  "version": version,
                  "email": motion_email,
                  "dtime": dtime
                  }
            api_url = os.path.join(api_url, 'email')
            response = sendToRobotAPI('POST', api_url, jsonpkg, mic, logger, ENVIRON)                    
        # if a phone number has been configured then send an SMS
        if len(motion_phone) > 0:
            jsonpkg = {"subscriberID": api_login,
                  "token": api_token,
                  "version": version,
                  "phone": motion_phone,
                  "text": motion_message
                  }
            api_url = os.path.join(api_url, 'sms')
            response = sendToRobotAPI('POST', api_url, jsonpkg, mic, logger, ENVIRON)                    
    
    
# function to handle motion sensor video file being generated
#-------------------------------------------------------------------------
def securityVideo(text, mic, ENVIRON, logger):
    # for a new video we will just synch the folder to the cloud again
    res = synchFolder(ENVIRON, logger)
    

    
""" *********************************************************************
 Function used to synch images from robotAI3/static/images to a cloud 
 location. This is to secure the video from local tampering to the Pi.
 Insert your own code here. 
********************************************************************* """
def synchFolder(ENVIRON, logger):
    # get the images path we need to synch
    TOPDIR = ENVIRON["topdir"]
    imgFolder = os.path.join(TOPDIR, 'static/images')
    print("Add your own code to robotAI3/client/modules/motionLoopHandle.py to synch video files to the cloud.")
    
    # return 1 if success
    return 1
    

