# -*- coding: utf-8-*-
import re
import os
import datetime
import logging
from client.app_utils import uzbl_goto, getYesNo, sendToRobotAPI

"""
===============================================================================================
"Chatty Robot" Module For interactive conversation, jokes, and other purposes
Usage: Called by various modules (joke, MotionLoop, etc) as well as triggered via sensors
  - Trigger via CHATBOT and the text will be fetched from online database
  - Trigger via CHATFILE and the text will be fetched from the file location instead
  
Author: Lee Matthews 2017
===============================================================================================
"""

# Set priority to an average level
# -----------------------------------------------------------------------------
PRIORITY = 1


#default function to handle the request for this module
def handle(text, mic, ENVIRON):
    bot = chatBot(text, mic, ENVIRON)
    chatid = ''
    # get the chat ID or filepath that was sent 
    if ':' in text:
        arr = text.split(":")
        chatid = arr[1]
    # call the relevant process based on the trigger word
    if 'CHATFILE' in text.upper():
        bot.doFile(chatid)
    else:
        bot.doChat(chatid)



#returns true if the stated command contains the right keywords
def isValid(text):
    return bool(re.search(r'\bchatbot|chatfile\b', text, re.IGNORECASE))



# class for creating the interactive chat bot
#=========================================================================
class chatBot(object):

    # initialise the chat object
    # ------------------------------------------------------
    def __init__(self, text, mic, ENVIRON):
        self.Mic = mic
        self.Text = text
        self.ENVIRON = ENVIRON
        self.api_token = ENVIRON["api_token"]
        self.api_login = ENVIRON["api_login"]
        self.api_url = ENVIRON["api_url"]
        self.logger = logging.getLogger(__name__)
        self.logger.level = ENVIRON["loglvl"]


    # fetch the chat sequence and then loop through results
    # ------------------------------------------------------
    def doFile(self, filePath):
        import json
        #test filePath is valid
        if not os.path.isfile(filePath):
            self.Mic.say('Uh Oh. I was supposed to say something, but cannot find the file.')
            return
        #open the file and get chat list from JSON document
        try:
            with open(filePath) as json_file:  
                response = json.load(json_file)
                self.logger.debug(response)
                rows = response["list"]
        except:
            self.logger.warning("Failed to load JSON file for CHATFILE process")
            return
        #loop through and call doChatItem for each 
        for row in rows:
            resp = self.doChatItem(row['text'], row['funct'])



    # fetch the chat sequence and then loop through results
    # ------------------------------------------------------
    def doChat(self, chatid="0-GREET-0"):
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # temporary fix for 2 part chat IDs (until API fixed)
        arr = chatid.split('-')
        if len(arr) == 2:
            chatid = '0-' + chatid
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        self.logger.debug("Fetching JSON from API for starting point of %s" % chatid) 
        # get results from robotAI API using given ID
        jsonpkg = {'subscriberID': self.api_login,
                   'token': self.api_token,
                   'chatid' : chatid,
                   }
        api_url = os.path.join(self.api_url, 'chat')
        response = sendToRobotAPI('GET', api_url, jsonpkg, self.Mic, self.logger, self.ENVIRON)
        self.logger.debug(response)
        rows = response["list"]
        if not rows or len(rows) == 0:
            self.logger.debug("No chat text found for %s" % chatid)
            self.Mic.say('Sorry, I could not work out what to say.')
        else:
            # loop through each item in the chat text returned
            for row in rows:
                resp = self.doChatItem(row['text'], row['funct'])
                #print 'RESPONSE = %s' % resp
                # if we need to select a path then loop through all options and search for response
                nText = row['next']
                if '|' in nText:
                    options = nText.split("|")
                    for item in options:
                        row = item.split("-")
                        rtxt = row[0]
                        if rtxt.upper() in resp:
                            self.doChat(item)


    # handle (eg. say) a single chat item
    # ------------------------------------------------------
    def doChatItem(self, text, funct):
        self.logger.debug("running doChatItem for function %s and text '%s'" % (funct, text))
        resp = ''
        text = self.enrichText(text)
        self.Mic.say(text)
        # if there is a function mentioned run it and get the results
        if funct:
            funct = funct.strip()
            if funct == "yesNo":
                resp = getYesNo(self.Mic, text)
            elif funct == "pauseListen":
                resp = self.pauseListen(False)
            elif funct == "callWeather":
                resp = self.callWeather()
            else:
                self.logger.debug("No handler for function %s" % funct)
                self.Mic.say('Sorry, I dont know what to do about %s' % funct)
        return resp


    # update the chat text with any context sensitive values
    # ------------------------------------------------------
    def enrichText(self, text):
        # replace the keyword 'dayPart' with relevant replacement
        if 'dayPart' in text:
            now = datetime.datetime.now()
            hour = now.hour
            if hour < 12:
                dayPart = "Morning"
            elif hour < 18:
                dayPart = "Afternoon"
            else:
                dayPart = "Evening"
            text = text.replace('dayPart', dayPart)
        # insert any custom text replacement logic after this line
        # -- here --
        # now return the adjusted text to the calling function
        return text


    # function to fetch the weather and speak / display
    # ------------------------------------------------
    def callWeather(self):
        from Weather import Weather
        weather = Weather("WEATHER TODAY", self.Mic, self.ENVIRON)
        weather.getWeather()
        return "OK"


    # function to pause in conversation or get a response
    # ----------------------------------------------------------
    def pauseListen(self, sendstt):
        text = self.Mic.activeListenToAllOptions(SEND=sendstt)
        return text

