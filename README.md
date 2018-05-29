# robotAI_python3
robotAI home automation and robotics platform. For more details reference the RobotAI website here https://thisrobotai.com/

This is a work in progress. 


# Instructions to install necessary pre-requisites and libraries

--Note that some of these libraries and applications might already be installed on your image. If so then no problem.

--install required libraries for audio onto raspberry pi

sudo apt-get install python3-pyaudio python-dev libportaudio-dev libasound2-dev libatlas-base-dev bison -y

sudo pip3 install pyaudio

--install text to speech software 

sudo apt-get install espeak flite libttspico0 libttspico-utils libttspico-data -y

--install software for playing music

sudo apt-get install mplayer -y

--install flask, which is required for local web pages to configure system

sudo pip3 install flask

--install pythion libraries leveraged by various modules

sudo pip3 install PyDictionary

sudo pip3 install requests  #this fails...need to work out where used

sudo pip3 install serial    #this fails...will impact robot operation

sudo pip3 install pytz      #this fails...need to eliminate need for it in time.py







