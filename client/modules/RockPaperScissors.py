# -*- coding: utf-8-*-
import re 
import random
from client.app_utils import getYesNo

# Set priority. A higher value means a lower priority. 
PRIORITY = 2


# variables for scoring
userWins = 0
robotWins = 0
rps = ['ROCK', 'PAPER', 'SCISSORS']


#default function to handle the request for this module
#-------------------------------------------------------------------------
def handle(text, mic, ENVIRON):

    # create function for scoring
    def score(user, robot):
        global userWins
        global robotWins
        userWins += user
        robotWins += robot
        mic.say("So far you have %s wins and I have %s wins." % (userWins, robotWins))

    # create function for scoring
    def finish():
        global userWins
        global robotWins
        if userWins > robotWins:
            mic.say("You beat me! That was fun. Maybe I will have better luck next time.")
        else:
            mic.say("Yay! I beat you. Perhaps you will win next time.")

    # function to play each game
    def play():
        mic.say('OK, lets go... one two three')
        # get a random number and then ROCK, PAPER or SCISSORS
        num = random.randint(0, 2)
        res = rps[num]

        # get user feedback
        mic.say('what do you have?')
        text = mic.activeListenToAllOptions()
        text = text[0]

        if 'ROCK' in text.upper():
            if res == 'ROCK':
                mic.say("It's a draw")
                score(0, 0)
            elif res == 'PAPER':
                mic.say('I win. I had paper.')
                score(0, 1)
            else:
                mic.say('You win. I had scissors.')
                score(1, 0)
        # allow for piper as well as paper as sometimes stt is wrong
        elif 'PAPER' in text.upper() or 'PIPER' in text.upper() or 'PAYPAL' in text.upper():
            if res == 'ROCK':
                mic.say('You win. I had rock.')
                score(1, 0)
            elif res == 'PAPER':
                mic.say("It's a draw.")
                score(0, 0)
            else:
                mic.say('I win. I had scissors.')
                score(0, 1)
        # allow for citizens as well as paper as sometimes stt is wrong
        elif 'SCISSORS' in text.upper() or 'CITIZENS' in text.upper() or 'SIZZLES' in text.upper():
            if res == 'ROCK':
                mic.say('I win. I had rock.')
                score(0, 1)
            elif res == 'PAPER':
                mic.say('You win. I had paper.')
                score(1, 0)
            else:
                mic.say("It's a draw.")
                score(0, 0)
        else:
            mic.say('I didnt hear you say ROCK, PAPER or SCISSORS')

    init = True
    # continue looping until user quits
    while True:
        if init:
            userWins = 0
            robotWins = 0
            init = False
            play()
        else:
            question = "Do you want to play again?"
            mic.say(question)
            resp = getYesNo(mic, question)
            if resp == "NO":
                finish()
                break
            else:
                play()

    
# returns true if the stated command contains the right keywords
#-------------------------------------------------------------------------
def isValid(text):
    return bool(re.search(r'\brock|paper|scissors\b', text, re.IGNORECASE))
    
    

        
   
   
   
   
   
   
   
   
