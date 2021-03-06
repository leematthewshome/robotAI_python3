# -*- coding: utf-8-*-
import datetime
import re
from client.app_utils import uzbl_goto


# Set priority lower so other commands dont trigger accidentally. Eg. "Its TIME for an UPDATE"
PRIORITY = 5


# default function to handle the request for this module
# -------------------------------------------------------------------------
def handle(text, mic, ENVIRON):

    #Open relevant page in UZBL browser
    if ENVIRON["screen"]:
        uzbl_goto("http://localhost/ShowDateTime.html")

    now = datetime.datetime.now()
    response = convertTime(now)
    
    mic.say("It is %s right now." % response)



# returns true if the stated command contains the right keywords
# -------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\btime\b', text, re.IGNORECASE))


        
# create time text from datetime object
def convertTime(now):
    hr = now.time().hour
    # work out minutes text
    min = now.time().minute
    if min < 10:
        minTxt = '0' + str(min)
    else:
        minTxt = str(min)
    # work out AM or PM and hour text
    if hr > 12 or hr == 0:
        suffix = 'PM'
        if hr == 0:
            hr = 12
        else:
            hr = hr - 12
    else:
        suffix = 'AM'
    
    hrTxt = str(hr)
    result = '%s %s %s' % (hrTxt, minTxt, suffix)
    return result
    
