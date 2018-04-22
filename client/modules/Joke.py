# -*- coding: utf-8-*-
import re
#import the chat bot module where we handle conversation
from ChatBot import chatBot


def handle(text, mic, ENVIRON):
    bot = chatBot(text, mic, ENVIRON)
    bot.doChat("JOKE1-0")


def isValid(text):
    return bool(re.search(r'\bjoke\b', text, re.IGNORECASE))
