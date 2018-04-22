# -*- coding: utf-8-*-
import re
import datetime
from client.app_utils import uzbl_goto, getConfigData, sendToRobotAPI
import logging
import os
from cgi import escape

import webbrowser

"""
===============================================================================================
Weather Module Utilising RobotAI API and website
Usage: 'What is the weather for [Today|Tomorrow|Friday|etc]'
Copyright: Lee Matthews 2016
===============================================================================================
"""

#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):
    weather = Weather(text, mic, ENVIRON)
    weather.getWeather()


#returns true if the stated command contains the right keywords
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\b(weathers?|temperature|forecast|outside|hot|' +
                          r'cold|rain)\b', text, re.IGNORECASE))


#class for fetching the weather forecast
#=========================================================================
class Weather(object):

    def __init__(self, text, mic, ENVIRON):
        self.Mic = mic
        self.Text = text
        self.api_token = ENVIRON["api_token"]
        self.api_login = ENVIRON["api_login"]
        self.api_url = ENVIRON["api_url"]
        TOPDIR = ENVIRON["topdir"]
        logLevel = ENVIRON["loglvl"]
        self.logger = logging.getLogger(__name__)
        self.logger.level = logLevel
        MyConfig = getConfigData(TOPDIR, "Weather")
        if "ERROR" in MyConfig or MyConfig == None:
            self.Mic.say("Sorry, I could not access the weather configuration data. I cannot complete the task")
            return
        else:
            self.weather_loc = MyConfig["Weather_location"]
            self.weather_fmt = MyConfig["Weather_format"]
            self.loc = self.weather_loc.split(",")
        self.ENVIRON = ENVIRON


    #default function to handle the request for this module
    #-------------------------------------------------------------------------
    def getWeather(self):
        #work out what day we need data for
        reqDay = self.getRequestedDay(self.Text)
        if reqDay is None:
            self.Mic.say("I did not hear which day you wanted so I will fetch the weather for today")
            todayDt = datetime.date.today()
            reqDay = todayDt.strftime("%A").upper()

        town = self.loc[0].strip()
        cntry = self.loc[1].strip()

        #set json package to send to API
        jsonpkg = {'subscriberID': self.api_login,
                   'token': self.api_token,
                   'town' : town,
                   'cntry' : cntry,
                   'day' : reqDay,
                   'fmt' : self.weather_fmt,
        }
        api_url = os.path.join(self.api_url, 'weather')
        response = sendToRobotAPI('GET', api_url, jsonpkg, self.Mic, self.logger, self.ENVIRON)
        voicetext = str(response["text"])

        if voicetext:
            voicetext = self.replaceAcronyms(voicetext)
            # Send data to webpage in text variable as DAY_Town_Country_format
            text = escape(reqDay + "_" + town + "_" + cntry + "_" + self.weather_fmt)
            token = escape(self.api_token)
            subscr = escape(self.api_login)
            URL = "http://localhost/auth_redir.php?page=%s&subscr=%s&token=%s&text=%s" % ("weath", subscr, token, text)
            uzbl_goto(URL)
            #webbrowser.open(URL)
            self.Mic.say(voicetext)


    # Replaces some commonly-used acronyms for an improved verbal weather report.
    # -------------------------------------------------------------------------
    def replaceAcronyms(self, text):
        words = {
            'N ': 'north ',
            'NNE ': 'north north east ',
            'NE ': 'north east ',
            'NE ': 'east north east ',
            'E ': 'east ',
            'ESE ': 'east south east ',
            'SE ': 'south east ',
            'SSE ': 'south south east ',
            'S ': 'south ',
            'SSW ': 'south south west ',
            'SW ': 'south west ',
            'WSW ': 'west south west ',
            'W ': 'west ',
            'WNW ': 'west north west ',
            'NW ': 'north west ',
            'NNW ': 'north north west ',
        }
        for key, value in  words.iteritems():
            text = text.replace(key, value)
        text = text.replace("F.", "degrees fahrenheit")
        text = text.replace("C.", "degrees celsius")
        text = text.replace("mph", "miles per hour")
        text = text.replace("km/h", "kilometers an hour")
        text = text.replace("cm.", "centimeters")
        text = text.replace("mm.", "millimeters")
        return text


    #work out what day to get the weather for
    #-------------------------------------------------------------------------
    def getRequestedDay(self, text):
        #work out next 7 dates
        todayDt = datetime.date.today()
        tmrwDt =  datetime.date.today()+ datetime.timedelta(days=1)
        nextDt =  datetime.date.today()+ datetime.timedelta(days=2)
        day3dt =  datetime.date.today()+ datetime.timedelta(days=3)
        day4dt =  datetime.date.today()+ datetime.timedelta(days=4)
        day5dt =  datetime.date.today()+ datetime.timedelta(days=5)
        day6dt =  datetime.date.today()+ datetime.timedelta(days=6)
        #get days from those dates
        today = todayDt.strftime("%A").upper()
        tmrw = tmrwDt.strftime("%A").upper()
        next = nextDt.strftime("%A").upper()
        day3 = day3dt.strftime("%A").upper()
        day4 = day4dt.strftime("%A").upper()
        day5 = day5dt.strftime("%A").upper()
        day6 = day6dt.strftime("%A").upper()
        #now return the day we should get the description for
        if "TODAY" in text:
            return today
        elif "TOMORROW" in text:
            return tmrw
        elif today in text:
            return today
        elif tmrw in text:
            return tmrw
        elif next in text:
            return next
        elif day3 in text:
            return day3
        elif day4 in text:
            return day4
        elif day5 in text:
            return day5
        elif day6 in text:
            return day6
        else:
            return None


