# -*- coding: utf-8-*-
import re
import os
"""
===============================================================================================
This module sends the client to a chat room using chrome
Usage:  Should be triggered by system using text '??'

===============================================================================================
"""

# Set priority lower so other commands dont trigger accidentally. Eg. "Its TIME for an UPDATE"
PRIORITY = 1


#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    URL = 'https://appear.in/leematt2'

    #kill any pre-existing chromium browser instance
    os.system('killall chromium-browser')
    #start new instance with 
    os.system('chromium-browser --use-fake-ui-for-media-stream %s' % URL)

    
    
# returns true if the stated command contains the right keywords
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\bchat\b', text, re.IGNORECASE))
