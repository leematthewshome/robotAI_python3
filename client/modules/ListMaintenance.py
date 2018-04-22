#!/usr/bin/env python2
# -*- coding: utf-8-*-
import re
import os
from cgi import escape 
from client.app_utils import uzbl_goto, getYesNo, sendToRobotAPI
import uuid
import logging
"""
===============================================================================================
List Management Module - to maintain items in list and display list in browser
Copyright: Lee Matthews 2017
Usage:  'Add [some thing] to the [list name] list'
        'Clear/Delete the [list name] list'
        'Display/show/fetch the [list name] list'
ToDo:   Allow for more flexible verbal commands...eg. "Put Milk on the shopping list"
===============================================================================================
"""


#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    slist = ShopList(text, mic, ENVIRON)
    # Work out which action we need to implement by looking for keywords
    # Note that 'Add' often gets interpreted as 'And'
    if "ADD" in text or text[:3] == "AND":
        slist.addItem()
    # Look for delete, clear or reset in the command
    elif bool(re.search(r'\bdelete|clear|reset\b', text, re.IGNORECASE)):
            slist.clearList()
    # Assume we just need to display the shopping list then
    else:
        slist.getList()


# returns true if the stated command contains the right keywords
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\bto do|shopping|list\b', text, re.IGNORECASE))


#class for all functions related to managing the shopping list
#=========================================================================
class ShopList(object):

    def __init__(self, text, mic, ENVIRON):
        self.Mic = mic
        self.Text = text
        self.api_token = ENVIRON["api_token"]
        self.api_login = ENVIRON["api_login"]
        self.api_url = ENVIRON["api_url"]
        self.id = str(uuid.uuid4())
        logLevel = ENVIRON["loglvl"]
        self.logger = logging.getLogger(__name__)
        self.logger.level = logLevel
        self.ENVIRON = ENVIRON


    #default function to handle the request for this module
    #-------------------------------------------------------------------------
    def getList(self, voice=True):
        #respond to the user
        if voice == True:
            voicetext = "Fetching the lists now."
            self.Mic.say(voicetext)
        text = escape(self.Text)
        token = escape(self.api_token)
        subscr = escape(self.api_login)
        URL = "http://localhost/auth_redir.php?page=%s&subscr=%s&token=%s&text=%s" % ("list", subscr, token, text)
        #print URL
        uzbl_goto(URL)


    #function to process adding an item to shoping list
    #-------------------------------------------------------------------------
    def addItem(self, repeat=False):
        # Remeove ADD or AND from the front of text
        if self.Text[:3] == "ADD" or self.Text[:3] == "AND" :
            text = self.Text[3:]
        else:
            text = self.Text

        # Try to get the listName assuming the format is "ADD [descript] TO THE [listName] LIST"
        listName = None
        r_obj = re.search('TO THE (.*)LIST', text)
        if r_obj is not None:
            listName = r_obj.group(0).replace('TO THE ', '').replace(' LIST', '')
            known1 = re.search('TO THE (.*)LIST', text).group(0)
        else:
            # If that failed try based on format of "ADD [descript] TO [listName] LIST"
            r_obj = re.search('TO (.*)LIST', text)
            if r_obj is not None:
                listName = r_obj.group(0).replace('TO ', '').replace(' LIST', '')
                known1 = re.search('TO (.*)LIST', text).group(0)

        # If neither worked then we have no list. Else get the item to add by removing known text
        if listName is None:
            self.Mic.say("Sorry, I could not work out what list you wanted.")
            return
        else:
            descript = text.replace(known1, "")
        if len(descript.replace(" ", "")) == 0:
            self.Mic.say("Sorry, I could not work out what you wanted me to add.")
            return

        # Confirm interpretation with the user
        if repeat==False:
            voicetext = "Did you ask to add %s to the %s list?" % (descript, listName)
        else:
            voicetext = "Add " + descript + "?"
        self.Mic.say(voicetext)
        resp = getYesNo(self.Mic, voicetext)
        if resp == "NO":
            self.Mic.say("Sorry I misunderstood you. Please start again.")
            return
        else:
            api_url = os.path.join(self.api_url, 'list')
            api_url = os.path.join(api_url, self.id)
            #remove apostrophe, as that can mess up the SQL
            descript = descript.replace("'", "")
            jsonpkg = {'subscriberID': self.api_login,
                       'token': self.api_token,
                       'listName': listName,
                        'descript': descript,
                       }
            response = sendToRobotAPI('PUT', api_url, jsonpkg, self.Mic, self.logger, self.ENVIRON)
            result = response["result"]
            if result == 'OK':
                voicetext = "%s has been added." % (descript)
                self.Mic.say(voicetext)
            self.getList(False)


    # Function to clear just checked or optionally all items from the shopping list
    # -------------------------------------------------------------------------
    def clearList(self):
        logger = self.logger
        mic = self.Mic
        text = self.Text
        api_url = os.path.join(self.api_url, 'list')
        #print api_url
        # Try to get the listName assuming the format is "[action] THE [listName] LIST"
        listName = None
        r_obj = re.search('THE (.*)LIST', text)
        if r_obj is not None:
            listName = r_obj.group(0).replace('THE ', '').replace(' LIST', '')
            known1 = re.search('THE (.*)LIST', text).group(0)

        # If we have no list. Else get the item to add by removing known text
        if listName is None:
            self.Mic.say("Sorry, I could not work out what you are referring to.")
            return
        else:
            descript = text.replace(known1, "")
        if len(descript.replace(" ", "")) == 0:
            self.Mic.say("Sorry, I could not work out what you are referring to.")
            return

        # check if the user wants to clear checked items from the shopping list
        voicetext = "Do you want to clear the checked items?"
        self.Mic.say(voicetext)
        resp = getYesNo(self.Mic, voicetext)
        if resp == "NO":
            self.Mic.say("OK. I will not clear the list.")
            return
        # check if the user wants to clear unchecked items as well
        voicetext = "Do you want to clear unchecked items as well?"
        self.Mic.say(voicetext)
        resp = getYesNo(self.Mic, voicetext)
        if resp == "YES":
            status = 1
        else:
            status = 0

        #set json package to send to API to delete row
        jsonpkg = {'subscriberID': self.api_login,
                   'token': self.api_token,
                   'listName': listName,
                   'status': status,
                   }
        response = sendToRobotAPI('DELETE', api_url, jsonpkg, self.Mic, self.logger)
        result = response["result"]
        if result == 'OK':
            voicetext = "The %s list has been cleared." % (listName)
            self.Mic.say(voicetext)
        self.getList(False)

