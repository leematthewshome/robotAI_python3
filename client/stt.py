# -*- coding: utf-8-*-
import os
import json
import logging
import requests
import base64
import time


# STT implementation using the robotAI community server API
#---------------------------------------------------------------------
class robotAI_stt():

    def __init__(self, ENVIRON):
        self.logger = logging.getLogger(__name__)
        self.logger.level = ENVIRON["loglvl"]
        self.api_apiurl = ENVIRON["api_url"]
        self.api_login  = ENVIRON["api_login"]
        self.api_token  = ENVIRON["api_token"]
        self.version    = ENVIRON["version"]
        # Check which API to use to the main URL entry point
        if "Google" in ENVIRON["stt_api"]:
            self.logger.debug("Using Google (paid) API for speech to text")
            self.api_apiurl = os.path.join(self.api_apiurl, 'stt')
        else:
            self.logger.debug("Using WitAI (free) API for speech to text")
            self.api_apiurl = os.path.join(self.api_apiurl, 'wit')

    def transcribe(self, fp):
        # prepare speech for sending
        data = fp.read()
        speech_content_bytes = base64.b64encode(data)
        speech_content = speech_content_bytes.decode('utf-8')
        #print(speech_content)

        jsonpkg = {'subscriberID': self.api_login,
                  'token': self.api_token,
                  'version': self.version,
                  'content': speech_content
                  }

        # Send recorded speech to API for conversion to text
        #--------------------------------------------------------------------------------------------------
        transcribed = []
        headers = {'Content-Type': 'application/json'}
        try:
            r = requests.post(self.api_apiurl, data=json.dumps(jsonpkg), headers=headers, verify=True)
            if r.status_code == 200:
                try:
                    text = r.json()["results"][0]["alternatives"][0]["transcript"]
                    transcribed.append(text.upper())
                except:
                    self.logger.critical('Could not parse response from API.', exc_info=True)
                    transcribed.append('APIERROR1')
                    print(r.content)
            else:
                self.logger.critical('Request failed with response: %r', r.text, exc_info=True)
                transcribed.append('APIERROR2')
        # handle where the request times out for some reason
        except requests.exceptions.Timeout:
            transcribed.append('APIERROR3')
        # handle all other exceptions
        except:
            transcribed.append('APIERROR4')


        print('API Transcribed: %r', transcribed)
        return transcribed


