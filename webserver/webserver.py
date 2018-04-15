"""
===============================================================================================
Webserver module 
Used to create a web site through which the user can edit setup to configure functionality

Set the HOTWORD_PATH variable to point to the folder where hotword files are located
===============================================================================================
"""
from flask import Flask
from flask import render_template
from flask import request
import os
import sqlite3


class webServer(object):

    def __init__(self, ENVIRON, SENSORQ, MIC):
        #setup global variables
        self.websrvApp = Flask(__name__)
        self.TOPDIR = '/home/pi/robotAI/'
        self.HOTWORD_PATH = '/home/pi/robotAI/static/hotwords/'


    def run(self):
        #default page for configuration
        @self.websrvApp.route('/')
        @self.websrvApp.route('/index')
        @self.websrvApp.route('/index.html')
        def index():
            return render_template('index.html')
            
        self.websrvApp.run(host= '0.0.0.0', debug=True)



# ==========================================================================
# Run the webserver
# ==========================================================================
if __name__ == "__main__":
    ENVIRON = 0
    SENSORQ = 0
    MIC = 0
    webApp = webServer(ENVIRON, SENSORQ, MIC)
    webApp.run()
    
