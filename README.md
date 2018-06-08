# robotAI_python3
Upgrade of This Robot AI home automation and robotics platform to Python3. For more details reference the RobotAI website here https://thisrobotai.com/

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

sudo pip3 install requests  

sudo pip3 install pyserial    

# Instructions to install This Robot AI software

Download the code from this site and unzip. Rename the resulting folder RobotAI3.

Run the code by entering  "python3 robotAI3/robotAI.py" (assuming you renamed the directory robotAI3). While the software is running the configuration web pages will be accessible at http://localhost:5000 (or use the IP address of your device if accessing remotely).  

The first time the code runs it will create a fresh configuration database for you. Edit the configuration using the URL above. You will need a subscription from https://thisrobotai.com to leverage any of the services provided through the website.










