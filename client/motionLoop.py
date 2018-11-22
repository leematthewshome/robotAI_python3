#!/usr/bin/env python
"""
===============================================================================================
Sensor for detecting motion using Open CV
Author: Lee Matthews 2018
Open computer vision (Open CV) libraries required 
Motion sensing will only run if ENVIRON['motion'] == True. ENVIRON['security'] determines whether 
motion raises an alarm or not. If not true then detected motion might only trigger a random event 
or conversation for example.
The directory path "/static/images" must exist under the robotAI root directory
===============================================================================================
"""
import datetime
import imutils
import time
import cv2
import os
import logging
import json
#allow for running listenloop either in isolation or via robotAI.py
try:
    from client.app_utils import getConfig, getConfigData, sendToRobotAPI
except:
    from app_utils import getConfig, getConfigData, sendToRobotAPI


class motionLoop(object):

    def __init__(self, ENVIRON, SENSORQ, MIC):
        self.Mic = MIC
        self.ENVIRON = ENVIRON
        self.SENSORQ = SENSORQ
        self.TOPDIR = ENVIRON["topdir"]
        filename = os.path.join(self.TOPDIR, "static/sqlite/robotAI.sqlite")
        if os.path.isfile(filename):
            config = getConfigData(self.TOPDIR, "Motion")
            if "ERROR" in config:
                print ("MotionLoop: Error getting Config: " + config["ERROR"])
                debugFlag = 'TRUE'
            else:
                debugFlag = getConfig(config, "Motion_2debug")

        #Set debug level based on details in config DB
        self.logger = logging.getLogger(__name__)
        logging.basicConfig()
        if debugFlag=='TRUE':
            self.logger.level = logging.DEBUG
        else:
            self.logger.level = logging.INFO

        # setup variables for motion detection process
        #-------------------------------------------------
        self.detector = getConfig(config, "Motion_detectMethod")
        self.framesCheck = 10                           
        self.motionChat = getConfig(config, "Motion_motionChat")
        self.securitychat = getConfig(config, "Motion_securityChat")
        self.imagePath = os.path.join(self.TOPDIR, "static/images/")
        # try to get the integer values from config
        try:
            self.chatDelay = int(getConfig(config, "Motion_waitChat"))
            self.delay = int(getConfig(config, "Motion_waitDetect"))
            self.min_area = int(getConfig(config, "Motion_minarea"))
            self.detectPin = int(getConfig(config, "Motion_detectPin"))
        except:
            self.Mic.say("There is a problem with one of the configuration values, so I am using my defaults.")
            self.chatDelay = 0
            self.delay = 10
            self.min_area = 500
            self.detectPin = 0
            
        # variables required to pre-fetch the security chat JSON
        self.api_token = ENVIRON["api_token"]
        self.api_login = ENVIRON["api_login"]
        self.api_url = ENVIRON["api_url"]
        self.chatfile = os.path.join(self.TOPDIR, "static/securityChat.json")

        # set lastChat so it triggers a chat if motion detected after startup
        self.lastChat = datetime.datetime.today() - datetime.timedelta(minutes=self.chatDelay)
        # set non to blank as we handle that below using len(self.motionChat)
        if not self.motionChat:
            self.motionChat = ''
        self.logger.debug("Chat triggered by motion is %s" % self.motionChat)
        self.logger.debug("Minimum area for movement is %s" % self.min_area)
        self.logger.debug("Delay between detection events %s seconds" % self.delay)
        self.logger.debug("Delay between chat events %s minutes" % self.chatDelay)
        self.logger.debug("Path for saving images is %s" % self.imagePath)
        
        # delete jpg files from images directory when starting sensor
        #self.logger.debug("Deleting old files in %s" % self.imagePath)
        #filelist = [ f for f in os.listdir(self.imagePath) ]
        #for f in filelist:
        #    os.remove(os.path.join(self.imagePath, f))


        
    # Get security chat json and save as file. This speeds up response for security alert
    #============================================================================================
    def createFile(self):
        chatid = self.securitychat
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # temporary fix for 2 part chat IDs (until API fixed)
        arr = chatid.split('-')
        if len(arr) == 2:
            chatid = '0-' + chatid
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if len(self.securitychat) > 0:
            jsonpkg = {'subscriberID': self.api_login,
                       'token': self.api_token,
                       'chatid' : chatid,
                       }
            api_url = os.path.join(self.api_url, 'chat')
            response = sendToRobotAPI('GET', api_url, jsonpkg, self.Mic, self.logger, self.ENVIRON)
            with open(self.chatfile, 'w') as outfile:
                json.dump(response, outfile)



    # Loop to keep checking every 5 seconds whether we should turn motion detection on
    #============================================================================================
    def runLoop(self):
        self.logger.debug("Starting Motion Sensor Loop")
        # pre-fetch the security chat text 
        self.createFile()
        while True:
            self.logger.debug("ENVIRON for Motion and Security : %s and %s" % (self.ENVIRON["motion"], self.ENVIRON["security"]))
            if self.ENVIRON["motion"]:
                # let the user know security mode is coming
                if self.ENVIRON["security"]:
                    self.Mic.say("Security camera will be enabled in %s seconds. Any detected motion will raise an alarm." % str(self.delay))
                # run the motion detection logic based on detector chosen
                if self.detector == 'Camera':
                    self.detectMotion()
                else:
                    self.detectHuman()
            else:
                time.sleep(5)

                
                
    # Steps to perform when Security Alert Triggered
    # ============================================================================================
    def securityWarn(self, camera):
    
        # function to save single image when motion detected
        def snapshot(camera, num):
            file = time.strftime("%y%m%d%H%M%S") + '-' + str(num) + '.jpg'
            fullpath = self.imagePath + file
            self.logger.debug("Saving image to %s" % fullpath)
            (grabbed, frame) = camera.read()
            cv2.imwrite(fullpath, frame)
            time.sleep(0.5)
            return file
        
        # function to save video when motion detected
        def recordVideo(camera, sec):
            file = time.strftime("%y%m%d%H%M%S") + '.avi'
            fullpath = self.imagePath + file
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(fullpath, fourcc, 20.0, (640,480)) 
            start_time = time.time()
            while( int(time.time() - start_time) < sec):
                ret, frame = camera.read()
                if ret==True:
                    #frame = cv2.flip(frame, 0)
                    out.write(frame)
                    #cv2.imshow('frame',frame)
                else:
                    break
            return file

        #old code to take 3 snapshots
        #f1 = snapshot(camera, 1)
        #f2 = snapshot(camera, 2)
        #f3 = snapshot(camera, 3)
        #command = 'SECURITYCAM ,%s,%s,%s' % (f1, f2, f3)

        file = recordVideo(camera, 3)
        command = 'SECURITYWARN ,%s' % (file)
        self.logger.debug("Posting %s to Queue" % command)
        self.ENVIRON["listen"] = False
        self.SENSORQ.put(['brain', command])

        # trigger Chat then record more video for reaction (if chat ID configured)
        if len(self.securitychat) > 0:
            command = 'CHATFILE:%s:%s' % (self.chatfile, self.securitychat)
            self.logger.debug("Posting %s to Queue" % command)
            self.ENVIRON["listen"] = False
            self.SENSORQ.put(['brain', command])
        
        #record more video while chat is being executed
        file = recordVideo(camera, 10)
        command = 'SECURITYVIDEO ,%s' % (file)
        self.logger.debug("Posting %s to Queue" % command)
        self.ENVIRON["listen"] = False
        self.SENSORQ.put(['brain', command])


        
    # Work out what we need to do when motion detected
    # ============================================================================================
    def detectionEvent(self, lastAlert, camera):
        # Check lastAlert to see if we need to trigger a new Alert for the motion
        curDTime = datetime.datetime.today()
        self.logger.debug("Motion detected at %s " % curDTime)
        diff = curDTime - lastAlert
        if (diff.seconds) < self.delay:
            self.logger.debug("Motion delay has not expired. %s seconds remaining." % diff.seconds)                
        else:
            lastAlert = curDTime
            self.logger.debug("Motion detected at %s and motion delay has expired" % curDTime)
            
            # Check listen loop to ensure brain is not busy with an event
            if self.ENVIRON["listen"] == True:
                command = None
                # if in security camera mode then capture video
                #----------------------------------------------
                if self.ENVIRON["security"] == True:
                    self.logger.debug("Security mode is enabled so trigger security alert")
                    self.securityWarn(camera)
                # else check whether we should begin a chat loop
                #----------------------------------------------
                else:
                    self.logger.debug("Checking if we should trigger a chat")
                    diff = 0
                    # only trigger a chat if we have a delay and a chat ID
                    if self.chatDelay > 0 and len(self.motionChat) > 0:
                        diff = curDTime - self.lastChat
                    if diff > datetime.timedelta(minutes=self.chatDelay):
                        self.lastChat = curDTime
                        command = 'CHATBOT:%s' % self.motionChat
                        self.ENVIRON["listen"] = False
                        self.logger.debug("Posting %s to Queue" % command)
                        self.SENSORQ.put(['brain', command])
        # pre-fetch the security chat text to regenerate file
        self.createFile()
        return lastAlert

        
        
    # Loop to detect motion using the PIR Sensor
    # ============================================================================================
    def detectHuman(self):
        self.logger.debug("Using PIR sensor on pin %s to detect motion" % self.detectPin)
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.detectPin, GPIO.IN, GPIO.PUD_UP)
        camera = cv2.VideoCapture(0)
        lastAlert = datetime.datetime.today()
        frames = 0
        
        # loop continuously cnd check GPIO Pin for motion
        while True:
            if GPIO.input(self.detectPin) == GPIO.LOW:
                self.logger.debug("No motion detected yet.")
            else:
                lastAlert = self.detectionEvent(lastAlert, camera)

            frames += 1
            # check the ENVIRON when frame count reaches check point
            if frames > self.framesCheck:
                self.logger.debug("Checking to see if we should stop detecting motion")
                frames = 0
                if not self.ENVIRON["motion"]:
                    self.logger.debug("Time to stop detecting motion")
                    # cleanup the camera quit function
                    camera.release()
                    break
                    
            #pause before next loop
            time.sleep(0.3)

            
            
    # Loop to detect motion using the camera
    # ============================================================================================
    def detectMotion(self):
        self.logger.debug("Starting to detect Motion")
        # define feed from camera
        camera = cv2.VideoCapture(0)
        time.sleep(1)
        # initialize variables used by the motion sensing
        firstFrame = None
        lastAlert = datetime.datetime.today()
        frames = 0
        
        # loop over the frames of the video feed and detect motion
        while True:
            # if we are busy processing a job then skip motion until we are done
            # (the listen flag is our default indicator that brain is processing something)
            if self.ENVIRON["listen"] == False:
                continue
                
            # grab the current frame and initialize the occupied/unoccupied text
            self.logger.debug("Getting another frame. ENVIRON listen = %s" % self.ENVIRON["listen"])
            (grabbed, frame) = camera.read()
            frames += 1

            # resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # if the first frame is None, initialize it
            if firstFrame is None:
                firstFrame = gray
                continue

            # compute the absolute difference between the current frame and first frame
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
            # Update the reference frame
            firstFrame = gray
            # dilate the thresholded image to fill in holes, then find contours on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)
            (image, cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # loop over the contours
            for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < self.min_area:
                    continue
                #motion must be detected, see if we need to trigger a new Alert for the motion
                lastAlert = self.detectionEvent(lastAlert, camera)

            # check the ENVIRON when frame count reaches check point
            if frames > self.framesCheck:
                self.logger.debug("Checking to see if we should stop detecting motion")
                frames = 0
                if not self.ENVIRON["motion"]:
                    self.logger.debug("Time to stop detecting motion")
                    # cleanup the camera quit function
                    camera.release()
                    break



#---------------------------------------------------------------------------
# Function called by main robotAI procedure to start this sensor
#---------------------------------------------------------------------------
def doSensor(ENVIRON, SENSORQ, MIC):
    loop = motionLoop(ENVIRON, SENSORQ, MIC)
    loop.runLoop()


    
# **************************************************************************
# This will only be executed when we run the sensor on its own for debugging
# **************************************************************************
if __name__ == "__main__":
    print("******** WARNING ********** Starting Sensor from __main__ procedure")
    from multiprocessing import Queue
    SENSORQ = Queue()

    import testSensor
    ENVIRON = testSensor.createEnviron()
    MIC = testSensor.createMic(ENVIRON, 'pico-tts')
    
    doSensor(ENVIRON, SENSORQ, MIC)