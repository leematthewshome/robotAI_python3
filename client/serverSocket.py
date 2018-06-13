#!/usr/bin/python
"""
===============================================================================================
Sensor to connect to the Robot AI website and listen for communications from the server
Uses the Socket.io framework via https://pypi.org/project/socketIO-client/

Note that only one process at a time can use microphone. If it is busy then the browser will not 
open with access to the mic and camera.  ENVIRON["listen"] manages this.
===============================================================================================
"""
import logging
import subprocess
import os
import time
#allow for running listenloop either in isolation or via robotAI.py
try:
    from client.app_utils import getConfigData, getConfig
except:
    from app_utils import getConfigData, getConfig
from socketIO_client import SocketIO, LoggingNamespace

#======================================================
# serverSocket class
#======================================================
class serverSocket(object):

    def __init__(self, ENVIRON, SENSORQ, MIC):
        self.Mic = MIC
        self.ENVIRON = ENVIRON
        TOPDIR = ENVIRON["topdir"]
        
        #get the module configuration info
        filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
        config = getConfigData(TOPDIR, "WebSocket")
        if "ERROR" in config:
            print("serverSocket: Error getting Config: " + config["ERROR"])
            debugFlag = 'TRUE'
        else:
            debugFlag = getConfig(config, "WebSocket_2debug")
            self.URL = getConfig(config, "WebSocket_socketurl")
        
        #Set debug level based on details in config DB
        self.logger = logging.getLogger(__name__)
        logging.basicConfig()
        if debugFlag=='TRUE':
            self.logger.level = logging.DEBUG
        else:
            self.logger.level = logging.INFO

        
    # Connect to server and listen for messages. Socket.IO library will reconnect if conn lost
    #============================================================================================
    def run(self):

        def on_connect():
            self.logger.debug('You have connected')

        def on_disconnect():
            self.logger.debug('You have been disconnected')

        def on_reconnect():
            self.logger.debug('You have reconnected')

        def on_join_room(*args):
            print('join_room', args)

        def on_conferGo(*args):
            self.logger.debug('Mesage to go to conference received.')
            #get the data that was passed in
            pwd = args[0]['passwd']
            url = args[0]['url']
            user = args[0]['user']
            whitelist = False
            
            #check the password is valid and the user type
            
            #this should be handled by the queue!!!!
            self.ENVIRON["listen"] = False
            time.sleep(1)
            if whitelist:
                result=subprocess.Popen(["chromium-browser", "--use-fake-ui-for-media-stream", url], stdout=subprocess.PIPE)
            else:
                result=subprocess.Popen(["chromium-browser", "--use-fake-ui-for-media-stream", url], stdout=subprocess.PIPE)

                
        def on_conferKill(*args):
            self.logger.debug('Mesage to kill conference instance received.')
            result=subprocess.Popen(['killall', 'chromium-browse'], stdout=subprocess.PIPE)
            self.ENVIRON["listen"] = True
            
        # Connect to the server 
        TOKEN = self.ENVIRON["api_token"]
        SUBSCR = self.ENVIRON["api_login"]
        USRNAME = self.ENVIRON["devicename"]

        qstring = {'token': TOKEN, 'subscriber': SUBSCR, 'user': USRNAME}
        self.logger.debug('Attempting to connect with %s - %s - %s' % (TOKEN, SUBSCR, USRNAME))
        socketIO = SocketIO(self.URL, 443, params=qstring)

        # Set up custom listeners
        socketIO.on('connect', on_connect)
        socketIO.on('disconnect', on_disconnect)
        socketIO.on('reconnect', on_reconnect)
        socketIO.on('join_room', on_join_room)
        socketIO.on('conferGo', on_conferGo)
        socketIO.on('conferKill', on_conferKill)
        socketIO.wait()

     

 
# ==========================================================================
# Function called by main robotAI process to run this sensor
# ==========================================================================
def doSensor(ENVIRON, SENSORQ, MIC):
    socket = serverSocket(ENVIRON, SENSORQ, MIC)
    socket.run()



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
    
    doSensor(ENVIRON, SENSORQ, MIC)

