# robotAI_python3
Upgrade of This Robot AI home automation and robotics platform to Python3. For more details reference the RobotAI website here https://thisrobotai.com/

This is a work in progress. 


# Instructions to install necessary pre-requisites and libraries

--start by updating your environment

sudo apt-get update

sudo apt-get upgrade

--Note that some of these libraries and applications might already be installed on your image. If so then no problem.

--install required libraries for audio onto raspberry pi

sudo apt-get install python3-pyaudio python-dev python3-dev libportaudio-dev libasound2-dev libatlas-base-dev bison -y

sudo pip3 install pyaudio

--install text to speech software 

sudo apt-get install espeak flite libttspico0 libttspico-utils libttspico-data -y

--install software for playing music

sudo apt-get install mplayer -y

--install flask, which is required for local web pages to configure system

sudo pip3 install flask

--install socketIO_client, which is only required for the module that maintains a socket connection to the server

sudo pip3 install socketIO-client

--install open-cv (computer vision), which is only required for the motion sensor module

sudo pip3 install imutils

sudo pip3 install opencv-python

sudo apt-get install libatlas-base-dev

sudo apt-get install libjasper-dev

sudo apt-get install libqtgui4

sudo apt install libqt4-test

sudo apt-get install python3-pyqt5

--install pythion libraries leveraged by various modules

sudo pip3 install PyDictionary

sudo pip3 install requests  

sudo pip3 install pyserial   

# Instructions to install This Robot AI software

Download the code from this site and unzip. Rename the resulting folder RobotAI3.

Run the code by entering  "python3 robotAI3/robotAI.py" (assuming you renamed the directory robotAI3). While the software is running the configuration web pages will be accessible at http://localhost:5000 (or use the IP address of your device if accessing remotely).  

The first time the code runs it will create a fresh configuration database for you. Edit the configuration using the URL above. You will need a subscription from https://thisrobotai.com to leverage any of the services provided through the website. That will include Speech To Text (STT) capabilities so you can give commands to This Robot AI verbally. Refer to instructions here: https://thisrobotai.com/setup/configuration.php however note that they relate to the older version of the platform and may differ slightly. If you dont want to leverage the online APIs (provided at a minor cost) but still want to give verbal commands, then you will need to leverage your own STT setup. One option is to use your own Google account. Code for that is here: https://github.com/leematthewshome/robotAI_GoogleSTT 










