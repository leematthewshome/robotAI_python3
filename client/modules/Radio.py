# -*- coding: utf-8-*-
import re
import os
from urllib2 import URLError
import logging
from client.app_utils import uzbl_goto, sendToRobotAPI
"""
===============================================================================================
This module allows the user to play internet radio stations
Usage:  'Play Blues Radio'
        'Play classical Radio'
        'Stop the radio'
        'Turn Off the Radio'
Copyright: Lee Matthews 2016
===============================================================================================
"""

#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    api_token = ENVIRON["api_token"]
    api_login = ENVIRON["api_login"]
    api_url = ENVIRON["api_url"]
    logger = logging.getLogger(__name__)
    logger.level = ENVIRON["loglvl"]

    #ToDo add a check for the mplayer program first

    # Check if the user asked to stop the radio
    if "STOP" in text or "OFF" in text:
        mic.say("Stopping the radio.")
        os.system('killall mplayer')
    else:
        # get results from robotAI API using search phrase
        jsonpkg = {'subscriberID': api_login,
                   'token': api_token,
                   'text' : text,
                   }
        api_url = os.path.join(api_url, 'radio')
        response = sendToRobotAPI('GET', api_url, jsonpkg, mic, logger, ENVIRON)
        stations = response["list"]
        if not stations or len(stations) == 0:
            logger.debug("No stations found for '%s'" % text)
            mic.say('Sorry, I was unable to find a radio station with the search terms you gave me.')
            mic.say('Ensure you say one of the keywords saved with your stations on the Robot A I website.')
        else:
            pickRadio(stations, mic, logger)


# returns true if the stated command contains the right keywords
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\bradio\b', text, re.IGNORECASE))



# function to prompt the user to pick a station if multiple received
#-------------------------------------------------------------------------
def pickRadio(stations, mic, logger):
    cnt = len(stations)
    if cnt == 1:
        stn = stations[0]["station"]
        url = stations[0]["url"]
    else:
        mic.say("I found %s stations based on your request." % cnt)
        max = 1
        if cnt > 5:
            mic.say("I will list the first 5 for you and you can tell me which number you want")
        else:
            mic.say("I will list them for you and you can tell me which number you want")
        for row in stations:
            logger.debug(row)
            mic.say("Number %s. %s" % (max, row["station"]))
            max = max + 1
            if max > 5:
                break
        mic.say("OK. Tell me which number you want me to play.")
        res = mic.activeListenToAllOptions()
        text = res[0]
        num = getNum(text)
        if num and num <= cnt:
            num -= 1
            stn = stations[num]["station"]
            url = stations[num]["url"]
        else:
            mic.say("Sorry, I didnt get which number you wanted. Please start again if you still want to play the radio.")
            return
    # If the command was not to stop the radio then lets start it
    playRadio(stn, url, mic, logger)


# function to play a particular radio station
#-------------------------------------------------------------------------
def playRadio(stn, url, mic, logger):
    import subprocess
    try:
        # kill any existing processes first
        os.system('killall mplayer')
        # now start a new process to play the selected station
        mic.say("OK. Playing %s." % stn)
        command = 'mplayer %s' % url
        subprocess.Popen(command, shell=True)
    except:
        mic.say("Sorry, I was unable to play the selected radio station.")


# return the spoken index number to select a station
#-------------------------------------------------------------------------
def getNum(txt):
    if bool(re.search(r'\btwo|second|2\b', txt, re.IGNORECASE)) == True:
        return 2
    if bool(re.search(r'\bthree|third|3\b', txt, re.IGNORECASE)) == True:
        return 3
    if bool(re.search(r'\bfour|fourth|4\b', txt, re.IGNORECASE)) == True:
        return 4
    if bool(re.search(r'\bfive|fifth|5\b', txt, re.IGNORECASE)) == True:
        return 5
    # check for ONE last in case use says 'THE SECOND ONE'
    if bool(re.search(r'\bone|first|1\b', txt, re.IGNORECASE)) == True:
        return 1

