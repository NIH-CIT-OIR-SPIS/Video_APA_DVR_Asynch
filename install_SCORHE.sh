#!/bin/bash
# This script is used to setup the SCORHE environment

SCORHE_DIR=$(pwd)
echo "Installing SCORHE dependencies..."

echo "Installing updates and upgrades..."
sudo apt-get -y update && \
sudo apt-get -y upgrade && \
sudo apt install -y net-tools

# Check if python3 is installed
if ! [ -x "$(command -v python3)" ]; then
  echo 'Error: python3 is not installed.' >&2
  echo 'Installing python3...'
  sudo apt-get -y install python3
fi

# Check if pip3 is installed
if ! [ -x "$(command -v pip3)" ]; then
  echo 'Error: pip3 is not installed.' >&2
  echo 'Installing pip3...'
  sudo apt-get -y install python3-pip
fi

sudo apt-get -y install python3-pyqt5 && \
pip3 install numpy opencv-python paramiko typing matplotlib pygo pygi requests

sudo apt-get -y install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio

cd ~/Downloads/

wget https://download.tsi.telecom-paristech.fr/gpac/release/2.2.1/gpac_2.2.1-rev0-gb34e3851-release-2.2_amd64.deb

sudo apt install -y ./gpac_2.2.1-rev0-gb34e3851-release-2.2_amd64.deb  # Or whatever you have corresponding to the correct release

cd $SCORHE_DIR

echo "\n\nSCORHE dependencies installed."

