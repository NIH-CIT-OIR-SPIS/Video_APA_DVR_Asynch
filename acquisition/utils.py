"""A utilty module for use throughout the acquisition package"""
# Note that this is where settings made by the user via the GUI launched by launcher.py are saved.
# These settings are automatically saved to C:\User\[UserNAME]\Downloads\SCHORHE directory, 
# and if such a directory doesn't exist it will create one


import errno
import argparse
import os
import getpass
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
import copy
#from scorhe_aquisition_tools import cam_set, cage_set



"""
Make a txt file, which for one line (the first line) stores a path variable (User/ti.....)
This storage will happen via cam_set.py and will only happen in cam_set.py if the line is empty


if that line is empty (in other words EOF):
    APPDATA_DIR = os.path.join(os.getenv("USERPROFILE"), "Downloads", "SCHORE", "")
    if not os.path.isdir(APPDATA_DIR):
        os.makedirs(APPDATA_DIR)
else:
    APPDATA_DIR = os.path.join( IN HERE INSERT THE FILE PATH via the txt file)
    ADD EXCEPTION STATEMENT HANDELER

"""
APPDATA_DIR = ""
APPDATA_OTHER = ""
USERPROFILE_HOME = ""
if platform.system() == 'Windows':
    USERPROFILE_HOME = os.getenv("USERPROFILE")
    if os.stat("save_location_settings.txt").st_size != 0:
        pathFile = open("save_location_settings.txt")
        line = pathFile.read().replace("\n", " ")
        pathFile.close()
        if not os.path.isdir(line):
            APPDATA_DIR = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
            if not os.path.isdir(APPDATA_DIR):
                os.makedirs(APPDATA_DIR)
            file = open("save_location_settings.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            file = open("save_location_cages.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
        else:
            APPDATA_DIR = copy.deepcopy(line)
    else:
        APPDATA_DIR = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
        if not os.path.isdir(APPDATA_DIR):
            os.makedirs(APPDATA_DIR)
        file = open("save_location_settings.txt", "w")
        file.write(APPDATA_DIR)
        file.close()
        file = open("save_location_cages.txt", "w")
        file.write(APPDATA_DIR)
        file.close()
elif platform.system() == 'Linux':
    USERPROFILE_HOME = os.environ['HOME']
    if os.stat("save_location_settings_linux.txt").st_size != 0:
        pathFile = open("save_location_settings_linux.txt")
        line = pathFile.read().replace("\n", " ")
        pathFile.close()
        if not os.path.isdir(line):
            APPDATA_DIR = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
            if not os.path.isdir(APPDATA_DIR):
                os.makedirs(APPDATA_DIR)
            file = open("save_location_settings_linux.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            file = open("save_location_cages_linux.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
        else:
            APPDATA_DIR = copy.deepcopy(line)
    else:
        APPDATA_DIR = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
        if not os.path.isdir(APPDATA_DIR):
            os.makedirs(APPDATA_DIR)
        file = open("save_location_settings_linux.txt", "w")
        file.write(APPDATA_DIR)
        file.close()
        file = open("save_location_cages_linux.txt", "w")
        file.write(APPDATA_DIR)
        file.close()
else:
    raise OSError('SCORHE Acquisition does not support your system: {}'.format(platform.system()))
    
#if platform.system() == 'Windows':
#    USERPROFILE_HOME = os.getenv("USERPROFILE")
#    if os.stat("save_location_cages.txt").st_size != 0:
#        pathFile = open("save_location_cages.txt")
#        line = pathFile.read().replace("\n", " ")
#        pathFile.close()
#        if not os.path.isdir(line):
#            APPDATA_OTHER = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
#            if not os.path.isdir(APPDATA_OTHER):
#                os.makedirs(APPDATA_OTHER)
#            file = open("save_location_cages.txt", "w")
#            file.write(APPDATA_OTHER)
#            file.close()
#        else:
#            APPDATA_OTHER = copy.deepcopy(line)
#    else:
#        APPDATA_OTHER = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
#        if not os.path.isdir(APPDATA_OTHER):
#            os.makedirs(APPDATA_OTHER)
#        file = open("save_location_cages.txt", "w")
#        file.write(APPDATA_OTHER)
#        file.close()
#elif platform.system() == 'Linux':
#    USERPROFILE_HOME = os.environ['HOME']
#    if os.stat("save_location_cages_linux.txt").st_size != 0:
#        pathFile = open("save_location_cages_linux.txt")
#        line = pathFile.read().replace("\n", " ")
#        pathFile.close()
#        if not os.path.isdir(line):
#            APPDATA_OTHER = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
#            if not os.path.isdir(APPDATA_OTHER):
#                os.makedirs(APPDATA_OTHER)
#            file = open("save_location_cages_linux.txt", "w")
#            file.write(APPDATA_OTHER)
#            file.close()
#        else:
#            APPDATA_OTHER = copy.deepcopy(line)
#    else:
#        APPDATA_OTHER = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
#        if not os.path.isdir(APPDATA_OTHER):
#            os.makedirs(APPDATA_OTHER)
#        file = open("save_location_cages_linux.txt", "w")
#        file.write(APPDATA_OTHER)
#        file.close()
#else:
#    raise OSError('SCORHE Acquisition does not support your system: {}'.format(platform.system()))


def expFilePath(strIn: str) -> str:
    """Gets the file path for the experiment's json file."""
    holder = APPDATA_DIR if strIn is None else strIn
    return os.path.join(holder, "exp.json")


def settingsFilePath(strIn: str) -> str:
    """Gets the file path for the program's settings json file."""
    holder = APPDATA_DIR if strIn is None else strIn
    return os.path.join(holder, "settings.json")

def settingsCagesFilePath(strIn: str) -> str:
    """Gets the file path for the program's settings json file, for individual cages."""
    holder = APPDATA_DIR if strIn is None else strIn
    return os.path.join(holder, "settings_cages.json")

def convertTimestamp(t: float) -> str:
    """Converts numeric time to a string that MATLAB can read.

    t is a double representing the elapsed number of seconds since the epoch.
    The resulting string shows the year, month, day, hour, minute, and second.
    The second is followed by a decimal point with three digit precision.

    :param t: the time to convert, in seconds since the epoch
    :return: A string representation of the given time in local time.
    """
    return time.strftime('%Y-%m-%d %Hh%Mm%S.{}s'.format(
            str(int(round(t * 1000)) % 1000).rjust(3, '0')),
            time.localtime(t))


def truncateFilename(filename: str) -> str:
    """Return the part of a video filename containing the time, camera ID and suffix.

    This is used to remove a bit of clutter from the console.

    :param filename: A filename for a video, formatted with no spaces in the
        time or camera id, and otherwise looks like this:
        ``"[{misc} ]{time} {id}.{ext}"``.
    :return: A string containing the time an camera id of a file, separated by
        a space.
    """
    return ' '.join(filename.split(' ')[-2:])

def writeDefualtSavePath(strIn: str) -> bool:
    global APPDATA_DIR
    #global APPDATA_OTHER
    if strIn is None:
        if platform.system() == 'Windows':
            if not APPDATA_DIR:
                APPDATA_DIR = os.path.join(USERPROFILE_HOME, "Downloads", "SCORHE", "")
                if not os.path.isdir(APPDATA_DIR):
                    os.makedirs(APPDATA_DIR)
            file = open("save_location_settings.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            file = open("save_location_cages.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            return True
        elif platform.system() == 'Linux':

            if not APPDATA_DIR:
                APPDATA_DIR = os.path.join(os.environ['HOME'], "Downloads", "SCORHE", "")
                if not os.path.isdir(APPDATA_DIR):
                    os.makedirs(APPDATA_DIR)
            file = open("save_location_settings_linux.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            file = open("save_location_cages_linux.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            return True
        else:
            raise OSError('SCORHE Acquisition does not support your system: {}'.format(platform.system()))
    else:
        if platform.system() == 'Windows':
            temp = copy.deepcopy(APPDATA_DIR)
            APPDATA_DIR = os.path.join(strIn, "SCORHE", "")
            try:
                if temp and temp != os.path.join(USERPROFILE_HOME, "") and str(temp).find("SCORHE") != -1: 
                    shutil.copytree(temp, APPDATA_DIR)

            except OSError as err:
                if err.errno == errno.ENOTDIR:
                    shutil.copy2(temp, APPDATA_DIR)
                elif err.errno == errno.EEXIST:
                    print("Error: %s" % err)
                    shutil.rmtree(temp)
                    writeDefualtSavePath(temp)
                else:
                    print("Error copying file: %s" % err)
            try:
                shutil.rmtree(temp)
            except OSError as err:
                if err.errno == errno.ENOTDIR:
                    print("Error trying to delete a file not directory: {}".format(err))
                    os.remove(temp)
                else:
                    print("[ERROR]: {}".format(err))
            file = open("save_location_settings.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            file = open("save_location_cages.txt", "w")
            file.write(APPDATA_DIR)
            file.close()                
            return False
        elif platform.system() == 'Linux':
            temp = copy.deepcopy(APPDATA_DIR)
            APPDATA_DIR = os.path.join(strIn, "SCORHE", "")
            try:
                if temp and temp != os.path.join(os.environ['HOME'], "") and str(temp).find("SCORHE") != -1: 
                    shutil.copytree(temp, APPDATA_DIR)

            except OSError as err:
                if err.errno == errno.ENOTDIR:
                    print("Error copying file: %s" % err)
                else:
                    shutil.copy2(temp, APPDATA_DIR)
            try:
                shutil.rmtree(temp)
            except OSError as err:
                if err.errno == errno.ENOTDIR:
                    print("Error trying to delete a file not directory: {}".format(err))
                    os.remove(temp)
                else:
                    print("[ERROR]: {}".format(err))
            file = open("save_location_settings_linux.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            file = open("save_location_cages_linux.txt", "w")
            file.write(APPDATA_DIR)
            file.close()
            return False
        else:
            raise OSError('SCORHE Acquisition does not support your system: {}'.format(platform.system()))

#def makeSubdirectory(parent_path: str, name: str) -> None:
#    global APPDATA_DIR
#    isPath = False
#    for name in os.path.listdir(parent_path):
#        if os.path.isdir(os.path.join(parent_path, name)):
#            isPath = True
#            APPDATA_DIR = os.path.join(parent_path, name)
#            break
#    if isPath:
#        return True
#    else:
#        os.makedirs(APPDATA_DIR)
#        return False