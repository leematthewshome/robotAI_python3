# robotAI_python3
robotAI home automation and robotics platform

This is a work in progress. I am updating my own platform to make it Pythin3 compatible and to add more functionality.


Loose instructions to install into virtual environment


#if using python 3.4 install virtual env
#-----------------------------------------------------
sudo apt-get install python3.4-dev python3.4-venv


#create virtual environment named 'virtual'
#-----------------------------------------------------
mkdir robotAI3
cd robotAI3
python3.4 -m venv virtual

#activate the virtual environment and add flask
#-----------------------------------------------
source virtual/bin/activate
pip3 install flask

#install other required modules
#-----------------------------------------------
pip3 install requests
pip3 install serial
*ensure the libportaudio dependencies are also installed
pip install --allow-unverified=pyaudio pyaudio




