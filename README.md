# robotAI_python3
Upgrade of This Robot AI home automation and robotics platform to Python3. For more details reference the RobotAI website here https://thisrobotai.com/

This is a work in progress. Available python and raspbian packages seem to change over time. These instructions worked for Raspbian Buster as at 14/07/2019

--Note that some of these libraries and applications might already be installed on your image. If so then no problem.

# Instructions to install necessary pre-requisites and libraries

--start by updating your environment

sudo apt-get update

sudo apt-get upgrade

-- upgrade PIP to latest version

wget https://bootstrap.pypa.io/get-pip.py

sudo python3 get-pip.py

--Installation of prerequisites for snowboy hotword detector

sudo apt-get install python-pyaudio python3-pyaudio sox portaudio19-dev

pip3 install pyaudio

sudo apt-get install libatlas-base-dev

--install required libraries for audio onto raspberry pi

sudo apt-get install python-dev libportaudio-dev libasound2-dev  bison -y

sudo apt-get install espeak -y

--install pico text to speech software (seems no longer available for latest raspbian)

#sudo apt-get install espeak flite libttspico0 libttspico-utils libttspico-data -y

--install flask, which is required for local web pages to configure system

sudo pip3 install flask

--install software for playing music

sudo apt-get install mplayer -y

--install socket client, for the (IN DEVELOPMENT) websocket sensor

sudo pip3 install socketIO-client

--install open-cv (computer vision) required for the motion sensor module

sudo pip3 install imutils

sudo pip install opencv-contrib-python

--install pythion libraries leveraged by various modules

sudo pip3 install PyDictionary

sudo pip3 install requests  

sudo pip3 install pyserial   


# Instructions to install This Robot AI software

Download the code from this site and unzip. Rename the resulting folder RobotAI3.

Run the code by entering  "python3 robotAI3/robotAI.py" (assuming you renamed the directory robotAI3). While the software is running the configuration web pages will be accessible at http://localhost:5000 (or use the IP address of your device if accessing remotely).  

The first time the code runs it will create a fresh configuration database for you. Edit the configuration using the URL above. You will need a subscription from https://thisrobotai.com to leverage any of the services provided through the website. That will include Speech To Text (STT) capabilities so you can give commands to This Robot AI verbally. Refer to instructions here: https://thisrobotai.com/setup/configuration.php however note that they relate to the older version of the platform and may differ slightly. If you dont want to leverage the online APIs (provided at a minor cost) but still want to give verbal commands, then you will need to leverage your own STT setup. One option is to use your own Google account. Code for that is here: https://github.com/leematthewshome/robotAI_GoogleSTT 










