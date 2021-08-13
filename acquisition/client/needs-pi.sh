#!/bin/bash

PYTHON_VERSION="3.4"
PYTHON_EXEC="python$PYTHON_VERSION"
TMP_DIR="/tmp"
PYTHON_SRC_DIR="$TMP_DIR/Python-3.6.5"
INSTALL_DIR="/tmp/scorhe-install"

cp "$INSTALL_DIR"/source/* /home/pi/scripts

# check if crontab is set correctly to launch the client program
REBOOT_CRON="@reboot sleep 10; export XAUTHORITY=/home/pi/.Xauthority; export DISPLAY=:0.0; $PYTHON_EXEC /home/pi/scripts/"
if ! crontab -l | grep -q '^'"$REBOOT_CRON" ; then
    crontab -l | ( sed 's/^\(@reboot.*\)$//g' ; echo "$REBOOT_CRON" ) | crontab -
fi

echo "Finished updating sources."
