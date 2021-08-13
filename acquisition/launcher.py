"""
The SCORHE launcher is a program that provides the logic for the front end user facing code.
This file exists to link the frontend GUI code (which is a mess due to the
fact it was automatically generated) to the backend server code. Both the server and the
GUI are instantiated within its logic and will be utilized to create a good user experience.
Though its logic and GUI buttons, a user will be able to start recording, previewing all cameras
on the network. The user will also be able to group cameras and schedule experiments.

# SCORHE Launcher, Author: Joshua Lehman, 2017
"""


"""
Noah Cubert_July 2020 Intern: 
All comments by this user will be denoted with an NC before the comment.
For a single line comment denoted by '#' the following example will occur:
# NC: This is a test comment
For a block comment the following example will occur:
'''
NC: This is a test block comment
'''
"""
import datetime
import calendar
# for some reason, this is needed to make sure the server doesnt crash.
# noinspection PyUnresolvedReferences
import encodings.idna
import json
import logging
import os
import sys
import threading
import time
import copy
import platform

#import glob
#import psutil

from functools import partial

from PyQt5 import QtCore, QtWidgets

from typing import Dict, List, Union, Optional, Tuple
try:
    import sip
except ImportError:
    sip = None

import utils
from scorhe_aquisition_tools import cam_set, exp_updater, \
    updater, gplayer, cage_set, bundle
from scorhe_aquisition_tools.scorhe_launcher_gui import LegendGui, AcquisitionWindow, SettingsWindowIndivid, SettingsWindowOther, ShutdownGui
from scorhe_server import server, gpac

logger = logging.getLogger(__name__)

#logger = logging.basicConfig(filename="log_process_forest.log", level=logging.INFO)
COUNTER = 0

HOLDER_CAGE = ""
#saveFilePathCage = r"save_location_cages.txt"
#if platform.system() == 'Linux':
#    saveFilePathCage = r"save_location_cages_linux.txt"

class LaunchObject:
    """This class launches the whole server experiences.

    It first instantiates an instance of CameraServer, and then launches the
    required GUIs for user interaction.

    Q widgets are not threadsafe, so this can't be a thread.
    """
    # Somehow using slots breaks time.sleep in startLauncher and I don't know why
    # __slots__ = ('argv', 'camPorts', 'activeStreams', 'settings', 'expInfo',
    #              'players', 'controllerThread', 'updater', 'setter',
    #              'expUpdater', 'cameras', 'csv', 'buttons', 'cameraPickers',
    #              'playersGroup', 'text', 'window', 'time', 'recording',
    #              'addedExp', 'timed', 'saveLocation', 'endRunThread',
    #              'startRunThread',
    #              )
  
    def __init__(self, argv: List[str], window: AcquisitionWindow):

        self.saveFilePathCage = r"save_location_cages.txt"
        if platform.system() == 'Linux':
            self.saveFilePathCage = r"save_location_cages_linux.txt"
        if utils.APPDATA_DIR:
            self.path = utils.APPDATA_DIR
        else:
            self.path = os.path.join(os.getenv("USERPROFILE"), "Downloads", "SCORHE", "")

        self.camPorts = {}
        """Dictionary to map camera to streaming port.
        :type: Dict[str, int]
        """

        self.activeStreams = {"topLeftSelect": "", "topRightSelect": "",
                              "botLeftSelect": "", "botRightSelect": ""}
        """List reference to streams that are being shown in players.
        
        Maps selector name to selected camera id.
        :type: Dict[str, str]
        """

        self.activeRecordings = {"topLeftSelect": {'cameraInfo': {}, 'isRecording': False, 'cageName': "" }, "topRightSelect": {'cameraInfo': {}, 'isRecording': False, 'cageName': "" },
                                 "botLeftSelect": {'cameraInfo': {}, 'isRecording': False, 'cageName': "" }, "botRightSelect": {'cameraInfo': {}, 'isRecording': False, 'cageName': "" }
                                 }
        """ 
        Dictionary telling what cameras are currently in which wells along with recording information. Utilized for forming wells. 
        Wells are GUI buttons that correspond to the top left, top right, bottom left and bottom right recording cage drop down menus.
        :type: Dict[str, dict]
        """
        
        self.cageMap = {}
        """ 
        Dictionary with each cage name being mapped to a camera, well, and recording boolean value.
        :type: Dict[str, dict]
        """

        self.defaultSett = {'compression': 1, 'color': True, 'iso': '0', 'len': 5,  'reso': '1280x720',
                       'vflip': {'camera': {}, 'default': False}, 'fps': 60, 'shutter speed': 8333, 'brightness': 50, 'contrast': 0,
                       'autogain': True, 'gain': 0,
                       'camMap': {'name': {}, 'camera': {}},
                       'rotation': {'camera': {}, 'default': 0},
                       'zoom location': {'camera': {}, 'default': (0, 0)},
                       'zoom dimension': (1280, 720),
                       'pushUpdates': False, 'grouptype': 'SCORHE',
                       'baseDirectory': '', 'active cams': [],}
        # Shutterspeed  in micro seconds (us)  shutter speed being 0 means it is auto adjusting
        self.cageListOpen = False
        self.defaultCager = False
        self.buttonHolder = ""
        self.textHolder = ""


        """
        Dictionary telling what cameras are currently recording and storing data.

        Maps stream to camera name and whether or not the stream is recording.
        :type: Dict[str, dict]
        """




        self.loadAsynchSettings = False
        self.settingsCages = {}
        self.cageSettingsOpen = {'state': False}

        """Dictionary of settings for the system cages. Where each individual cage can have individual settings.
        
        :type settings: Dict[str: Union[int, str, float, List, Dict[str, Dict]]]
        """



        
        #self.running = {'recordingRunning': False, 'previewRunning': True}

        self.builtIt = False

        self.settings = {}
        """Dictionary of settings for the system.
        
        :type settings: Dict[str: Union[int, str, float, List, Dict[str, Dict]]]
        """

        self.expInfo = {}
        """A dictionary used to store the details needed for an experiment.
        
        This includes its name, save location, start and end times, among other
        things. 
        
        This dictionary is given to the expUpdate to set its data.
        """

        self.prevExpTitle = {'name': ''}
        self.currExpTitle = {'name': ''}
        self.expRunning = False
        self.expInfoHolder = {}
        self.expChanged = False


        self.players = {None: 0, None: 0, None: 0, None: 0}
        """A dictionary mapping player objects to camera port."""

        # Reference to SCORHE controller
        self.controllerThread, _ = server.masterRunServer(argv)
        """The thread controlling the server.
        
        This allows a way to access all the server settings and configuration. 
        """

        self.serverOptions = self.controllerThread.server.options
        self.clientOptions = self.controllerThread.server.clientOptions
        
        self.controllerThread.server.asynch = self.loadAsynchSettings

        self.cameras = []
        """A list of the currently known camera ids.
        :type: List[str]
        """
        
        self.csv = {"maps": [], "labels": []}
        """A deserialized version of the csv specifying experiment data for the researchers."""

        # Reference to main window object items (Main GUI)
        self.buttons = window.buttons
        """A dictionary mapping button names to button objects.
        
        This is used for binding the buttons to listeners to act on button 
        presses.
        """

        self.cameraPickers = window.cameraPickers
        """A dictionary selector names the combobox pickers.
        
        This is used to bind listeners to update the program with user 
        selections.
        """

        self.playersGroup = window.players
        """A dictionary mapping the names of players to their objects.
        
        This is used to ensure videos are streamed to the correct viewport.
        """

        self.text = window.text
        """A dictionary mapping the names of modifiable text fields to their objects.
        
        This allows the program to modify text fields on the program, such as 
        experiment times and the storage indicator.
        """

        self.window = window
        """The main window. Stored for access in the future."""

        # Reference to a update/expUpdater/setter object
        self.updater = updater.Updater(self.camUpdate, self.text,
                                       self.controllerThread,
                                       self.camPorts)

       
        self.time = {'end': datetime.datetime.now(),
                     'start': datetime.datetime.now()}  # type: Dict[str, datetime.datetime]
        """A dictionary holding the start and end time of an experiment."""


        # General info regarding current runtime status
        self.recording = False
        """Whether the program is currently recording from its cameras."""

        self.addedExp = False
        """Whether an experiment had recently been added."""

        self.timed = False
        """Whether the current experiment has a separate thread managing its start and end."""


        self.cageTimeMap = {'timed': False, 'endRunThread': None, 'startRunThread': None, 'endTime': datetime.datetime.now(), 'startTime': datetime.datetime.now()} ##################################################################################

        self.timing_per_cage_threads = {"topLeftSelect": None, "topRightSelect": None, "botLeftSelect": None, "botRightSelect": None,
                                        "top_left_time": '00:00:00', "top_right_time": '00:00:00', "bot_left_time": '00:00:00', "bot_right_time": '00:00:00'}
        self.update_text_thread_timer = {"topLeftSelect": False, "topRightSelect": False, "botLeftSelect": False, "botRightSelect": False}
        self.update_lock = threading.Lock()
        self.saveLocation = ""
        """The location where the saved files should be stored in."""

        self.timerTotalRun = None
        """ A thread used to keep track of the total amount of time that has passed since the experiment has started """

        self.timeRemainRun = None
        """ A thread used to keep track of the total amount of time left since the experiment has started """
        
        self.endRunThread = None
        """A thread used to end the experiment at the right time."""

        # NC:  The self.startRunThread functionality interferes with the functionality of the self.endRunThread
        self.startRunThread = None
        """A thread used to end the experiment at the right time."""
        self.cageSetter = None
        self.setter = None
        self.expUpdater = None
        self.cageSetter = None


        
        self.openSettingsJson()
        # Give server GUI determined settings
        self.setSettings()


        self.window.setSelectionType(self.settings['grouptype'])
        # Sets up buttons
        self.setUpGUIButtons()
        time.sleep(0.1)
        # Declares an instance of the GUI information updater
        # Starts the updater
        self.updater.update()
        # Sets up side info panel
        self.setUpInfoPanel()
        self.camUpdate()
        self.cageUpdate()

        self.buildCageMap()
        self.openSettingsCagesJson()
        self.setSettingsCages()
        #Sets up essential maps
        

        # Sets up cage window and cage buttons
        self.cageWindow = None
        self.cagebuttons = None
        self.cagetext = None
        self.cageRecord = ""

        self.cageSettingsWindow = None
        self.cageSettingsButtons = None
        self.cageSettingsText = None


        self.timeStorage = 0.0
        self.timeRunStorage = 0.0
        self.timeRemainStore = -1



        # Auto Shutdown Vars
        self.shutWindow = None
        self.shutbuttons = None
        self.shuttext = None
        self.shutdownThread = None
        self.autoThread = None
        self.autoClose = True
        #self.secondsTillShutdown = 30
        self.secondsTillShutdown = 10
        self.terminateShutdownThread = None

    def cageUpdate(self) -> None:
        """Update the cages in the dropdown menus.

        :return: Nothing
        """
        
        if self.settings['grouptype'].lower() != 'scorhe':
            return
        for name, picker in self.cameraPickers.items():
            prev = self.activeStreams[name]
            if prev and picker.findText(prev) >= 0:
                picker.setCurrentIndex(0)
            picker.clear()
            picker.addItem("")
            picker.addItems(sorted(list(self.settings['camMap']['name'].keys())))
            if prev and picker.findText(prev) >= 0:
                picker.setCurrentIndex(picker.findText(prev))
            else:
                picker.setCurrentIndex(0)
        self.updateWellList()


    def camUpdate(self, cameras: Optional[List[str]]=None) -> None:
        """Update the list of cameras if a list was passed.

        This allows calling updateCameras() to simply update the names.
        """
        curCams = set(self.cameras)
        
        if self.settings['grouptype'].lower() != 'scorhe':
            if cameras is not None:
                inCams = set(cameras)
                deadCams = curCams - inCams
                newCams = inCams - curCams
                self.cameras = cameras

                for cam in deadCams:
                    if cam in self.settings['camMap']['camera']:
                        for selector in self.cameraPickers.values():
                            selector[self.settings['camMap']['camera'][cam]].setEnabled(False)
                    else:  # TODO: log unlabeled cameras in the UI?
                        pass
            else:
                newCams = curCams
                for selector in self.cameraPickers.values():
                    for button in selector.values():
                        button.setEnabled(False)

            for cam in newCams:
                if cam in self.settings['camMap']['camera']:
                    for selector in self.cameraPickers.values():
                        selector[self.settings['camMap']['camera'][cam]].setEnabled(True)
                else:  # TODO: log unlabeled cameras in the UI?
                    pass

        # go through the cameras and get their names, if they have one. otherwise, just use their id
        camNames = [""] + [
            i if i not in self.settings['camMap']['camera'].keys() else
            self.settings['camMap']['camera'][i] for i in self.cameras]
        camNames.sort()
        self.camCageUpdate()
            
            

    def camCageUpdate(self) -> None:
        if self.settingsCages:
            i = 0
            camList = list(self.settings['camMap']['name'].keys())
            otherlist = list(self.settingsCages.keys())
            for i in range(len(camList)):
                if camList[i] not in otherlist:
                    self.settingsCages.update([(camList[i], {})])
                    self.settingsCages[camList[i]] = copy.deepcopy(self.settings)
                
                self.settingsCages[camList[i]]['camMap'] = self.settings['camMap']
            i = 0
            for i in range(len(otherlist)):
                if otherlist[i] not in camList:
                    self.settingsCages.pop(otherlist[i])
                    #self.settingsCages[camlist[i]] = copy.deepcopy(self.settings)
            i = 0
            for i in range(len(camList)):
                self.settingsCages[camList[i]]['camMap'] = self.settings['camMap']
            self.buildCageMap()

    def setUpGUIButtons(self) -> None:
        """Connect up all main GUI buttons."""
        self.buttons["power"].clicked.connect(self.shutdown)
        #self.buttons["start rec"].clicked.connect(self.toggleRecording)
        #self.buttons["loadSettings"].clicked.connect(self.toggleLoadSettings)
        
        self.buttons["start rec top left"].clicked.connect(lambda: self.toggleRecordingIndivid("topLeftSelect"))
        self.buttons["start rec top right"].clicked.connect(lambda: self.toggleRecordingIndivid("topRightSelect"))
        self.buttons["start rec bottom left"].clicked.connect(lambda: self.toggleRecordingIndivid("botLeftSelect"))
        self.buttons["start rec bottom right"].clicked.connect(lambda: self.toggleRecordingIndivid("botRightSelect"))
        
        #self.buttons["cage list recordings"].clicked.connect(self.handleCageListButton)
        self.buttons["cageSettings"].clicked.connect(self.handleCageSettingsButton)

        
        for pickerName, picker in self.cameraPickers.items():
            if self.settings['grouptype'].lower() == 'scorhe':
                picker.clear()
                picker.addItem("")
                picker.currentIndexChanged.connect(partial(self.setUpPlayers, pickerName ))
                picker.currentIndexChanged.connect(partial(self.updateWellList))
            else:
                for name, button in picker.items():
                    button.clicked.connect( partial(self.setUpPlayers, pickername, name))            

        self.buttons["settings"].clicked.connect(self.handleSettingsButton)
        #self.buttons["add exp"].clicked.connect(self.addExp)
        self.buttons["playback"].clicked.connect(self.launchEditor)
        self.buttons["playback"].setEnabled(False)
        self.buttons["legend"].clicked.connect(self.openLegend)
 
        


    def setUpInfoPanel(self) -> None:
        """Instantiate main GUI side info panel."""
        self.text["exp name"].setText("Untitled")
        self.text["start time"].setText("None")
        self.text["end time"].setText("None")
        self.text["time run for"].setText("00:00:00")
        self.text["time remain"].setText("00:00:00")
        self.text["cam num"].setText("0")

    def setUpPlayers(self, pickerName: str, name: str) -> None:
        """Sets up the players for playing the previews.

        When a group is clicked on in the main window, this function chooses
        which players to start; which players to instantiate and in which frame.
        """
        try:
            isScorhe = self.settings['grouptype'].lower() == 'scorhe'
            
            if isScorhe:
                name = self.cameraPickers[pickerName].currentText()
            self.stopAllPlayers()
            possPlayers = {0: self.playersGroup["topLeftPlayer"],
                           1: self.playersGroup["topRightPlayer"],
                           2: self.playersGroup["botLeftPlayer"],
                           3: self.playersGroup["botRightPlayer"]}  # type: Dict[int, QtWidgets.QFrame]
            pickers = [self.cameraPickers["topLeftSelect"],
                       self.cameraPickers["topRightSelect"],
                       self.cameraPickers["botLeftSelect"],
                       self.cameraPickers["botRightSelect"]]
            ind = ["topLeftSelect", "topRightSelect", "botLeftSelect",
                   "botRightSelect"]

            def createPlayer(players: Dict[gplayer.GPlayer, QtWidgets.QFrame],
                             winId: sip.voidptr,
                             frame: QtWidgets.QFrame,
                             port: int) -> Dict[gplayer.GPlayer, QtWidgets.QFrame]:
                """Function creates a gstreamer player in provided frame."""
                dim = frame.frameRect()
                player = gplayer.GPlayer(port, winId, dim.width(), dim.height())
                player.setWindowTitle('Player')
                player.start()
                players[player] = frame
                return players

            # Get selected group/groups
            old = self.activeStreams[pickerName]
            self.activeStreams[pickerName] = name

            new = name
            if new:  # things should be disabled
                if old != new:  # this is a new pick, things should be disabled
                    for j in range(0, 4):
                        if ind[j] != pickerName:
                            if isScorhe:
                                pickers[j].model().item(pickers[j].findText(new)).setEnabled(False)
                            else:
                                pickers[j][new].setEnabled(False)
                    if old:  # something else was here, enable it
                        # enable things
                        for j in range(0, 4):
                            if ind[j] != pickerName:
                                if isScorhe:
                                    pickers[j].model().item(pickers[j].findText(old)).setEnabled(True)
                                else:
                                    pickers[j][old].setEnabled(True)
                    else:  # there was nothing else here, no need to enable anything
                        pass
                else:  # there was a stream here, enable for the rest
                    for j in range(0, 4):
                        if ind[j] != pickerName:
                            if isScorhe:
                                pickers[j].model().item(pickers[j].findText(old)).setEnabled(True)
                            else:
                                pickers[j][old].setEnabled(True)
                    self.activeStreams[pickerName] = None
            else:  # no new stream
                if old:  # there was a stream here, enable for the rest
                    for j in range(0, 4):
                        if ind[j] != pickerName:
                            if isScorhe:
                                pickers[j].model().item(pickers[j].findText(old)).setEnabled(True)
                            else:
                                pickers[j][old].setEnabled(True)
                else:  # there wasn't a stream here to begin with, do nothing
                    pass

            cams = []
            # noinspection PyTypeChecker
            for c in self.activeStreams.values():
                if c:
                    if isScorhe:
                        if 'main' in self.settings['camMap']['name'][c]:
                            cams.append(self.settings['camMap']['name'][c]['main'])
                    elif c in self.settings['camMap']['name']:
                        cams.append(self.settings['camMap']['name'][c])

            self.controllerThread.server.mappySetter(self.cageMap, self.settingsCages)
            for camera in cams:
                # For each camera in selected cage issue a individual preview
                # message to each (saves bandwidth then sending to all)
                #if bool(self.cageMap) and bool(self.settingsCages):
                #    t1 = threading.Thread(target=self.controllerThread.server.sendSelectStartPreviewingMessage, args=[camera, self.cageMap, self.settingsCages])
                #else:
                t1 = threading.Thread(target=self.controllerThread.server.sendSelectStartPreviewingMessage, args=[camera])
                t1.start()
                t1.join()



            


            
            # Update all camera preview ports
            t1 = threading.Thread(target=self.updater.updatePreviewPorts())
            t1.start()
            t1.join()
            cameraToView = []
            for key in ind:
                camera = self.activeStreams[key]
                # Add the selected preview ports to a list
                if camera:
                    if isScorhe:
                        try:
                            camera = self.settings['camMap']['name'][camera]['main']
                        except KeyError:
                            camera = ''
                    else:
                        camera = camera if camera not in self.settings['camMap']['name'].keys() else \
                            self.settings['camMap']['name'][camera]
                if camera and camera in self.camPorts:
                    cameraToView.append(self.camPorts[camera])
                else:
                    cameraToView.append(None)

            # Created all requested players
            for cameraNum in range(0, len(cameraToView)):
                if cameraToView[cameraNum]:
                    self.players = createPlayer(self.players,
                                                possPlayers[cameraNum].winId(),
                                                possPlayers[cameraNum],
                                                cameraToView[cameraNum])
            
        except Exception as e:
            logger.error(e)
            import traceback
            traceback.print_exception(Exception, e, e.__traceback__)
            traceback.print_tb(e.__traceback__)

    def stopAllPlayers(self) -> None:
        """Function stops all the running players."""
        isScorhe = self.settings['grouptype'].lower() == 'scorhe'
        keys = self.players.keys()
        # noinspection PyTypeChecker
        for player in [key for key in keys if key]:
            player.quit(self.players[player])
        # noinspection PyTypeChecker
        for camera in [c for c in self.activeStreams.values() if c]:
            if isScorhe:
                if 'main' in self.settings['camMap']['name'][camera]:
                    camera = self.settings['camMap']['name'][camera]['main']
            else:
                camera = camera if camera not in self.settings['camMap']['name'].keys() else \
                    self.settings['camMap']['name'][camera]
            if camera and camera in self.camPorts:
                t1 = threading.Thread(target=self.controllerThread.server.
                                      sendSelectStopPreviewingMessage, args=[camera])
                t1.start()
                t1.join()

        t1 = threading.Thread(target=self.updater.updatePreviewPorts())
        t1.start()
        t1.join()
        # Force frame reset
        for key, value in self.playersGroup.items():
            value.setAutoFillBackground(False)
            value.setAutoFillBackground(True)


    def runTimer(self) -> None:
        """Functions schedules start and end time timers for experiment recording."""

        #start = "start"
        totalRuntime = (self.time["end"] - self.time["start"]).total_seconds()
        if (totalRuntime > 0):
            
            #self.text["time run for"].setText(str(self.time["end"] - self.time["start"]))
            self.text["time run for"].setText('00:00:00')
            #self.startRecordingAtTime(self.time["start"])


            self.timeRemainStore = int(round( (self.time["end"] - datetime.datetime.now()).total_seconds(), 2 ))

            print("running")
            runtimeFromNow = round( (self.time["end"] - datetime.datetime.now()).total_seconds(), 2 )
            #self.endRunThread = threading.Timer(runtimeFromNow, self.stopAllRecording)
            #self.endRunThread.start()




            self.timed = True
        else:
            print("You have non compatable start and end times for your experiment.")

    def totalRunTimer(self) -> None:
        """ Timer keeping track of how long your experiment has run for from the moment you created your experiment to the time specified. """
        self.timeStorage += 1.0
        self.text["time run for"].setText(str(datetime.timedelta(seconds=self.timeStorage)))
        self.timerTotalRun = threading.Timer(1, self.totalRunTimer)
        self.timerTotalRun.start()

    def totalTimeRemain(self) -> None:
        """ Tells you how much time you have left for your experiment  Adds and extra minute to the time to account for setting up to start recording"""
        self.timeRemainStore = int((self.time["end"] - datetime.datetime.now()).total_seconds())
        if self.timeRemainStore < 0:
            self.text['time remain'].setText("00:00:00")
            
        else:
            self.text['time remain'].setText(str(datetime.timedelta(seconds=self.timeRemainStore)))
        self.timeRemainRun = threading.Timer(1, self.totalTimeRemain)
        self.timeRemainRun.start()

    
    #def stopTimeLeftTimer(self) -> None:
    #    self.timerTotalRun.cancel()

    #def runTimerCages(self) -> None:
    #    # TODO: Implement timers for each individual cage.
    #    return
    #    totalRuntime = (self.time["end"] - self.time["start"]).total_seconds()
    #    if totalRuntime > 0:
    #        self.text['time run for'].setText(str(self.time["end"] - self.time['start']))
    #        self.startRecordingAtTime(self.time[start])
    #        runtimeFromNow = round( (self.time["end"] - datetime.datetime.now()).total_seconds(), 2 )            
    #        self.endRunThread = threading.Timer(runtimeFromNow, self.toggleRecording)
    #        self.endRunThread.start()
    #        self.timed = True
        


# NC: As of 7-7-2020 this function was causing a recording issue and multi-threading errors (see description in attached ERROR_LOG_VideoAPA.txt)
# NC: As such this function is no longer needed for acquisition purposes (this is different for editor purposes please add if you are using for editing purposes please utilize self.recordingStartedMessage() function instead of self.toggleRecording )
    def startRecordingAtTime(self, startTime) -> None:
        """Function starts a timer for experiment recording start time."""
        delay = (startTime - datetime.datetime.now()).total_seconds()

        #self.startRunThread = threading.Timer(delay, self.toggleRecording)  # NC: The timer itself isn't the problem it's the fact the self.toggleRecording is set up to be executed after the timer is done.
        self.startRunThread = threading.Timer(delay, self.recordingStartedMessage(delay)) 
        self.startRunThread.start()


    def launchEditor(self) -> None:
        """Launches the editing software."""
        pass

    def openSettingsJson(self) -> None:
        """Function attempts to open previous saved settings file and applies to current run."""
        default = self.defaultSett
        
        if os.path.isfile(utils.settingsFilePath(None)):
            with open(utils.settingsFilePath(None), 'r') as f:
                data = json.load(f)
                # copies contents of the json in, so any other object with ref
                # to settings will also update
                for c in data:
                    self.settings[c] = data[c]
                # noinspection PyTypeChecker
                for c in default.keys():
                    if c not in self.settings.keys():
                        self.settings[c] = default[c]
                if not isinstance(self.settings['vflip'], dict):
                    self.settings['vflip'] = {'camera': {},
                                              'default': self.settings['vflip']}
                if 'zoom' in self.settings:
                    pts = self.settings['zoom']  # type: Dict[str, Union[List[int], Dict[str, List[int]]]]
                    del self.settings['zoom']
                    pts.items()
                    self.settings['zoom dimension'] = pts['default'][2:]
                    # noinspection PyTypeChecker
                    for cam, window in pts['camera'].items():
                        self.settings['zoom location'][cam] = window[:2]
                        if window[2:] != self.settings['zoom dimension']:
                            logger.warning(
                                    "Warning: {} has dim {}, which was set as {} "
                                    "elsewhere. Check your settings file.".format(
                                            cam, window[2:], self.settings['zoom dimension']))
                            self.settings['zoom dimension'] = window[2:]
        else:
            # If saved settings file does not exist use default
            self.settings = default

    def closeSettingsJson(self) -> None:
        """Save current settings to a file."""
        strIn = None
        if utils.APPDATA_DIR:
            strIn = utils.APPDATA_DIR         
        with open(utils.settingsFilePath(strIn), 'w') as f:
            json.dump(self.settings, f, sort_keys=True, indent=4)


    def saveExpJson(self) -> None:
        """Save current experiment information to a file."""
        if self.addedExp:
            obj = {}
            if os.path.isfile(utils.expFilePath(None)):
                with open(utils.expFilePath(None), 'r') as f:
                    obj = json.load(f)

            name = self.expInfo['name']
            del self.expInfo['name']
            obj[name] = self.expInfo
            with open(utils.expFilePath(None), 'w') as f:
                json.dump(obj, f, sort_keys=True, indent=4)
            self.expInfo['name'] = name
            with open(os.path.join(self.expInfo['saveDir'], 'exp.json'), 'w') as f:
                json.dump(self.expInfo, f, sort_keys=True, indent=4)


    def setButtonOther(self) -> None:
        
        buttonList = ["start rec top left", "start rec top right", "start rec bottom left", "start rec bottom right"]
        textList = ["Record Top Left", "Record Top Right", "Record Bottom Left", "Record Bottom Right"]
        if self.recording:
            self.buttonHolder = "In synch"
            for i in buttonList:
                self.buttons[i].setText("In Synch Mode")
            i = 0
            for i in self.cageMap:
                if self.cageMap[i]['wellSelect'] != 'notInSelect':
                    strInsert = i + ": is in synch"
                    if self.cageListOpen:
                        self.cagetext["recCombo"].setItemText(self.cagetext["recCombo"].currentIndex(), strInsert)
                    if self.cageSettingsOpen['state']:
                        self.cageSettingsText["cageCombo"].setItemText(self.cagetext["cageCombo"].currentIndex(), strInsert)
        else:
            self.buttonHolder = ""
            i = 0
            for i in range(4):
                self.buttons[buttonList[i]].setText(textList[i])
            i = 0
            for i in self.cageMap:
                if self.cageMap[i]['wellSelect'] != 'notInSelect':
                    strInsert = i + ": is not recording"
                    if self.cageListOpen:
                        self.cagetext["recCombo"].setItemText(self.cagetext["recCombo"].currentIndex(), strInsert)
                    if self.cageSettingsOpen['state']:
                        self.cageSettingsText["cageCombo"].setItemText(self.cagetext["cageCombo"].currentIndex(), strInsert)
                 
    def setCameraRecordMap(self) -> None:
        """ Creates the self.activeRecordings map. """
        listOther = ["topLeftSelect", "topRightSelect", "botLeftSelect",  "botRightSelect"]
        settingsMap = self.settings['camMap']['name']
        for i in range(4):
            self.activeRecordings[listOther[i]]['cageName'] = self.activeStreams[listOther[i]]
            if self.activeRecordings[listOther[i]]['cageName']:
                self.activeRecordings[listOther[i]]['cameraInfo'] = settingsMap[self.activeRecordings[listOther[i]]['cageName']]

    def setRecordingBool(self, well: str, setBoolByInt: int) -> None:
        """ Utility function that will change boolean values in self.activeRecordings and self.cageMap. """
    
        listOther = ["topLeftSelect", "topRightSelect", "botLeftSelect",  "botRightSelect"]
        if well == "SynchRecordx86":
            self.activeRecordings["topLeftSelect"]['isRecording'] = (self.recording and bool(setBoolByInt))
            self.activeRecordings["topRightSelect"]['isRecording'] = (self.recording and bool(setBoolByInt))
            self.activeRecordings["botLeftSelect"]['isRecording'] = (self.recording and bool(setBoolByInt))
            self.activeRecordings["botRightSelect"]['isRecording'] = (self.recording and bool(setBoolByInt))
            for i in self.cageMap:
                if listOther.count(self.cageMap[i]['wellSelect']) == 1:
                    self.cageMap[i]['isRecording'] = (self.recording and bool(setBoolByInt))
        elif listOther.count(well) == 1:
            self.activeRecordings[well]['isRecording'] = bool(setBoolByInt)
            for i in self.cageMap:
                if self.cageMap[i]['wellSelect'] == well:
                   self.cageMap[i]['isRecording'] = bool(setBoolByInt)           

    def buildCageMap(self) -> None:
        if bool(self.settings) and bool(self.settings['camMap']) and bool(self.settings['camMap']['name']):
            cageEmpty = True
            for i in self.settings['camMap']['name']:
                if self.settings['camMap']['name'][i]:
                    cageEmpty = False
                    break
            if cageEmpty:
                print("None of the cages map to any camera")
                return

            if not bool(self.cageMap):
                # Make deep copy as you don't want to interfere with keys for self.settings
           
                cageMapTemp = copy.deepcopy(self.settings['camMap']['name'])
                i = 0
                for i in cageMapTemp:
                    cageMapTemp[i].update([('isRecording', False)])
                    cageMapTemp[i].update([('wellSelect', 'notInSelect')])
                self.cageMap = copy.deepcopy(cageMapTemp)
                #print(self.cageMap.values())
                #print(self.settings['camMap']['name'].values())
                

            if list(set(self.cageMap.keys())) != list(set(self.settings['camMap']['name'].keys())):
                cageMapTemp = copy.deepcopy(self.settings['camMap']['name'])
                i = 0 
                camList = list(self.settings['camMap']['name'])
                otherList = list(self.cageMap.keys())
                toAdd = []
                toRemove =[]
                i = 0
                for i in range(len(camList)):
                    if camList[i] not in otherList:
                        toAdd.append(camList[i])
                i = 0
                for i in range(len(otherList)):
                    if otherList[i] not in camList:
                        toRemove.append(otherList[i])
                if toRemove:
                    i = 0
                    for i in range(len(toRemove)):
                        self.cageMap.pop(toRemove[i])
                if toAdd:
                    i = 0
                    for i in range(len(toAdd)):
                        self.cageMap.update([(toAdd[i], {})])
                        self.cageMap[toAdd[i]].update([('isRecording', False)])
                        self.cageMap[toAdd[i]].update([('wellSelect', 'notInSelect')])
                i = 0
                for i in self.cageMap:
                    self.cageMap[i].update(self.settings['camMap']['name'][i])

            #for cage in self.settings['camMap']['name']:
            #    print(self.settings['camMap']['name'][cage])
            #    if 'main' in self.settings['camMap']['name'][cage]:
            #        if self.cageMap[cage]['main'] != self.settings['camMap']['name'][cage]['main']:
            #            self.cageMap[cage]['main'] = copy.deepcopy(self.settings['camMap']['name'][cage]['main'])
            #    if 'front' in self.settings['camMap']['name'][cage]:
            #        if self.cageMap[cage]['front'] != self.settings['camMap']['name'][cage]['front']:
            #            self.cageMap[cage]['front'] = copy.deepcopy(self.settings['camMap']['name'][cage]['front'])
            #    if 'rear' in self.settings['camMap']['name'][cage]:
            #        if self.cageMap[cage]['rear'] != self.settings['camMap']['name'][cage]['rear']:
            #            self.cageMap[cage]['rear'] = copy.deepcopy(self.settings['camMap']['name'][cage]['rear'])           

            i = 0
            streams = copy.deepcopy(self.activeStreams)
            count = 0
            for i in streams:
                if streams[i] == '':
                    streams[i] = count
                count += 1
            rev_streams = {value : key for (key, value) in streams.items()}
            for i in self.cageMap:
                if list(rev_streams).count(i) == 1:
                    self.cageMap[i]['wellSelect'] = rev_streams[i]
                else:
                    self.cageMap[i]['wellSelect'] = 'notInSelect'
            self.builtIt = True
        else:
            self.builtIt = False
            print("Please make cages.")


    def anythingRecording(self) -> bool:
        if self.cageMap and self.builtIt:
            for cage in self.cageMap:
                if self.cageMap[cage]['isRecording']:
                    return True
        if self.recording:
            return True

        return False

    def checkThreadTimers(self) -> None:
        
        if self.expInfo:
            if self.expInfoHolder:
                if self.expInfo['name'] != self.expInfoHolder['name']:
                    self.expChanged = True
                else:
                    self.expChanged = False
            self.expInfoHolder = copy.deepcopy(self.expInfo)
        #print(" self.currExpTitle['name']:  %s" % self.currExpTitle['name'])
        #print(" self.prevv %s" % self.prevExpTitle['name'])
        if self.timerTotalRun is None and self.timeRemainRun is None:
            if not self.anythingRecording():
                #if self.addedExp:
                #    self.totalTimeRemain()
                self.totalRunTimer()
        elif self.timerTotalRun is not None and not self.timerTotalRun.isAlive() or \
           self.timeRemainRun is not None and not self.timeRemainRun.isAlive():

            if not self.anythingRecording():
                if self.expInfo and self.currExpTitle['name'] and \
                   self.expInfoHolder['name'] != self.currExpTitle['name']:
                    self.timeRemainStore = 0
                    self.timeStorage = 0
                #if self.expRunning:
                #   self.totalTimeRemain()
                self.totalRunTimer()


        if self.expInfo:
            if not self.currExpTitle['name'] and not self.prevExpTitle['name']:
                self.currExpTitle['name'] = copy.deepcopy(self.expInfo['name'])
                self.prevExpTitle['name'] = ''
            else:
                 self.prevExpTitle['name'] = copy.deepcopy(self.currExpTitle['name'])
                 self.currExpTitle['name'] = copy.deepcopy(self.expInfo['name'])





    def toggleRecording(self) -> None:
        """Calls the SCORHE_server's toggle recording function.

        This function is called when the "start recording" button is pressed on
        the GUI, it will also change toggle button text
        """
        self.checkThreadTimers()
        self.autoClose = True

        i = 0
        self.buildCageMap() #if not self.builtIt: self.buildCageMap()
        self.setCameraRecordMap()
        self.setRecordingBool("SynchRecordx86", 1)

        self.controllerThread.toggleRecording(self.cageMap)
        if not self.recording:
            if not self.addedExp:
                self.controllerThread.server.options.activeCams = self.controllerThread.\
                    server.clients.getClients("Camera")
            # Start to record, prompt button to ask for stop recording
            self.buttons["start rec"].setText("Stop Recording")
            self.recording = True
            self.setRecordingBool("SynchRecordx86", 1)  # NC edit
        else:
            if self.addedExp:
                self.saveExpJson()
                self.addedExp = False
            # Stop recording, prompt button to ask for start recording
            self.buttons["start rec"].setText("Start Recording")
            self.recording = False
            self.setRecordingBool("SynchRecordx86", 1)
            w = self.controllerThread.server.options.captureWidth
            h = self.controllerThread.server.options.captureHeight
            fps = self.controllerThread.server.clientOptions.fps
            f = self.controllerThread.server.options.baseDirectory
            if self.timed:
                if self.startRunThread is not None and \
                        self.startRunThread.isAlive():
                    self.startRunThread.cancel()
                if self.endRunThread is not None and \
                        self.endRunThread.isAlive():
                    self.endRunThread.cancel()
                if self.expChanged: self.controllerThread.server.options.baseDirectory = ''
                if not self.addedExp: self.expInfo = {}
                self.timed = False
            gpac.run(width=w, height=h, fps=fps, filesDir=f)
            self.controllerThread.server.options.activeCams = self.controllerThread.\
                server.clients.getClients("Camera")
        self.setButtonOther()


        if not self.anythingRecording():
            if self.timerTotalRun is not None and self.timerTotalRun.isAlive():
                self.timerTotalRun.cancel()
            if self.timeRemainRun is not None and self.timeRemainRun.isAlive():
                self.timeRemainRun.cancel()



    def toggleRecordingIndivid(self, wellSelect: str) -> None:
        """ Toggles recordings based on well selection. """
        self.buildCageMap() #if not self.builtIt: self.buildCageMap()
        self.setCameraRecordMap()

        if self.activeRecordings[wellSelect]['cageName']:
            #if self.addedExp and (not self.expRunning):
            #    self.toggleRecordingCage(self.activeRecordings[wellSelect]['cageName'], wellSelect)
            #else:
            #    tp = (self.activeRecordings[wellSelect]['cageName'], wellSelect)
            #    self.addExp(tp)
            #    #while not self.addedExp:
            #    #    time.sleep(0.0001)
            #    #print("whyu")
            #    #self.toggleRecordingCage(self.activeRecordings[wellSelect]['cageName'], wellSelect)
            #    #while not self.addedExp:
            #    #    time.sleep(0.001)
            #    #self.toggleRecordingCage(self.activeRecordings[wellSelect]['cageName'], wellSelect)
            #    #while exp_updater.name
            ##if not(self.expUpdater is None:
            ##    print('ih')
            ##    self.addExp()
            ##    self.toggleRecordingCage(self.activeRecordings[wellSelect]['cageName'], wellSelect)
            ##else:
            ##    print("Please add experiment")
            if self.expInfo:
                self.toggleRecordingCage(self.activeRecordings[wellSelect]['cageName'], wellSelect)
            else:
                tp = (self.activeRecordings[wellSelect]['cageName'], wellSelect)
                self.addExp(tp)
        else:
            print("Please make sure you choose a cage first.")


    def run_well_timer(self, time_dur: float, time_start: float, well: str, cage: str):
        while time.time() - time_start < time_dur:
            self.text[well].setText(str(datetime.timedelta(seconds=int(time_dur - (time.time() - time_start))  )) )
            #with self.update_lock:
            time.sleep(0.001)
            if not self.update_text_thread_timer[well]:
                return
        #with self.update_lock:
        #    self.update_text_thread_timer[well] = False
        #with self.update_lock:
        #    self.update_text_thread_timer[well] = False
        self.toggleRecordingCage(cage, well, well)
        #time.sleep(1)
        #if self.update_text_thread_timer[wellSelect]:
        #    self.toggleRecordingCage(cage, well)

    def toggleRecordingCage(self, cage: str, well: str="", weller_two: str=""):
        self.autoClose = True
        self.checkThreadTimers()

        self.buildCageMap() #if not self.builtIt: self.buildCageMap()
        self.setCameraRecordMap()
        if self.buttonHolder == "In synch":
            print("Please stop recording in synchronized mode.")
        else:
            wellSelect = ""
            if bool(self.cageMap[cage]['wellSelect']) and self.cageMap[cage]['wellSelect'] != 'notInSelect':
                wellSelect = self.cageMap[cage]['wellSelect']
            if wellSelect == "topLeftSelect":
                self.buttonHolder = "start rec top left"
                self.textHolder = "Record Top Left"
            elif wellSelect == "topRightSelect":
                self.buttonHolder = "start rec top right"
                self.textHolder = "Record Top Right"
            elif wellSelect == "botLeftSelect":
                self.buttonHolder = "start rec bottom left"
                self.textHolder = "Record Bottom Left"
            elif wellSelect == "botRightSelect":
                self.buttonHolder = "start rec bottom right"
                self.textHolder = "Record Bottom Right"

            
            self.controllerThread.toggleRecordingCage(cage, self.cageMap)
            if not self.cageMap[cage]['isRecording']:
                if not self.addedExp:
                    self.controllerThread.server.options.activeCams = self.controllerThread.\
                        server.clients.getClients("Camera")
                if self.cageListOpen:
                    strInsert = cage + ": is recording"
                    self.cagetext["recCombo"].setItemText(self.cagetext["recCombo"].currentIndex(), strInsert)
                if self.cageSettingsOpen['state']:
                    strInsert = cage + ": is recording"
                    self.cageSettingsText["cageCombo"].setItemText(self.cagetext["cageCombo"].currentIndex(), strInsert)
                if wellSelect:
                    if self.timing_per_cage_threads[wellSelect] is None:
                        time_started = time.time()
                        time_in = datetime.datetime.strptime(self.text[wellSelect].text(), "%H:%M:%S") 
                        time_in -= datetime.datetime(1900, 1, 1)
                        time_duration = time_in.total_seconds()
                        #if time_duration < 5.0:
                        #    print("must be greater than 5 seconds")
                        #    self.toggleRecordingCage(cage, well, weller_two)
                        self.timing_per_cage_threads[wellSelect] = threading.Thread(target=self.run_well_timer, args=(time_duration, time_started, wellSelect, cage))
                        self.timing_per_cage_threads[wellSelect].start()
                        with self.update_lock:
                            self.update_text_thread_timer[wellSelect] = True
                    self.buttons[self.buttonHolder].setText("Stop Recording")

                    #self.text[wellSelect] = 
                self.cageMap[cage]['isRecording'] = True
                
                #******IMPLEMENT A self.setRecordingBool(wellSelect, 1) setter to apply to toggleRecordingIndivid and toggleRecording
            else:
                if self.addedExp:
                    self.saveExpJson()
                    self.addedExp = False
                # Stop recording, prompt button to ask for start recording
                if self.cageListOpen:
                    strInsert = cage + ": is not recording"
                    self.cagetext["recCombo"].setItemText(self.cagetext["recCombo"].currentIndex(), strInsert)
                if self.cageSettingsOpen['state']:
                    strInsert = cage + ": is not recording"
                    self.cageSettingsText["cageCombo"].setItemText(self.cagetext["cageCombo"].currentIndex(), strInsert)
                if wellSelect and (not weller_two):
                    if self.update_text_thread_timer[wellSelect]:
                        with self.update_lock:
                            self.update_text_thread_timer[well] = False
                        self.timing_per_cage_threads[wellSelect].join()
                        self.timing_per_cage_threads[wellSelect] = None

                if wellSelect or weller_two: 
                    self.buttons[self.buttonHolder].setText(self.textHolder)

                self.cageMap[cage]['isRecording'] = False
                #******IMPLEMENT A self.setRecordingBool(wellSelect, 1) setter to apply to toggleRecordingIndivid and toggleRecording
                
                #someStillRecording = False
                #for k in self.cageMap:
                #    if self.cageMap[k]['isRecording']:
                #        someStillRecording = True
                #        break
                if not self.anythingRecording():
                    w = self.controllerThread.server.options.captureWidth
                    h = self.controllerThread.server.options.captureHeight
                    fps = self.controllerThread.server.clientOptions.fps # clientOption.fpsCage
                    f = self.controllerThread.server.options.baseDirectory
                    if self.timed:
                        if self.startRunThread is not None and \
                                self.startRunThread.isAlive():
                            self.startRunThread.cancel()
                        if self.endRunThread is not None and \
                                self.endRunThread.isAlive():
                            self.endRunThread.cancel()
                        if self.expChanged: self.controllerThread.server.options.baseDirectory = ''
                        if not self.addedExp: self.expInfo = {}
                        self.timed = False
                    gpac.run(width=w, height=h, fps=fps, filesDir=f)  # WILL NEED TO CHANGE THIS AFTER toggleRecordingCage and individual settings in server.py -> class < ClientOptions >  is implemented ****^^^^^^^
                    if self.timerTotalRun is not None and self.timerTotalRun.isAlive():
                        self.timerTotalRun.cancel()
                    if self.timeRemainRun is not None and self.timeRemainRun.isAlive():
                        self.timeRemainRun.cancel()
                self.controllerThread.server.options.activeCams = self.controllerThread.\
                        server.clients.getClients("Camera")


           
            
    def updateCageList(self) -> None:
        """Updates the drop down list in the GUI of cages in the individual cage recording functionality."""
        cage = 0
 
        from collections import OrderedDict
        otherCages = dict(OrderedDict(sorted(self.cageMap.items())))
        strInsert =""
        for cage in self.cageMap:
            if self.buttonHolder == "In synch":
                strInsert = cage + ": is in synch"
            elif self.cageMap[cage]['isRecording']:
                strInsert = cage + ": is recording"
            elif not self.cageMap[cage]['isRecording']:
                strInsert = cage + ": is not recording"
            if not strInsert:
                logger.error("Something is wrong in updating strInsert in updateCageList().")
            elif self.cageListOpen:
                self.cagetext["recCombo"].addItem(strInsert)
            elif self.cageSettingsOpen['state']:
                self.cageSettingsText["cageCombo"].addItem(strInsert)
            else:
                print("Neither self.cageListOpen nor self.cageSettingsOpen['state'] are true.")


    def updateWellList(self) -> None:
        """ Update well recording buttons with corresponding prompts depending on whether or not a specific cage is recording. """
        cage = 0
        hold = ""
        store = ""
        if not self.cageMap: self.buildCageMap()
        if not self.cageMap:
            print("Problem with updateWellList in launcher.py")
            return
        
        if self.buttonHolder == "In synch":
            self.setButtonOther()
        elif self.recording:
            self.buttonHolder = "In synch"
            self.setButtonOther()
        else:
            for cage in self.cageMap:
                if bool(self.cageMap[cage]['wellSelect']) and self.cageMap[cage]['wellSelect'] != 'notInSelect':
                    wellSelect = self.cageMap[cage]['wellSelect']
                    if wellSelect == "topLeftSelect":
                        hold = "start rec top left"
                        store = "Record Top Left"
                    elif wellSelect == "topRightSelect":
                        hold = "start rec top right"
                        store = "Record Top Right"
                    elif wellSelect == "botLeftSelect":
                        hold = "start rec bottom left"
                        store = "Record Bottom Left"
                    elif wellSelect == "botRightSelect":
                        hold = "start rec bottom right"
                        store = "Record Bottom Right"
                    if self.cageMap[cage]['isRecording']:
                        self.buttons[hold].setText("Stop Recording")
                    else:
                        self.buttons[hold].setText(store)
        

    def handleCageListButton(self) -> None:
        """Function opens up a list of cages that are either recording. Runs setter."""
        self.stopAllPlayers()
        self.buildCageMap()
        self.cageWindow = SettingsWindowIndivid(self.cageMap)
        self.cageWindow.show()
        self.cagebuttons = self.cageWindow.buttons
        self.cagetext = self.cageWindow.text
        self.cageListOpen = True
        self.updateCageList()
        self.cageWindow.show()

 
        self.runCageRecords()


    def runCageRecords(self) -> None:
        self.cagebuttons["okay"].clicked.connect(self.closeCageRecords)
        self.cagebuttons["record"].clicked.connect(self.toggler)
        self.cagebuttons["names"].clicked.connect(self.setCamNames)

    def closeCageRecords(self) -> None:
        self.cageListOpen = False
        self.cageWindow.close()
        self.cageUpdate()
        #self.buildCageMap()
        self.cageWindow = None

    def setCamNames(self) -> None:
        """
        A listener that opens the bundling system to assign cameras to names.
        """
        self.stopAllPlayers()
        bundler = bundle.Bundler(self.settings['camMap'], self.controllerThread, self.camPorts,
                                 self.updater, self.camUpdate, self.settings['grouptype'])
        bundler.runBundle()

    def toggler(self) -> None:
        substr = self.cagetext["recCombo"].currentText().split(':', 1)
        cage = substr[0]
        self.toggleRecordingCage(cage, "")
    

    def handleCageSettingsButton(self) -> None:
        """Function that opens a list of recordings and the settings for each cage."""
        if self.loadAsynchSettings:
            self.stopAllPlayers()
            self.cageSetter = cage_set.CageSetter(self.setSettingsCages, # type Dict
                                                  self.camUpdate,        # Callable
                                                  self.cageUpdate,       # Callable
                                                  self.buildCageMap,     # Callable
                                                  self.settings,         # type Dict   
                                                  self.defaultSett,      # type Dict
                                                  self.settingsCages,    # type Dict
                                                  self.cageMap,          # type Dict
                                                  self.camPorts,         # type Dict
                                                  self.loadAsynchSettings, # type immutable bool
                                                  self.cageSettingsOpen, # type Dict
                                                  self.buttonHolder,     # type immutable string
                                                  self.controllerThread  # server controller
                                                  )
            self.cageSetter.runCageSettings()
        else:
            print("Please press the load asynch settings button.")

    def toggleLoadSettings(self) -> None:
        cageRec = False
        self.buildCageMap()
        #self.camUpdate()
        # Setting individual cage settings for default

        self.stopAllPlayers()


        if bool(self.cageMap) and bool(self.settings):
            cage = 0
            for cage in self.cageMap:
                if self.cageMap[cage]['isRecording']:
                    cageRec = True
                    break
        else:
            print("No cages.")
            return
       
        #if not self.loadAsynchSettings:
        #     if self.recording or cageRec:
        #         print("Please stop recording to load asynchronous settings.")
        #     else:
        #        self.loadAsynchSettings = True
        #        self.controllerThread.server.cageSettingsOn = True
        #        self.setSettingsCages()
        #        self.buttons["loadSettings"].setText("Load Synchronous \n Recording Settings")
        #else:
        #    if self.recording or cageRec:
        #        print("Please stop recording to load synchronous settings.")
        #    else:
        #        self.loadAsynchSettings = False
        #        self.controllerThread.server.cageSettingsOn = False
        #        self.setSettings()
        #        self.buttons["loadSettings"].setText("Load Asynchronous \n Recording Settings")
        
            
    def openSettingsCagesJson(self) -> None:
        """Function attempts to open previous saved settings file for asynchronous recording and applies to current run."""
        defaultCages = copy.deepcopy(self.settings['camMap']['name'])
        cage = 0
        for cage in defaultCages:
            defaultCages[cage] = copy.deepcopy(self.defaultSett)

        for cage in defaultCages:
            if self.settings['camMap']['name']:
                defaultCages[cage]['camMap']['name'] = self.settings['camMap']['name']
            if self.settings['camMap']['camera']:
                defaultCages[cage]['camMap']['camera'] = self.settings['camMap']['camera']
        if bool(self.settings):

            if os.path.isfile(utils.settingsCagesFilePath(None)):
                with open(utils.settingsCagesFilePath(None), 'r') as f:
                    data = json.load(f)

                    for c in data:
                        self.settingsCages[c] = data[c]
                    for b in defaultCages.keys():
                        if b not in self.settingsCages.keys():
                            self.settingsCages[b] = defaultCages[b]
                        for c in defaultCages[b].keys():
                            if c not in self.settingsCages[b].keys():
                                self.settingsCages[b][c] = defaultCages[b][c]

                    for cage in self.settingsCages:
                        if not isinstance(self.settingsCages[cage]['vflip'], dict):
                            self.settingsCages[cage]['vflip'] = {'camera': {},
                                                                    'default': self.settingsCages[cage]['vflip']}
                        if 'zoom' in self.settingsCages[cage]:
                            pts = self.settingsCages[cage]['zoom']
                            del self.settingsCages[cage]['zoom']
                            pts.items()
                            self.settingsCages[cage]['zoom dimension'] = pts['default'][2:]
                            for cam, window in pts['camera'].items():
                                self.settingsCages[cage]['zoom location'][cam] = window[:2]
                                if window[2:] != self.settingsCages[cage]['zoom dimension']:
                                    logger.warning(
                                            "Warning: {} has dim {}, which was set as {} "
                                            "elsewhere. Check your settings file.".format(
                                                    cam, window[2:], self.settingsCages[cage]['zoom dimension']))
                                    self.settingsCages[cage]['zoom dimension'] = window[2:]
        else:
            self.after(defaultCages)

    def after(self, defaultCages: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]]) -> None:
        if not self.settingsCages: 
            self.settingsCages = copy.deepcopy(defaultCages)
            for cage in self.settingsCages:
                if self.settings['camMap']['name']:
                    self.settingsCages[cage]['camMap']['name'] = self.settings['camMap']['name']
                if self.settings['camMap']['camera']:
                    self.settingsCages[cage]['camMap']['camera'] = self.settings['camMap']['camera']


    def closeSettingsCagesJson(self) -> None:
        """Save current cage settings to a file."""
        strIn = None
        if utils.APPDATA_DIR:
            strIn = utils.APPDATA_DIR
        with open(utils.settingsCagesFilePath(strIn), 'w') as f:
            json.dump(self.settingsCages, f, sort_keys=True, indent=4)

    def setSettingsCages(self) -> None:
        """Function takes provided GUI settings and sets them at the server low level."""
        if not self.cageMap: self.buildCageMap()
        if not self.anythingRecording(): #self.running['recordingRunning']: #and not self.running['previewRunning']:
            if self.loadAsynchSettings:
                for cage in self.settingsCages:
                    self.controllerThread.server.options.segmentSize = self.settingsCages[cage]['len']
                    self.controllerThread.server.options.captureWidth = 1280
                    self.controllerThread.server.options.captureHeight = 720
                    self.controllerThread.server.sendSetCagesMessages(cage, self.cageMap, self.settingsCages)
                self.camUpdate()
            else:
                self.controllerThread.server.options.segmentSize = self.settings['len']
                self.controllerThread.server.options.captureWidth = 1280
                self.controllerThread.server.options.captureHeight = 720 
                clientOptions = self.controllerThread.server.clientOptions
                clientOptions.fps = self.settings['fps']
                clientOptions.shutterspeed = self.settings['shutter speed']

                clientOptions.brightness = self.settings['brightness']
                ##contraster$
                clientOptions.contrast = self.settings['contrast']

                clientOptions.iso = self.settings['iso']
                clientOptions.colorMode = self.settings['color']
                clientOptions.compression = self.settings['compression']
                clientOptions.autogain = self.settings['autogain']
                clientOptions.rotation = self.settings['rotation']
                clientOptions.zoomLocation = self.settings['zoom location']
                clientOptions.zoomDimension = self.settings['zoom dimension']
                clientOptions.vflip = self.settings['vflip'] 
                clientOptions.gain = self.settings['gain']
                clientOptions.camMap = self.settings['camMap']

                self.camUpdate()    





    def recordingStartedMessage(self, startTime: float) -> None:
        print("Started Recording at {} with delay of {} seconds.\n".format(datetime.datetime.now(), startTime))


    def handleSettingsButton(self) -> None:
        """Function opens up the settings choice panel and runs setter."""
        self.stopAllPlayers()
        self.setter = cam_set.Setter(self.setSettings,
                                     self.controllerThread,
                                     self.settings, self.camPorts,
                                     self.updater, self.camUpdate,
                                     self.cageUpdate)

        self.setter.runSettings()


    def addExp(self, tp: tuple=()) -> None:
        """Function opens GUI to add experiment and runs exp updater."""
        self.stopAllPlayers()

        if self.recording:
            #self.toggleRecording()
            print("Cant add experiment while recording")
            #self.expRunning = prev
            return
        else:
            for i in self.cageMap:
                if self.cageMap[i]['isRecording']:
                    #self.toggleRecordingCage(i, "")  #  remeber 'i' is a key of type str
                    print("Cant add experiment while recording")
                    #self.expRunning = prev
                    return
        self.expRunning = True
        #self.addedExp = True
        self.expUpdater = exp_updater.ExpUpdater(self, tp)
        self.expUpdater.runExpUpdater()
        #print("here %s" % self.expInfo)

    def openLegend(self) -> None:
        """
        Look at the CSV and make a legend out of it, attaching cameras to flies
        """
        if not self.csv or 'maps' not in self.csv or 'labels' not in self.csv \
                or not self.csv['maps'] or not self.csv['labels']:
            return
        ui = LegendGui()
        colToNum = {}
        cols = ["A", "B", "C", "D", "E", "F", "G", "H"]
        for a in range(0, len(cols)):
            colToNum[cols[a]] = a
        for obj in self.csv["maps"]:
            if 'WELLID' not in obj or not obj['WELLID']:
                return
            location = obj["WELLID"]
            col = colToNum[location[0]]
            row = int(location[1] + location[2]) - 1
            wid = ui.widgets[row][col]
            wid.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                              QtWidgets.QSizePolicy.MinimumExpanding)
            formLayout = QtWidgets.QFormLayout(wid)
            formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
            count = 0
            for key in self.csv["labels"]:
                if key not in ["WELLID", "WELLNBR", "PLATE"]:
                    label = QtWidgets.QLabel(wid)
                    label.setText(key)
                    formLayout.setWidget(count, QtWidgets.QFormLayout.LabelRole, label)
                    label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                        QtWidgets.QSizePolicy.MinimumExpanding)
                    value = obj[key]
                    if key != "__rest":
                        # __rest is the key for values without a key, which is an array
                        val = QtWidgets.QLabel(wid)
                        val.setText(value)
                        formLayout.setWidget(count, QtWidgets.QFormLayout.FieldRole, val)
                        val.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                          QtWidgets.QSizePolicy.MinimumExpanding)
                        count = count + 1
                    else:
                        for v in value:
                            val = QtWidgets.QLabel(wid)
                            val.setText(v)
                            formLayout.setWidget(count, QtWidgets.QFormLayout.FieldRole, val)
                            val.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                              QtWidgets.QSizePolicy.MinimumExpanding)
                            count = count + 1
            wid.adjustSize()
        # if the user wants the legend open and still be able to interact, remove modality
        # from legend_gui.py, change exec() to show(), and store the ui somewhere (avoids window
        # closing immediately from gc)
        ui.exec()


    def setSettings(self) -> None:
        """Function takes provided GUI settings and sets then at the server low level."""
        if not self.loadAsynchSettings and not self.anythingRecording(): #self.running['recordingRunning']:
            self.controllerThread.server.options.segmentSize = self.settings['len']
            ## clients v0.3 expect this, I think
            ## but I don't send this?

            self.controllerThread.server.options.captureWidth = 1280
            self.controllerThread.server.options.captureHeight = 720
            clientOptions = self.controllerThread.server.clientOptions

            clientOptions.fps = self.settings['fps']
            clientOptions.shutterspeed = self.settings['shutter speed']

            clientOptions.brightness = self.settings['brightness']
            ##contraster$
            clientOptions.contrast = self.settings['contrast']

            clientOptions.iso = self.settings['iso']
            clientOptions.colorMode = self.settings['color']
            clientOptions.compression = self.settings['compression']
            clientOptions.autogain = self.settings['autogain']
            clientOptions.rotation = self.settings['rotation']
            clientOptions.zoomLocation = self.settings['zoom location']
            clientOptions.zoomDimension = self.settings['zoom dimension']
            clientOptions.vflip = self.settings['vflip'] 
            clientOptions.gain = self.settings['gain']
            clientOptions.camMap = self.settings['camMap']
            
            self.camUpdate()
        if not self.settingsCages and bool(self.settings['camMap']['name']):
            for i in self.settings['camMap']['name']:
                if bool(self.settings['camMap']['name'][i].values()):
                    self.settingsCages.update([(i, copy.deepcopy(self.settings))])

    def startLauncher(self, argv: List[str]) -> None:
        """Function starts server and links to the front end logic."""
        self.openSettingsJson()
        self.openSettingsCagesJson()

        # Sets up SCORHE server
        self.controllerThread, _ = server.masterRunServer(argv)
        """:type: SCORHE_server.CameraServerController"""


        # Give server GUI determined settings for synchronous cameras
        self.setSettings()

        # Give server GUI determined settings for Asynchronous cameras 
        # however setSettingsCages will only be implemented to create the settingsCages map as
        # self.loadAsynchSettings is False at this point.

        self.setSettingsCages()


        self.window.setSelectionType(self.settings['grouptype'])
        # Sets up buttons
        self.setUpGUIButtons()
        time.sleep(0.1)
        # clientInfo dictionary
        # Declares an instance of the GUI information updater

        self.updater = updater.Updater(self.camUpdate, self.text,
                                       self.controllerThread,
                                       self.camPorts)
        # Starts the updater
        self.updater.update()
        # Sets up side info panel
        self.setUpInfoPanel()
        self.camUpdate()
        self.cageUpdate()

    def deleteTempFiles(self, filename: str) -> None:
        pass
        #import glob, pathlib

        #path_mod = os.getenv("USERPROFILE") + r"\AppData\Local\Temp\gpac_*"
        #for f in glob.glob(path_mod):
        #    #print("removing file {}".format(f))
        #    try:
        #        os.remove(f)
        #    except Exception as err:
        #        print("Still using file {}. Error from server.py: {}".format(f, err))

        #for file in glob.glob("*.h264"):
        #    try:
        #        os.remove(file)
        #    except Exception as err:
        #        print("Still using file {}".format(err))

############################################################################################################################################################################################################################################################################################################
    def stopAllRecording(self) -> None:
        """ Function that stops all specified recordings after a certain amount of time; called by endRunThread. Starts an auto shutdown feature. """
        print("called")

        #try:
        #    # self.controllerThread.server.forceStop()
        #    self.controllerThread.stopRecordingAllCages(self.cageMap)
        #except Exception as err:
        #    print(err)
        self.modStopAllRec()
        #if self.cageMap and not self.recording:
        #    for cage in self.cageMap:
        #        self.stopperAll(cage, "")



        # if self.recording:
            # print("Shouldn't Happen if asynch seperate")
            # self.toggleRecording()
        # if self.cageMap:
            # for cage in self.cageMap:
                # if self.cageMap[cage]['isRecording']:
                    # self.toggleRecordingCage(cage, "")
        #elif self.cageMap and self.builtIt:
        #    for cage in self.cageMap:
        #        if self.cageMap[cage]['isRecording']:
        #            if self.cageMap[cage]['wellSelect'] != 'notInSelect':
        #                self.toggleRecordingCage(cage, self.cageMap[cage]['wellSelect'])
        #            else:
        #                self.toggleRecordingCage(cage, "")
                    
        #if self.timerTotalRun is not None and self.timerTotalRun.isAlive():
        #    self.timerTotalRun.cancel()
        #if self.timeRemainRun is not None and self.timeRemainRun.isAlive():
        #    self.timeRemainRun.cancel()
        #if self.anythingRecording(): 
        #    raise Exception("Something went wrong in stopAllRecording in launcher.py")
        # After the modStopAllRec function is called we want to start the auto shutdown feature otherwise the app might run into an error if kept idle for too long
        # especially if we have the project running overnight.
        #self.autoShutdownToggler()

        #if (self.timeRemainStore < 0 or self.timeRemainStore == 0) and not self.inShutDown:
        #    #self.handleAutoShutdown()            
        #    self.automaticShutdown()
        #    #self.autoThread = threading.Thread(target=self.automaticShutdown)
        #    #self.autoThread.start()
        #    #self.autoThread.join()
    def stopperAll(self, cage: str, well: str) -> None:
        self.autoClose = True
        self.checkThreadTimers()

        self.buildCageMap() #if not self.builtIt: self.buildCageMap()
        self.setCameraRecordMap()
        if self.buttonHolder == "In synch":
            print("Please stop recording in synchronized mode.")
        else:
            wellSelect = ""
            if bool(self.cageMap[cage]['wellSelect']) and self.cageMap[cage]['wellSelect'] != 'notInSelect':
                wellSelect = self.cageMap[cage]['wellSelect']
            if wellSelect == "topLeftSelect":
                self.buttonHolder = "start rec top left"
                self.textHolder = "Record Top Left"
            elif wellSelect == "topRightSelect":
                self.buttonHolder = "start rec top right"
                self.textHolder = "Record Top Right"
            elif wellSelect == "botLeftSelect":
                self.buttonHolder = "start rec bottom left"
                self.textHolder = "Record Bottom Left"
            elif wellSelect == "botRightSelect":
                self.buttonHolder = "start rec bottom right"
                self.textHolder = "Record Bottom Right"
        if self.addedExp:
            self.saveExpJson()
            self.addedExp = False
        # Stop recording, prompt button to ask for start recording
        if self.cageListOpen:
            strInsert = cage + ": is not recording"
            self.cagetext["recCombo"].setItemText(self.cagetext["recCombo"].currentIndex(), strInsert)
        if self.cageSettingsOpen['state']:
            strInsert = cage + ": is not recording"
            self.cageSettingsText["cageCombo"].setItemText(self.cagetext["cageCombo"].currentIndex(), strInsert)
        if wellSelect:
            self.buttons[self.buttonHolder].setText(self.textHolder)
        self.cageMap[cage]['isRecording'] = False
        
        if not self.anythingRecording():
            w = self.controllerThread.server.options.captureWidth
            h = self.controllerThread.server.options.captureHeight
            fps = self.controllerThread.server.clientOptions.fps # clientOption.fpsCage
            f = self.controllerThread.server.options.baseDirectory
            if self.timed:
                if self.startRunThread is not None and \
                        self.startRunThread.isAlive():
                    self.startRunThread.cancel()
                if self.endRunThread is not None and \
                        self.endRunThread.isAlive():
                    self.endRunThread.cancel()
                if self.expChanged: self.controllerThread.server.options.baseDirectory = ''
                if not self.addedExp: self.expInfo = {}
                self.timed = False
            gpac.run(width=w, height=h, fps=fps, filesDir=f)  # WILL NEED TO CHANGE THIS AFTER toggleRecordingCage and individual settings in server.py -> class < ClientOptions >  is implemented ****^^^^^^^
            if self.timerTotalRun is not None and self.timerTotalRun.isAlive():
                self.timerTotalRun.cancel()
            if self.timeRemainRun is not None and self.timeRemainRun.isAlive():
                self.timeRemainRun.cancel()
        self.controllerThread.server.options.activeCams = self.controllerThread.\
                server.clients.getClients("Camera")   
                
                
    def modStopAllRec(self) -> None:
        """ Function that stops all specified recordings after a certain amount of time. """
        if self.recording:
            self.toggleRecording()
        if self.cageMap:
            for cage in self.cageMap:
                if self.cageMap[cage]['isRecording']:
                    self.toggleRecordingCage(cage, "")


        if self.timerTotalRun is not None and self.timerTotalRun.isAlive():
            self.timerTotalRun.cancel()
        if self.timeRemainRun is not None and self.timeRemainRun.isAlive():
            self.timeRemainRun.cancel()
        if self.anythingRecording(): 
            raise Exception("Something went wrong in stopAllRecording in launcher.py")

    #def autoShutdownToggler(self) -> None:
    #    """ Method that implements a timer of 30 seconds to automatically call self.shutdown() 
    #    on the application unless user action is recorded """
    #    if (self.time["end"] - datetime.datetime.now()).total_seconds() <= 0: 
    #        self.timerForShutdown()
    #        #time.sleep(10)
    #        #self.shutdown()
    #        self.shutdownThread = threading.Timer(10, self.shutdown)
    #        self.shutdownThread.start()
            

    #def timerForShutdown(self) -> None:
    #    if self.autoClose:
    #        self.secondsTillShutdown -= 1
    #        print("Seconds till auto shutdown: {}".format(int(self.secondsTillShutdown)))
    #        self.autoThread = threading.Timer(1, self.timerForShutdown)
    #        self.autoThread.start()
    #    else:
    #        if self.shutdownThread is not None and self.shutdownThread.isAlive():
    #            self.shutdownThread.cancel()
    #            self.shutdownThread = None
    #        if self.autoThread is not None and self.autoThread.isAlive():
    #            self.autoThread.cancel()
    #            self.autoThread = None


    #def autoShutdownStop(self) -> None:
    #    if self.shutdownThread is not None and self.shutdownThread.isAlive():
    #        self.shutdownThread.cancel()
    #        self.secondsTillShutdown = 30
    #    if self.autoThread is not None and self.autoThread.isAlive():
    #        self.autoThread.cancel()

    #def handleAutoShutdown(self) -> None:
    #    self.stopAllPlayers()
    #    #self.buildCageMap()
    #    self.shutWindow = ShutdownGui()
    #    self.shutWindow.show()
    #    self.shutbuttons = self.shutWindow.buttons
    #    self.shuttext = self.shutWindow.text
    #    self.sutWindow.show()


    #def automaticShutdown(self) -> None:

    #    if self.shutbuttons is None: self.handleAutoShutdown()
    #    self.secondsTillShutdown -= 1
    #    if self.secondsTillShutdown < 0:
    #        self.shutdown()
    #    else:
    #        self.shuttext["okay"].setText(str("Seconds Left Till Shutdown: " + self.secondsTillShutdown))
    #        self.shutdownThread = threading.Timer(1, automaticShutdown)
    #        self.shutdownThread.start()

############################################################################################################################################################################################################################################################################################################

    def shutdown(self, *_) -> None:
        """Shuts down launcher."""

        # Stop the GUI info updates
        #self.inShutDown = True
        w = self.controllerThread.server.options.captureWidth
        h = self.controllerThread.server.options.captureHeight
        fps = self.controllerThread.server.clientOptions.fps
        f = self.controllerThread.server.options.baseDirectory
        if self.timed:
            if self.startRunThread is not None and self.startRunThread.isAlive():
                self.startRunThread.cancel()
            if self.endRunThread is not None and self.endRunThread.isAlive():
                self.endRunThread.cancel()
            if self.timerTotalRun is not None and self.timerTotalRun.isAlive():
                self.timerTotalRun.cancel()
            if self.timeRemainRun is not None and self.timeRemainRun.isAlive():
                self.timeRemainRun.cancel()
            if self.recording:
                self.toggleRecording()

    

        ## 
        #self.terminateShutdownThread = threading.Timer(1, self.terminateThread)
        if self.autoThread is not None and self.autoThread.isAlive():
            self.autoThread.cancel()

        #if self.anythingRecording(): 
        #    self.modStopAllRec()
        self.updater.stop()


        # Save all camera client information
        self.closeSettingsJson()
        self.closeSettingsCagesJson()
        self.saveExpJson()
        # Restarts the clients
        self.controllerThread.reboot()
        try:
            gpac.run(width=w, height=h, fps=fps, filesDir=f)
        except Exception as err:
            logger.error("Couldn't Run; Premature shutdown; Error: {}".format(err))
        # Shutdown server
        self.controllerThread.close()


        #self.deleteTempFiles(f)

        sys.exit()


def main(argv: List[str]) -> None:
    """
    Main function initiates the launch object and main window GUI and runs them
    """
    app = QtWidgets.QApplication(argv)
    window = AcquisitionWindow()
    launch = LaunchObject(argv, window)
    #launch.startLauncher(argv)  # NC RECOMMENT
    window.closeEvent = launch.shutdown
    #if launch.shutdownThread is not None and launch.shutdownThread.isAlive():
    #    launch.shutdownThread.cancel()
    #window.showFullScreen()
    window.showNormal()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception as e:
        print(e)
