# -*- coding: utf-8-*-
import logging
import re
import os
from client.app_utils import getConfig, getConfigData, sendToRobotAPI
import pickle
"""
===============================================================================================
Module to handle Alert / Alarm / Reminder events raised by the TimerLoop Sensor
Usage: Triggered by expiry of events in the calendar or system events
Copyright: Lee Matthews 2017
===============================================================================================
"""


#returns true if the stated command contains the right keywords
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\btimer alert|timer expire|calendar|event|alert|alarm\b', text, re.IGNORECASE))


# default function to handle the requests for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    if "TIMER ALERT" in text:
        eventHandle(text, mic, ENVIRON, 1)
    elif "TIMER EXPIRE" in text:
        eventHandle(text, mic, ENVIRON, 0)
    elif "UPDATE" in text or "REFRESH" in text or "RELOAD" in text:
        refreshCache(text, mic, ENVIRON)
    else:
        mic.say("I think you want to do something about my calendar or schedule, but I am not sure what.")
        mic.say("Can you be more specific?")


# function to refresh the daily cache of events 
# -------------------------------------------------------------------------
def refreshCache(text, mic, ENVIRON):
    ENVIRON["timerCache"] = False
    mic.say("OK. I will update my list of events from the system in one minute.")


# function to handle the expiry of an event (triggered by TIMER ALERT)
#-------------------------------------------------------------------------
def eventHandle(text, mic, ENVIRON, handle=1):
    sl = text.split(":")
    id = sl[1]
    logger = logging.getLogger(__name__)

    #set default text to say if we dont find the event details in cache
    sText = "That is odd. I need to remind you about an event but I cannot find the text. Perhaps it was deleted."
    
    #Get config details for the timer module 
    TOPDIR = ENVIRON["topdir"]
    filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
    if os.path.isfile(filename):
        # get timer module configuration information or use defaults
        config = getConfigData(TOPDIR, "Timer")
        if "ERROR" in config:
            logger.warning("Error getting Timer sensor config: " + config["ERROR"])
            def_alarm = "doorDingDong.wav"
            debugFlag = 'TRUE'
        else:
            def_alarm = getConfig(config, "Timer_def_alarm")
            debugFlag = getConfig(config, "Timer_2debug")

    if debugFlag == 'TRUE':
        logger.level = logging.DEBUG

    # get api detalis from the environment 
    api_token = ENVIRON["api_token"]
    api_login = ENVIRON["api_login"]
    api_url = ENVIRON["api_url"]
    api_url = os.path.join(api_url, 'event', id)
    logger.debug("Path to call Event API will be %s " % api_url)

    # if expiry only then do it and exit
    if handle == 0:
        logger.debug("Expired event, so we will just mark it off as expired ")
        updateEvent(api_login, api_token, api_url, mic, logger, ENVIRON)
        return
    
    alarm = os.path.join(TOPDIR, "static/audio", def_alarm)

    # fetch details of the alert from the daily file cache
    # NOTE THAT ORDER OF VALUES IN LIST RETURNED BY API MATTERS  ***********
    #===========================================================================
    filename = os.path.join(TOPDIR, "static/alerts.p")
    try:
        with open(filename, 'rb') as f:
            events = pickle.load(f)
            for event in events:
                #print event
                if str(event[0]) == str(id):
                    sText = event[5]
                    execute = event[6]
    except:
        sText == "That is odd. I need to remind you about an event but I was not able to find the details on file. "

    # Work out what we should be doing about this particular alert
    # --------------------------------------------------------------------------
    filename = os.path.join(TOPDIR, "client/modules/TimerLoopCustom.py")
    if execute == 'alert' or execute == None:
        # Todo Work out how to handle snoozing of alerts by the user
        mic.play(alarm)
        mic.say(sText)
    # set environment variable for security mode on
    elif execute == 'securityOn':
        logger.debug("Turning security camera mode on")
        ENVIRON["motion"] = True
        ENVIRON["security"] = True
    # set environment variable for security mode off
    elif execute == 'securityOff':
        logger.debug("Turning security camera mode off")
        ENVIRON["motion"] = False
        ENVIRON["security"] = False
    # if chat is selected then use the text as the chat item to fetch
    elif execute == 'chat':
        from ChatBot import chatBot
        bot = chatBot(sText, mic, ENVIRON)
        bot.doChat(sText)
    # if chat is selected then use the text as the chat item to fetch
    elif execute == 'command':
        ENVIRON["command"] = sText
    # check for file which the user can add custom functions into
    else:
        mic.say("A calendar event expired but I am note sure how to handle it. You may need to update it online.")

    # Flag the event as expired using API
    updateEvent(api_login, api_token, api_url, mic, logger, ENVIRON)

    

# function to call the API to update events as Expired
#-------------------------------------------------------------------------
def updateEvent(api_login, api_token, api_url, mic, logger, ENVIRON):
    jsonpkg = {'subscriberID': api_login,
               'token': api_token,
               }
    result = sendToRobotAPI('PUT', api_url, jsonpkg, mic, logger, ENVIRON)

