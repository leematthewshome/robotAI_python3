# -*- coding: utf-8-*-
"""
===============================================================================================
Server Message Module
Usage: Triggered by server messages (in message node) returned with API calls. 
       A message might be returned with an API call if your subscription is about to expire for example
Copyright: Lee Matthews 2017

!!!! ToDo Move to using the chat functionality in future, so it can be multi language and more conversational
===============================================================================================
"""
import re


# Priority set to high as 'SERVERMSG' unlikely to be spoken and we dont want 
# server messages to accidentally trigger other modules
# -----------------------------------------------------------------------------
PRIORITY = 1


#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    # remove the trigger text from the string
    text = text.upper()
    text = text.replace("SERVERMSG", "")
    text = text.lstrip()
    
    #ToDo Move to using the chat functionality in future, so it can be multi language and more conversational
    mic.say(text)


#returns true if the stated command begins with any of the phrases
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\bservermsg\b', text, re.IGNORECASE))
