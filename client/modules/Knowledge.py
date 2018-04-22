# -*- coding: utf-8-*-
"""
===============================================================================================
Knowledge Module Utilising This Robot AI API
Usage: 'How far is it to the moon'
Copyright: Lee Matthews 2017
NOTE: Priority set to large number (low priority) so that questions like 'what is the time?'
      are captured by the right module. This module should be just above the unclear module
===============================================================================================
"""
import re
import os
from client.app_utils import uzbl_goto, sendToRobotAPI, getYesNo
import logging


# Set priority low (using a high number) as other modules should default first
#  for example, "what is the time" should be handled by time.py NOT this module
# -----------------------------------------------------------------------------
PRIORITY = 9


#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    # get necessary info from the environment and setup logging
    api_token = ENVIRON["api_token"]
    api_login = ENVIRON["api_login"]
    api_url = ENVIRON["api_url"]
    logLevel = ENVIRON["loglvl"]
    logger = logging.getLogger(__name__)
    logger.level = logLevel

    # confirm with the user tat we should proceed
    voicetext = "Would you like me to look that question up on the web?"
    mic.say(voicetext)
    resp = getYesNo(mic, voicetext)
    if resp == "NO":
        mic.say("Sorry if I misunderstood you.")
        return
    else:
        #set json package to send to API
        jsonpkg = {'subscriberID': api_login,
                'token': api_token,
                'text' : text,
        }
        api_url = os.path.join(api_url, 'know')
        response = sendToRobotAPI('GET', api_url, jsonpkg, mic, logger, ENVIRON)
        rows = response["list"]
        # the list element should be a list of {'title' : value, 'text' : value} pairs
        if not rows or len(rows) == 0:
            mic.say('Sorry, I could not find any results for that question.')
            mic.say('Perhaps try a more specific question.')
        else:
            cnt = 0
            entries = len(rows)
            if rows[0]['title'] == 'Input interpretation' or rows[0]['title'] == 'Input':
                subject = rows[0]['text']
                cnt = 1
                num = entries - cnt
                mic.say('I found %s records about %s' % (num, subject))
            else:
                mic.say('I found %s records ' % (entries))
            # loop through entries one at a time
            mic.say('The first records is... ')
            while cnt < entries:
                mic.say(rows[cnt]['title'])
                mic.say(rows[cnt]['text'])
                cnt = cnt + 1
                next = rows[cnt]['title']
                mic.say('The next record is %s ' % (next))
                voicetext = "Would you like me to continue?"
                mic.say(voicetext)
                resp = getYesNo(mic, voicetext)
                if resp == "NO":
                    mic.say("OK.")
                    break


#returns true if the stated command begins with any of the phrases
#-------------------------------------------------------------------------
def isValid(text):
    # allow for "TELL ME" or "CAN YOU TELL ME" or "PLEASE TELL ME"
    if bool(re.search(r'\bTELL ME\b', text, re.IGNORECASE)):
        return True
    # test for question indicator at front of text string
    if bool(re.search(r'^WHO', text, re.IGNORECASE)):
        return True
    if bool(re.search(r'^WHAT', text, re.IGNORECASE)):
        return True
    if bool(re.search(r'^WHEN', text, re.IGNORECASE)):
        return True
    if bool(re.search(r'^HOW', text, re.IGNORECASE)):
        return True
    return False
