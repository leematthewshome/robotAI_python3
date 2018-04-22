# -*- coding: utf-8-*-
import datetime
import re
import os
from semantic.dates import DateService
from pytz import timezone
from client.app_utils import uzbl_goto
from client.app_utils import getConfigData


# Set priority lower so other commands dont trigger accidentally. Eg. "Its TIME for an UPDATE"
PRIORITY = 5


# default function to handle the request for this module
# -------------------------------------------------------------------------
def handle(text, mic, ENVIRON):

    #Open relevant page in UZBL browser
    if ENVIRON["screen"]:
        uzbl_goto("http://localhost/ShowDateTime.html")

    tz = getTimezone()
    now = datetime.datetime.now(tz=tz)
    service = DateService()
    response = service.convertTime(now)

    mic.say("It is %s right now." % response)



# returns true if the stated command contains the right keywords
# -------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\btime\b', text, re.IGNORECASE))



# Returns the timezone from config
def getTimezone():
    config = getConfigData(os.getcwd(), "General")
    try:
        return timezone(config['General_zone'])
    except:
        return None

