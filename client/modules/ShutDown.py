# -*- coding: utf-8-*-
import re
import random
from client.app_utils import getYesNo
import os
"""
===============================================================================================
This module allows the user to shut down OR reboot the Robot AI module and the Pi
Usage: 'Shut Down'
Copyright: Lee Matthews 2016
===============================================================================================
"""


#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    if 'SHUTDOWN' in text or 'SHUT DOWN' in text:
        questn = 'Do you want me to shut down?'
        command = 'sudo shutdown now -h'
        output = ["Great! I would like to hang around for a little longer.", "OK then. I will stay and help out.",
                  "That's good. I don't want to sleep just yet.", "Thank you. I will wait for your next command."]
        oktext = 'OK, shutting down'
    else:
        questn = 'Do you want me to reboot?'
        command = 'sudo shutdown -r now'
        output = ["Sorry. I must have misunderstood you", "OK, sorry. I thought you asked me to reboot.",
                  "Alright, maybe later then."]
        oktext = 'OK, rebooting now'

    # now confirm operation and either execute or quit
    mic.say(questn)
    resp = getYesNo(mic, questn)
    if resp == "YES":
        mic.say(oktext)
        os.system(command)
    else:
        message = random.choice(output)
        mic.say(message)


# returns true if the stated command contains the right keywords
# -------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\bshut down|shutdown|reboot|restart\b', text, re.IGNORECASE))
