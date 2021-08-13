#!/bin/bash

PYTHON_VERSION="3.4"
PYTHON_EXEC="python$PYTHON_VERSION"
TMP_DIR="/tmp"
PYTHON_SRC_DIR="$TMP_DIR/Python-3.6.5"
INSTALL_DIR="/tmp/scorhe-install"


####
# Installing  libraries (python, gstreamer, PyQt)
if ! which ${PYTHON_EXEC} 2>/dev/null >/dev/null ; then
    echo "Installing python $PYTHON_VERSION...."
    # not in python 3.6, gotta install new python
    tar -zxf "$INSTALL_DIR/Python-3.6.5.tgz" -C ${TMP_DIR} --touch
    pushd .
    cd ${PYTHON_SRC_DIR}
    ./configure
    # using 4 cores instead of 1 makes the compilation only take 16 minutes
    # instead of 30.
    make -j4
    sudo make install
    popd
    # if stuff stays its in temp which should get deleted on reboot.
    rm -rf ${PYTHON_SRC_DIR}
    echo "Finished installing python $PYTHON_VERSION."
fi

# check if PyQt5 is installed
#if ! ${PYTHON_EXEC} -c "import PyQt5" 2>/dev/null >/dev/null ; then
#    # PyQt5 is not installed, install from source. Also sip.
#
#    if ! ${PYTHON_EXEC} -c "import sip" 2>/dev/null >/dev/null; then
#        echo "Installing sip 4.19..."
#        tar -zxf "$INSTALL_DIR/sip-4.19.12.tar.gz" -C ${TMP_DIR} --touch
#        pushd .
#        cd "$TMP_DIR/sip-4.19.12"
#        sudo ${PYTHON_EXEC} configure.py --sip-module PyQt5.sip
#        make -j4
#        sudo make install
#        popd
#        echo "Finished installing sip"
#    fi
#    echo "Installing PyQt5...."
#    tar -zxf "$INSTALL_DIR/PyQt5_gpl-5.11.2.tar.gz" -C ${TMP_DIR} --touch
#    pushd .
#    cd "$TMP_DIR/PyQt5_gpl-5.11.2"
#    sudo ${PYTHON_EXEC} configure.py --qmake /usr/lib/arm-linux-gnuabihf/qt5/bin/qmake
#    make -j4
#    sudo make install
#    popd
#    echo "Finished installing PyQt5."
#fi

# check if picamera is installed
if ! ${PYTHON_EXEC} -c "import picamera" 2>/dev/null >/dev/null ; then
    # PyQt5 is not installed, install via wheel
    echo "Installing picamera...."
    sudo ${PYTHON_EXEC} -m pip install -U "$INSTALL_DIR/picamera-1.13.tar.gz" >/dev/null
    echo "Finished installing picamera."
fi

# installing linux packages from offline is hard
# let's just hope we'll never have to update it.

####
# RPi configuration files.

echo "Misc configs..."
# check if hdmi is setup correctly
# right now commenting and letting the pi figure out its hdmi setup
if grep -q '^hdmi' /boot/config.txt ; then
    sudo sed -i 's/^\(hdmi\)/#\1/g' /boot/config.txt
fi

# check if bluetooth and wifi are disabled
if ! grep -q '^dtoverlay=pi3-disable-bt' /boot/config.txt ; then
    echo "dtoverlay=pi3-disable-bt" | sudo tee -a /boot/config.txt
fi
if ! grep -q '^dtoverlay=pi3-disable-wifi' /boot/config.txt ; then
    sudo echo "dtoverlay=pi3-disable-wifi" | sudo tee -a /boot/config.txt
fi

# check if xserver command is setup correctly. if not, fix it.
# now pi doesn't sleep and cursor is hidden.
if grep -q '^#xserver-command=' /etc/lightdm/lightdm.conf ; then
    sudo sed -i 's/^#\?\(xserver-command=\).*$/\1X -nocursor -s 0 -dpms/' /etc/lightdm/lightdm.conf
fi

# check if keyboard is setup as a US keyboard.
if ! grep -q '^XKBLAYOUT="us"$' /etc/default/keyboard ; then
    sudo sed -i 's/^\(XKBLAYOUT=\).*$/\1"us"/g' /etc/default/keyboard
fi

# check that the camera is enabled.
if grep -q '^#start_x' /boot/config.txt ; then
    sudo sed -i 's/^#\(start_x\).*$/\1=1/' /boot/config.txt
elif ! grep -q '^start_x' /boot/config.txt ; then
    echo "start_x=1" | sudo tee -a /boot/config.txt
fi

if ! grep -q '^gpu_mem' /boot/config.txt ; then
    echo "gpu_mem=128" | sudo tee -a /boot/config.txt
fi

echo "Misc configs done."

echo "Updating sources...."

if [ -d /home/pi/scripts ] ; then
    pushd .
    cd /home/pi
    tar c -zf scripts.tar.gz scripts
    rm -rf /home/pi/scripts/*
    popd
else
    mkdir /home/pi/scripts
fi
