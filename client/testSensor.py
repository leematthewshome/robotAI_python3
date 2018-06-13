#!/usr/bin/python
"""
===============================================================================================
This module is used for TESTING ONLY

It is loaded by the sensors when they are run independently of the main robotAI process
This is to facilitate debugging the sensors in isolation
Note that the path is hard coded for the moment to /home/pi/robotAI3/client (see TOPDIR below)
Author: Lee Matthews 2018
===============================================================================================
"""
import os
import logging
from app_utils import getConfig, getConfigData
import tts, stt, mic

TOPDIR = '/home/pi/robotAI3'
filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
cfg_general = getConfigData(TOPDIR, "General")
cfg_listen = getConfigData(TOPDIR, "Listen")

def createEnviron():
    #set values shared across processes (fetch Listen config as we need it for stt_api)
    ENVIRON = {}
    ENVIRON["listen"] = True                                                #flags whether listenLoop is able to 'listen' for inputs
    ENVIRON["screen"] = True                                                #flags whether screen view is able to be changed or not
    ENVIRON["motion"] = False                                               #flags whether to run motion sensor
    ENVIRON["security"] = False                                             #flags whether we are in security mode for motion sensor
    ENVIRON["topdir"] = TOPDIR                                              #master directory to work paths off
    ENVIRON["loglvl"] = logging.DEBUG                                       #store General config debug flag
    ENVIRON["stt_api"]   = getConfig(cfg_listen, "Listen_stt_api")          #speech to text API to use
    ENVIRON["version"]   = getConfig(cfg_general, "General_version")        #version of client code
    ENVIRON["api_url"]   = getConfig(cfg_general, "General_api_url")        #API root entry point
    ENVIRON["api_token"] = getConfig(cfg_general, "General_api_token")      #token for access
    ENVIRON["api_login"] = getConfig(cfg_general, "General_api_login")      #subscriber login
    ENVIRON["devicename"]  = getConfig(cfg_general, "General_devicename")   #Identity of this device (eg. Doorbell, Home Assistant, etc.)
    return ENVIRON


def createMic(ENVIRON, speech):
    tts_engine_class = tts.get_engine_by_slug(speech)
    stt_engine = stt.robotAI_stt(ENVIRON)
    MIC = mic.Mic(tts_engine_class.get_instance(), stt_engine, ENVIRON)
    return MIC
