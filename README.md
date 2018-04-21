# robotAI_python3
robotAI home automation and robotics platform. For more details reference the RobotAI website here https://thisrobotai.com/

This is a work in progress. I am updating my own platform to make it Python3 compatible and to add more functionality.

# Instructions to install into virtual environment - Raspbian Jessie used

--If using python 3.4 install virtual env

  sudo apt-get install python3.4-dev python3.4-venv

--create virtual environment named 'virtual' using python 3.4

  mkdir robotAI3
  
  cd robotAI3
  
  python3.4 -m venv virtual

--whenever installing python modules into the virtual environment ensure you activate first

source virtual/bin/activate


# Instructions to install necessary libraries

--install required libraries for audio onto raspberry pi

sudo apt-get install python3-pyaudio python-dev libportaudio-dev libasound2-dev libatlas-base-dev bison -y

pip install --allow-unverified=pyaudio pyaudio

--install text to speech software 

sudo apt-get install espeak flite libttspico0 libttspico-utils libttspico-data -y

--install software for playing music

sudo apt-get install mplayer -y

--install these python modules (activate virtual environment first if using)

pip3 install flask

--install pythion libraries leveraged by various modules

///this one seems to error : pip3 install semantic

pip3 install pytz

pip3 install PyDictionary

* note that some errors seem to result when installing falsk but these seem to be OK

pip3 install requests

pip3 install serial







