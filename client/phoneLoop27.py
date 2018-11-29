"""
===============================================================================================
Sensor to handle incoming IP calls using Linphone's Python API
Author: Lee Matthews 2016
Expects Contacts table in the RobotAI config database. Callers that are whitelisted in table 
are allowed to dial straight through. 

This needs to be run in a Python27 process. For robotAI3 code this is started as an external 
process. We therefore pass the config DB path and fetch all variables locally.
===============================================================================================
"""
#!/usr/bin/env python
import linphone
import logging
import signal
import time
import os
import sqlite3
import threading
from app_utils import getConfig, getConfigData, sendToRobotAPI, busyOn, busyCheck


class SecurityCamera:

    #def __init__(self, ENVIRON, SENSORQ, MIC, snd_playback=''):
    def __init__(self, ENVIRON, snd_playback=''):
        #add callee parameter to the environment, for outgoing calls
        ENVIRON["callee"] = None
        self.TOPDIR = ENVIRON["topdir"]
        filename = os.path.join(self.TOPDIR, "static/sqlite/robotAI.sqlite")
        #get the module configuration info
        if os.path.isfile(filename):
            config = getConfigData(self.TOPDIR, "Phone")
            if "ERROR" in config:
                logger.debug("Error getting the sensor configuration: " + config["ERROR"])
            else:
                debugFlag = getConfig(config, "Phone_2debug")
                self.camera = getConfig(config, "Phone_camera")
                self.snd_capture = getConfig(config, "Phone_snd_capture")
                self.admin = getConfig(config, "Phone_admin")
                username = getConfig(config, "Phone_account")
                password = getConfig(config, "Phone_password")

        self.ENVIRON = ENVIRON
        #self.SENSORQ = SENSORQ
        #self.MIC = MIC

        self.quit = False
        callbacks = {
            'call_state_changed': self.call_state_changed
        }
        #---------------------------------------
        # Configure the linphone core
        #---------------------------------------
        # Set debug level based on details in config DB
        self.logger = logging.getLogger(__name__)
        if debugFlag == 'TRUE':
            self.logger.level = logging.DEBUG
            logging.basicConfig(level=logging.DEBUG)
        else:
            self.logger.level = logging.INFO
            logging.basicConfig(level=logging.INFO)

        linphone.set_log_handler(self.log_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        self.core = linphone.Core.new(callbacks, None, None)
        self.core.max_calls = 1
        self.core.echo_cancellation_enabled = True
        self.core.video_capture_enabled = True
        self.core.keep_alive_enabled = True
        self.core.video_display_enabled = False
        self.core.stun_server = 'stun.linphone.org'
        self.core.ring = self.TOPDIR + "/static/audio/oldphone.wav"
        self.logger.debug("self.core.ring = " + self.core.ring)
        self.core.ringback = self.TOPDIR + "/static/audio/ringback.wav"
        self.logger.debug("self.core.ringback = " + self.core.ringback)
        # self.core.ice_enabled = True
        #if len(self.camera):
        #    self.logger.debug("Camera = " + self.camera)
        #    self.core.video_device = self.camera
        #if len(self.snd_capture):
        #    self.logger.debug("Capture = " + self.snd_capture)
        #    self.core.capture_device = self.snd_capture
        if len(snd_playback):
            self.logger.debug("Playback = " + snd_playback)
            self.core.playback_device = snd_playback

        # Only enable PCMU and PCMA audio codecs
        #---------------------------------------
        for codec in self.core.audio_codecs:
            if codec.mime_type == "PCMA" or codec.mime_type == "PCMU":
                self.core.enable_payload_type(codec, True)
            else:
                self.core.enable_payload_type(codec, False)

        # Only enable VP8 video codec
        #---------------------------------------
        for codec in self.core.video_codecs:
            if codec.mime_type == "VP8":
                self.core.enable_payload_type(codec, True)
            else:
                self.core.enable_payload_type(codec, False)

        self.configure_sip_account(username, password)


    def signal_handler(self, signal, frame):
        self.logger.debug("Linphone SIGNAL signal_handler Tripped - Terminaing All Calls.")
        self.core.terminate_all_calls()
        self.quit = True


    def log_handler(self, level, msg):
        method = getattr(logging, level)
        method(msg)


    def call_state_changed(self, core, call, state, message):
        # substitutes for python3 app_utils functions to synch python27 and python3
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        folder = os.path.join(self.TOPDIR, 'static/python27/')
        def busyOff(ENVIRON, logger, folder):
            filelist = [ f for f in os.listdir(folder) ]
            for f in filelist:
                os.remove(os.path.join(folder, f))
        def busyOn(ENVIRON, logger, folder, filepath, stamp):
            file = stamp + '.busy'
            os.rename(filepath, os.path.join(folder, file))
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                
        self.logger.debug("Call_state_changed State = "" + str(state))
        if state == linphone.CallState.Idle:
            self.logger.debug("The call state is now Idle.")
        if state == linphone.CallState.OutgoingInit:
            self.outgoingCall = True
        if state == linphone.CallState.OutgoingRinging:
            self.outgoingCall = True
        if state == linphone.CallState.Error:
            self.logger.debug("A call state of linphone.CallState. Error was detected.")
            if self.outgoingCall == True:
                self.logger.debug("I was not able to connect your call. The other party may not be connected to the server.")
            else:
                self.logger.debug("There was some sort of error with the call.")
            #self.ENVIRON["listen"] = True
            busyOff(self.ENVIRON, self.logger, folder)
        if state == linphone.CallState.Released:
            self.outgoingCall = False
            #self.ENVIRON["listen"] = True
            busyOff(self.ENVIRON, self.logger, folder)
        if state == linphone.CallState.End:
            self.logger.debug("The active call was ended ")
            #self.ENVIRON["listen"] = True
            busyOff(self.ENVIRON, self.logger, folder)
        if state == linphone.CallState.IncomingReceived:
            #robotAI3 is python3 so create file as signal to interrupt processes
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            stamp = time.strftime("%y%m%d%H%M%S") 
            file = stamp + '.ask'
            filepath = os.path.join(folder, file)
            f = open(filepath, "w+")
            f.close()
            #wait and check if python3 process accepted 
            time.sleep(3)
            file = stamp + '.yes'
            filepath = os.path.join(folder, file)
            if not os.path.isfile(filepath):
                core.decline_call(call, linphone.Reason.Busy)
                busyOff(self.ENVIRON, self.logger, folder)
                return
            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            
            #Try to fetch caller details from our contact list
            id = call.remote_address_as_string
            self.logger.debug("Incoming call from " + id)
            caller = self.getCaller(id.replace("sip:", ""))
            try:
                CallName  = caller["Name"]
                CallWhite = caller["White"]
            except:
                CallWhite = False
            if CallWhite:
                #self.ENVIRON["listen"] = False
                busyOn(self.ENVIRON, self.logger, folder, filepath, stamp)
                self.logger.debug("Accepting call from " + call.remote_address_as_string)
                #self.MIC.play(self.core.ring)
                self.logger.debug("Giving snowboy 2 seconds to close the audio connection......")
                time.sleep(2)
                #self.MIC.say("I am accepting a call from " + CallName)

                if len(self.camera):
                    self.logger.debug("Camera = " + self.camera)
                    self.core.video_device = self.camera
                if len(self.snd_capture):
                    self.logger.debug("Capture = " + self.snd_capture)
                    self.core.capture_device = self.snd_capture

                params = core.create_call_params(call)
                core.accept_call_with_params(call, params)
            else:
                self.logger.debug("Rejecting call from " + call.remote_address_as_string)
                #self.MIC.say("Someone unknown is calling. I am rejecting the call.")
                core.decline_call(call, linphone.Reason.Declined)
                #self.ENVIRON["listen"] = True
                busyOff(self.ENVIRON, self.logger, folder)
                chat_room = core.get_chat_room_from_uri(self.admin)
                msg = chat_room.create_message(call.remote_address_as_string + ' tried to call')
                chat_room.send_chat_message(msg)
    

    def configure_sip_account(self, username, password):
        # Configure the SIP account
        proxy_cfg = self.core.create_proxy_config()
        proxy_cfg.identity_address = self.core.create_address('sip:{username}@sip.linphone.org'.format(username=username))
        proxy_cfg.server_addr = 'sip:sip.linphone.org;transport=tls'
        proxy_cfg.register_enabled = True
        self.core.add_proxy_config(proxy_cfg)
        auth_info = self.core.create_auth_info(username, None, password, None, None, 'sip.linphone.org')
        self.core.add_auth_info(auth_info)


    def getCaller(self, SoftPhone):
        filename = os.path.join(self.TOPDIR, "static/sqlite/robotAI.sqlite")
        result = {}
        try:
            con = sqlite3.connect(filename)
            cur = con.cursor()
        except:
            return result
        SQL = "SELECT FirstName, LastName, WhiteList, Mobile FROM Contacts where SoftPhone = '%s'" % SoftPhone
        self.logger.debug("Checking whitelist: " + SQL)
        cur.execute(SQL)
        rows = cur.fetchall()
        if not rows:
            return result
        row = rows[0]
        result.update({"Name" : str(row[0]) + " " + str(row[1]) , "White" : str(row[2]) , "Mobile" : str(row[3])})
        return result


    def create_call(self, personToCall):
        #self.MIC.say("I am calling " + personToCall)
        params = self.core.create_call_params(None)
        params.video_enabled = True
        print "***DEBUG*** Calling " + personToCall
        mycall = self.core.invite_with_params(personToCall, params)




    #Main sensor loop function that keeps checking for some sort of event or action that needs to be performed
    #-----------------------------------------------------------------------------------------------------------
    def run(self):
        cnt = 0
        while not self.quit:
            self.core.iterate()
            time.sleep(0.1)
            # reconnect to SIP server every 100 seconds so NAT port association does not change
            cnt += 1
            if cnt == 1000:
                self.logger.debug('------------------------------- Refreshing the connection to the SIP Server ---------------------------------')
                cnt = 0
                self.core.refresh_registers()
            # check if an outgoing call has been requested by call module
            if self.ENVIRON["callee"] and self.ENVIRON["listen"]:
                self.ENVIRON["listen"] = False
                time.sleep(2)
                self.core.capture_device = self.snd_capture
                self.logger.debug( "Creating a call to " + self.ENVIRON["callee"])
                self.create_call(self.ENVIRON["callee"])
                self.ENVIRON["callee"] = None



def doSensor(ENVIRON):
    cam = SecurityCamera(ENVIRON)
    cam.run()

    
    
# **************************************************************************
# This will only be executed when we run the sensor on its own
# **************************************************************************
if __name__ == "__main__":
    print("******** WARNING ********** Starting Sensor from __main__ procedure")

    TOPDIR = '/home/pi/robotAI3'
    filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
    cfg_general = getConfigData(TOPDIR, "General")
    ENVIRON = {}
    ENVIRON["listen"] = True                                                #flags whether listenLoop is able to 'listen' for inputs
    ENVIRON["screen"] = True                                                #flags whether screen view is able to be changed or not
    ENVIRON["motion"] = False                                               #flags whether to run motion sensor
    ENVIRON["security"] = False                                             #flags whether we are in security mode for motion sensor
    ENVIRON["topdir"] = TOPDIR                                              #master directory to work paths off
    ENVIRON["loglvl"] = logging.DEBUG                                       #store General config debug flag
    ENVIRON["version"]   = getConfig(cfg_general, "General_version")        #version of client code
    ENVIRON["api_url"]   = getConfig(cfg_general, "General_api_url")        #API root entry point
    ENVIRON["api_token"] = getConfig(cfg_general, "General_api_token")      #token for access
    ENVIRON["api_login"] = getConfig(cfg_general, "General_api_login")      #subscriber login
    ENVIRON["devicename"]  = getConfig(cfg_general, "General_devicename")   #Identity of this device (eg. Doorbell, Home Assistant, etc.)
    
    doSensor(ENVIRON)

