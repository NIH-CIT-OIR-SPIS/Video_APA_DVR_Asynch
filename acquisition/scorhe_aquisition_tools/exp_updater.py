import csv
import datetime
import os

from PyQt5 import QtCore, QtWidgets

from scorhe_aquisition_tools.scorhe_launcher_gui import AddExpWindow
from scorhe_server import server
import utils


class ExpUpdater:
    """
    Object that exists to create and store information about an experiment. Controls the add experiment window.
    """

    def __init__(self, launcher, tp_in):
        # Create GUI window
        self.addExpWindow = AddExpWindow()
        # Default start and end time for the experiment
        #self.addExpWindow.dateTimeEdit.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(60))
        #self.addExpWindow.dateTimeEdit_2.setDateTime(QtCore.QDateTime.currentDateTime().addSecs(240))
        self.tp = tp_in
        #self.run_rec_after = launcher.toggleRecordingIndivid
        #self.run_rec_after = run_rec_after
        # Launcher main window GUI and information references
        self.expInfo = launcher.expInfo
        self.text = launcher.text
        self.settings = launcher.settings
        self.csv = launcher.csv
        self.time = launcher.time
        self.controllerThread = launcher.controllerThread  # type: server.CameraServerController
        self.camPorts = launcher.camPorts
        self.camMap = launcher.settings['camMap']
        self.launcher = launcher

        # Check if exp is possible
        self.setCorrectly = False  # type: bool
        
    def runExpUpdater(self) -> None:
        """Setup button for adding an experiment.

        This one button saves all the information on the page/sets up experiment

        :return: Nothing
        """
        self.addExpWindow.nextButton.clicked.connect(self.setUpExp)
        self.addExpWindow.csvOpener.clicked.connect(self.openCsv)


        self.addExpWindow.saveLocationOpener.clicked.connect(self.selectSaveLocation)
        if utils.APPDATA_DIR:
            strIn = utils.APPDATA_DIR
        else:
            utils.writeDefualtSavePath(None)
            strIn = utils.APPDATA_DIR
        self.addExpWindow.saveLocationLineEdit.setPlaceholderText('default: '+ strIn)




        for camClient in self.controllerThread.server.clients.getClients('Camera'):
            camID = camClient.cameraID
            if camID in self.camMap:
                camID = self.camMap['camera'][camID] + ' (' + camID + ')'
            self.addExpWindow.addCamera(camID)

        self.addExpWindow.show()

    def setUpExp(self) -> None:
        """
        Large chunk of code that saves all entered experiment information

        :return: Nothing
        """

        # Save name of exp
        if self.addExpWindow.text['exp name'].text() == '':
            self.expInfo['name'] = 'Untitled'
        else:
            self.expInfo['name'] = self.addExpWindow.text['exp name'].text()

        # Save start and end times of the exp
        #tempStart = self.addExpWindow.text['start'].dateTime().toPyDateTime()
        #tempEnd = self.addExpWindow.text['end'].dateTime().toPyDateTime()
        #self.time['start'] = tempStart
        #self.time['end'] = tempEnd

        currDate = datetime.datetime.now()
        if self.addExpWindow.text['exp name'].text() != '': #and currDate < tempStart < tempEnd:
            # If dates are set correctly
            self.setCorrectly = True
            #self.expInfo['start'] = str(tempStart.strftime('%m/%d/%Y @ %H:%M:%S'))
            #self.expInfo['end'] = str(tempEnd.strftime('%m/%d/%Y @ %H:%M:%S'))
            save = self.addExpWindow.text['save path'].text()
            
            if not save:
                #self.expInfo['saveDir'] = utils.APPDATA_DIR
                if utils.APPDATA_DIR:
                    save = utils.APPDATA_DIR # NC edits
                else:
                    utils.writeDefualtSavePath(None)
                    save = utils.APPDATA_DIR
                #print(utils.APPDATA_DIR)
            self.expInfo['saveDir'] = os.path.join(save,
                                                   'experiments',
                                                   self.expInfo['name'],
                                                   '')
            #print("Save expInfo Directory %s" % self.expInfo['saveDir'])

            self.controllerThread.server.options.baseDirectory = \
                os.path.join(self.expInfo['saveDir'], 'videos')

            # Create the folder on the local system for this experiment
            if not os.path.exists(self.controllerThread.server.options.baseDirectory):
                os.makedirs(self.controllerThread.server.options.baseDirectory)

            self.expInfo['path'] = self.addExpWindow.text['save path'].text()
            self.expInfo['csv'] = self.csv
            self.expInfo['cams'] = self.camPorts  # {'id':port}
            self.expInfo['camNames'] = self.camMap
            # have something that has the mapping from camera name to camera id
            # Next few lines set all experiment information
            # Set experiment name and times
            self.text['exp name'].setText(self.expInfo['name'])
            #self.text['start time'].setText(self.expInfo['start'])
            #self.text['end time'].setText(self.expInfo['end'])

        # Exit the add exp window
        self.exitMainExp()

    def openCsv(self) -> None:
        """
        Opens the csv file used to store data on the monitored animals and
        stores it locally.

        :return: Nothing
        """
        text, _ = QtWidgets.QFileDialog.getOpenFileName(self.addExpWindow,
                                                        'Open a file', '.',
                                                        'CSV (*.csv)')
        if text:
            self.addExpWindow.csvInputLineEdit.setText(text)
            with open(text, 'r') as f:
                reader = csv.DictReader(f, restkey='__rest', restval='__Unknown',
                                        delimiter=',', skipinitialspace=True)
                self.csv['maps'] = [row for row in reader]
                self.csv['labels'] = reader.fieldnames

    def selectSaveLocation(self) -> None:
        """Opens a file dialog to select the directory to store the experiment data.

        :return: Nothing
        """
        text = QtWidgets.QFileDialog.getExistingDirectory(
                self.addExpWindow, 'Select a directory',
                os.getenv('USERPROFILE'))
        #rint(text)
        if text:
            self.addExpWindow.saveLocationLineEdit.setText(text)
            self.expInfo['saveDir'] = text
    

       
    def exitMainExp(self) -> None:
        """Exit the add exp window

        :return: Nothing
        """
        if self.setCorrectly:
            self.controllerThread.server.expName = self.expInfo['name']
            #self.controllerThread.server.startTime = self.expInfo['start']

            #self.controllerThread.server.endTime = self.expInfo['end']
 
            self.controllerThread.server.sendExpInfoMessages()
            self.settings['dir'] = self.expInfo['name']
            active = []
            for i in range(self.addExpWindow.camList.count()):
                it = self.addExpWindow.camList.item(i)
                if it.checkState() == QtCore.Qt.Checked:
                    active.append(it.text())
            self.settings['active cams'] = active
            self.controllerThread.server.options.activeCams = active
            #self.launcher.runTimer()   
            self.addExpWindow.close()
            self.launcher.addedExp = True
            self.launcher.expRunning = False
            if self.tp:
                fi, wellSelect = self.tp
                self.launcher.toggleRecordingCage(fi, wellSelect)
        else:
            QtWidgets.QMessageBox.warning(None, 'Exp not set correctly!',
                                          'Exp not set correctly!\nMake sure '
                                          'the experiment has a name, that the '
                                          'start time is in the future, and that '
                                          'the end time is after the start time.')
