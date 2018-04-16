# -*- coding: utf-8-*-
import random

# ----------------------------------------------------------------------------
# High numbers push the priority of a module down the list.
# This module is the 'catch-all' so no module should be lower than this one!
#
# Note that previously brain.py sorted in DESC order, but this has been changed
# as it makes sense to default to high priority if none is given.
# -----------------------------------------------------------------------------
PRIORITY = 99



#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):

    messages = ["Sorry, I dont understand."]

    message = random.choice(messages)

    mic.say(message)


# returns true all the time (this is the 'catch-all' module)
# -------------------------------------------------------------------------
def isValid(text):
    return True
