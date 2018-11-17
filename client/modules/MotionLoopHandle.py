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
motion detection on or off by voice command.
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
    # note that motion will trigger the chatbot module if not in security cam mode 
    if "SECURITYWARN" in text.upper() or "SECURITYVIDEO" in text.upper():
        logLevel = ENVIRON["loglvl"]
        logger = logging.getLogger(__name__)
        logger.level = logLevel
        if "SECURITYWARN" in text.upper():
            securityWarn(text, mic, ENVIRON, logger)
        if "SECURITYVIDEO" in text.upper():
            securityVideo(text, mic, ENVIRON, logger)
    elif "OFF" in text.upper() or "STOP" in text.upper():
        motionOff(text, mic, ENVIRON)
    elif "ON" in text.upper() or "START" in text.upper():
        motionOn(text, mic, ENVIRON)
    else:
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
    dtime = datetime.now().strftime('%Y-%m-%d %H:%M')
    arr = text.split(',')
    config = getConfigData(TOPDIR, "Motion")
    if "ERROR" in config or config == None:
        mic.say("Sorry, I could not access the motion sensor configuration. I cannot complete the task")
        return
    else:
        motion_email = config["Motion_notifyemail"]
        #????????? need to also allow for SMS ??????????
    
    # build basic json package to submit
    jsonpkg = {"subscriberID": api_login,
          "token": api_token,
          "version": version,
          "email": motion_email,
          "dtime": dtime
          }
    api_url = os.path.join(api_url, 'email')
    #response = sendToRobotAPI('POST', api_url, jsonpkg, mic, logger, ENVIRON)                    
    
    
# function to handle motion sensor video file being generated
#-------------------------------------------------------------------------
def securityVideo(text, mic, ENVIRON, logger):
    print('????????? Need to at least add some debugging here ?????????')
