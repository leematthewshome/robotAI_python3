# -*- coding: utf-8-*-
import sqlite3
import os
import time
#import subprocess as sub
import re
# used by uzbl_goto
import glob
# For function sendToRobotAPI
import requests, json


#Function to extract a set of global variables in a dictionary
#----------------------------------------------------------------
def getConfigData(TOPDIR, sGroup, logger=None):
    filename = os.path.join(TOPDIR, "static/sqlite/robotAI.sqlite")
    if logger:
        logger.debug("Getting Config values from " + filename)
    # *********************** TO DO - need to check if file exists somehow ****************
    try:
        con = sqlite3.connect(filename)
        cur = con.cursor()
    except:
        #return error status
        return {'ERROR': 'Could not connect to DB file'}
    #now get configuration items
    SQL = "SELECT category, code, value FROM ConfigValues where category = '%s'" % sGroup
    if logger:
        logger.debug("SQL = " + SQL)
    cur.execute(SQL)
    rows = cur.fetchall()
    #Test whether we have no rows from config
    if not rows:
        return {'ERROR': 'No rows returned by query'}
    myConfig = {}
    #loop through rows and define variables
    i = 0
    for row in rows:
        row = rows[i]
        myConfig.update({str(row[0]) + '_' + str(row[1]) : str(row[2])})
        i += 1
    return myConfig


#Function to get a config entry without returning an error
#----------------------------------------------------------------
def getConfig(config, item):
    try:
        return config[item]
    except:
        return None


#Lee function to open page in Kiosk Browser
#----------------------------------------------------------------
def uzbl_goto(URL):
    try:
        # check if uzbl browser has already been opened
        list = glob.glob('/tmp/uzbl_fifo*')
        for filepath in list:
            command = "echo 'uri " + str(URL) + "' > %s " % filepath
            #sub.Popen(command, shell=True)
            os.system(command)
    except:
        print("No instance of UZBL Browser found")


#Lee function to check for a Yes or No. Allows for one loop if
#no answer. Question should be posed to user in calling function
#---------------------------------------------------------------
def getYesNo(mic, questn):
    # function to see if the response contained yes
    def getResponse(texts):
        str = ""
        for text in texts:
            str += text
        return str

    # Active listen for a response from the speaker
    texts = mic.activeListenToAllOptions(SEND=True)
    # if no response was received we get an error so use try block
    try:
        resp = getResponse(texts)
    except:
        resp = "WHATEVER"
    # first check for yes or no
    if bool(re.search(r'\byes\b', resp, re.IGNORECASE)) == True:
        return "YES"
    elif bool(re.search(r'\bno\b', resp, re.IGNORECASE)) == True:
        return "NO"
    else:
        mic.say("Sorry, I did not hear a yes or no. " + questn)
        texts = mic.activeListenToAllOptions(SEND=True)
        try:
            resp = getResponse(texts)
        except:
            resp = "WHATEVER"
    # second check for yes or no
    if bool(re.search(r'\byes\b', resp, re.IGNORECASE)) == True:
        return "YES"
    else:
        return "NO"


# Called by Weather.py TimerLoopHandle.py Knowledge.py 
# Function to submit data to the robotAI website and receive results back
# --------------------------------------------------------------------------
def sendToRobotAPI(method, api_url, jsonpkg, mic, logger, ENVIRON=None):
    headers = {'Content-Type': 'application/json'}
    try:
        if method == 'DELETE':
            res = requests.delete(api_url, data=json.dumps(jsonpkg), headers=headers, verify=True)
        elif method == 'PUT':
            res = requests.put(api_url, data=json.dumps(jsonpkg), headers=headers, verify=True)
        else:
            res = requests.post(api_url, data=json.dumps(jsonpkg), headers=headers, verify=True)
        status = res.status_code
    # handle where the request times out for some reason
    except requests.exceptions.Timeout:
        status = -1
    # handle all other exceptions
    except:
        status = -2

    # Check results returned by the API
    if status == 200:
        try:
            result = res.json()["result"]
            if result == "ERR":
                text = res.json()["errmsg"]
                logger.debug('There was an error. The response was, ' + text, exc_info=True)
                mic.say('Something went wrong. The robot A I responded with, ' + text)
            elif result == 'OK':
                # Check the response for any messages from the server (eg. re subscription expiry)
                #---------------------------------------------------------------------------------------------
                nodes = res.json()
                if "message" in nodes:
                    if ENVIRON is not None:
                        ENVIRON["command"] = nodes['message']
                    logger.debug('Alert Received: %s' % res.json()['message'])

                #return the JSON data back to the calling function
                #---------------------------------------------------------------------------------------------
                return res.json()
            else:
                mic.say('An unrecognised response was received from the robot A I website.')
        except:
            logger.critical('Could parse response from API.', exc_info=True)
            mic.say('Sorry. I was unable to read the response from the robot A I website.')
    elif status == -1:
        logger.critical('Could not access the API. The http request timed out.', exc_info=True)
        mic.say('Hmmn. A timely response was not received from the robot A I website. Perhaps try again.')    
    elif status == -2:
        logger.critical('Could not access the API. The was an unhandled problem with the http request.', exc_info=True)
        mic.say('Sorry, there was a problem accessing the Robot A I website. Perhaps try again.')    
    else:
        logger.critical('Could not access the API. Response was %s.' % res.status_code, exc_info=True)
        mic.say('Sorry. I was not able to access the robot A I website to perform the task.')
