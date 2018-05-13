"""
===============================================================================================
Sensor to connect to the Robot AI website and listen for communications from the server
Uses the Socket.io framework via https://pypi.org/project/socketIO-client/

TODO - set logging based on config / 
===============================================================================================
"""
import logging
import subprocess
import os
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
        self.TOPDIR = ENVIRON["topdir"]
        self.TOKEN = ENVIRON["api_token"]
        self.SUBSCR = ENVIRON["api_login"]
        self.USRNAME = ENVIRON["devicename"]
        
        #get the module configuration info
        filename = os.path.join(self.TOPDIR, "static/sqlite/robotAI.sqlite")
        config = getConfigData(self.TOPDIR, "WebSocket")
        if "ERROR" in config:
            print("TimerLoop: Error getting Config: " + config["ERROR"])
            debugFlag = 'TRUE'
        else:
            debugFlag = getConfig(config, "WebSocket_2debug")
            self.URL = getConfig(config, "WebSocket_socketurl")
        
        #Set debug level based on details in config DB
        if debugFlag=='TRUE':
            self.logger = logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
        else:
            self.logger = logging.getLogger('socketIO-client').setLevel(logging.INFO)
        logging.basicConfig()

        
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
            if whitelist:
                result=subprocess.Popen(["chromium-browser", "--use-fake-ui-for-media-stream", url], stdout=subprocess.PIPE)
            else:
                result=subprocess.Popen(["chromium-browser", "--use-fake-ui-for-media-stream", url], stdout=subprocess.PIPE)

                
        def on_conferKill(*args):
            self.logger.debug('Mesage to kill conference instance received.')
            result=subprocess.Popen(['killall chromium-browser'], stdout=subprocess.PIPE)
            
            
        # Connect to the server 
        qstring = {'token': self.TOKEN, 'subscriber': self.SUBSCR, 'user': self.USRNAME}
        socketIO = SocketIO(self.URL, 443, params=qstring)

        # Set up custom listeners
        socketIO.on('connect', on_connect)
        socketIO.on('disconnect', on_disconnect)
        socketIO.on('reconnect', on_reconnect)
        socketIO.on('join_room', on_join_room)
        socketIO.on('conferGo', on_conferGo)
        socketIO.on('conferKill', on_conferGo)
        socketIO.wait()

     


 
# ==========================================================================
# Function called by main robotAI process to run this sensor
# ==========================================================================
def doSensor(ENVIRON, SENSORQ, MIC):
    socket = serverSocket(ENVIRON, SENSORQ, MIC)
    socket.run()



"""
if __name__ == "__main__":
    print("Starting socketListener from __main__ procedure")
    # Allow to manually run the sensor in isolation using the below
    class Mic(object):
        def say(self, text):
            print(text)
        def activeListenToAllOptions(self):
            print("running activeListenToAllOptions")
        
    #set up ENVIRON object
    ENVIRON = {}
    ENVIRON["topdir"] = "/home/pi/robotAI3"
    ENVIRON["api_token"] = 'H1G2F3D4R5T6H7K8H9F0DSAOYTREDBHH'        
    ENVIRON["api_login"] = 'lee.matthews.home'
    ENVIRON["devicename"] = 'Whatever'
    #setup QUEUE object
    from multiprocessing import Process, Manager, Queue
    SENSORQ = Queue()
    #setup MIC object
    MIC = Mic()
    doSensor(ENVIRON, SENSORQ, MIC)
"""
