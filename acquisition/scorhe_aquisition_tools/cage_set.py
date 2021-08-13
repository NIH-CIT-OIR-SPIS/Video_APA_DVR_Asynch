import os
import platform
import sys
import copy

from PyQt5 import QtCore, QtWidgets
from typing import Callable, Dict, List, Tuple, Union


import utils
from scorhe_server import server
from scorhe_aquisition_tools.scorhe_launcher_gui import SettingsWindowOther

class CageSetter:
    """
    Setter object helps the user modify the settings of the experiment.
    """
   
    def __init__(self,
                 setSettingsCages: Callable[[], None],
                 camUpdate: Callable[[], None],
                 cageUpdate: Callable[[], None],
                 buildCageMap: Callable[[], None],
                 settings: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]],
                 defaultSett: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]],
                 settingsCages: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]],
                 cageMap: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]],
                 camPorts: Dict[str, int],
                 loadAsynchSettings: bool,
                 cageSettingsOpen: Dict[str, bool],
                 buttonHolder: str,
                 controllerThread: server.CameraServerController,
                 ):
        self.setSettingsCages = setSettingsCages
        self.controllerThread = controllerThread
        self.camPorts = camPorts
        self.camUpdate = camUpdate
        self.cageUpdate = cageUpdate
        self.buildCageMap = buildCageMap

        # Vars
        self.buttonHolder = buttonHolder
        self.settings = settings
        self.defaultSett = defaultSett
        self.settingsCages = settingsCages
        self.cageMap = cageMap
        self.cageSettingsOpen = cageSettingsOpen
        self.loadAsynchSettings = loadAsynchSettings

        # Create GUI
        self.buildCageMap()
        self.cageSettingsWindow = SettingsWindowOther(self.cageMap)
        self.cageSettingsWindow.show()
        # Reference to GUI attributes
        self.cageSettingsButtons = self.cageSettingsWindow.buttons
        self.cageSettingsText = self.cageSettingsWindow.text
        # Our own variables set
        self.defaultCager = False
        self.cageSettingsOpen['state'] = True

        # Run Functions
        self.updateCageList()
        self.updaterCageSettings()
        self.cageSettingsWindow.show()


    def runCageSettings(self) -> None:
        self.cageSettingsButtons["close"].clicked.connect(self.closeSaveCageSettings)
        self.cageSettingsButtons["default"].clicked.connect(self.setDefaultCageSettings)
        self.cageSettingsButtons["setCageButton"].clicked.connect(lambda: self.saveCageSettings(True))
        self.cageSettingsButtons["compression"].valueChanged.connect(self.compressionChangedCage)
        self.cageSettingsText["cageCombo"].currentIndexChanged.connect(self.updaterCageSettings)
        self.cageSettingsWindow.saveLocationOpener.clicked.connect(self.selectSaveLocationCageSettings)
        self.updaterCageSettings()

    def compressionChangedCage(self) -> None:
        """This function is called when the compression setting is changed.

        This updates the text in the setting for the compression.
        """
        if self.cageSettingsText["cageCombo"].currentText().find("Select A Cage") != -1:
            #If the drop down menu contains a cage and 
            print("Please select a cage from the drop down menu. (Cage Settings)")
        elif self.cageSettingsText["cageCombo"].currentText().find(":") == -1:
            print('Please remove the special character \':\' from your cage name.')
        else:
            substr = self.cageSettingsText["cageCombo"].currentText().split(':', 1)
            cage = substr[0]
            self.cageSettingsButtons["compression"].setValue(self.settingsCages[cage]["compression"])
            new = self.settingsCages[cage]["compression"]
            self.cageSettingsText["compressionLabel"].setText("Compression: {}x".format(new))

    def closeSaveCageSettings(self) -> None:
        self.saveCageSettings(False)
        self.setSettingsCages()
        self.cageSettingsOpen['state'] = False
        self.cageSettingsWindow.close()
        self.cageUpdate()
        self.cageSettingsWindow = None

    def saveCageSettings(self, setCage: bool) -> None:
        """ This function saves the cage settings for the specified selected cage immediately. However this doesn't close the cageSettingsWindow. """
        if self.cageSettingsText["cageCombo"].currentText().find("Select A Cage") != -1:
            #If the drop down menu contains a cage and 
            print("Please select a cage from the drop down menu. (Cage Settings)")
        elif self.cageSettingsText["cageCombo"].currentText().find(":") == -1:
            print('Please remove the special character \':\' from your cage name.')
        else:
            substr = self.cageSettingsText["cageCombo"].currentText().split(':', 1)
            cage = substr[0]
            if not self.settingsCages:
                self.setDefaultCageSettings()
            self.settingsCages[cage]['len'] = self.cageSettingsText["clip len"].value()
            self.settingsCages[cage]['fps'] = self.cageSettingsText["fps"].value()


            self.settingsCages[cage]['shutter speed'] = self.cageSettingsText["shutter speed"].value()

            ##contraster$
            self.settingsCages[cage]['brightness'] = self.cageSettingsText["brightness"].value()
            self.settingsCages[cage]['contrast'] = self.cageSettingsText['contrast'].value()

            self.settingsCages[cage]['iso'] = self.cageSettingsButtons["iso"].currentText()
            self.settingsCages[cage]['compression'] = self.cageSettingsButtons["compression"].value()
            self.settingsCages[cage]['color'] = self.cageSettingsButtons["color"].isChecked()
            self.settingsCages[cage]['vflip']['default'] = self.cageSettingsButtons["vflip"].isChecked()
            self.settingsCages[cage]['reso'] = self.cageSettingsButtons["reso"].currentText()
            substr = self.cageSettingsButtons["reso"].currentText().split('x', 1)
            self.settingsCages[cage]['zoom dimension'] = (int(substr[0]), int(substr[1]))
            self.settingsCages[cage]['autogain'] = self.cageSettingsButtons['autogain'].isChecked()
            self.settingsCages[cage]['gain'] = self.cageSettingsText["gain"].value()

            if setCage: 
                self.setSettingsCages()

    def updaterCageSettings(self) -> None:
        """
        Fill out the settings[cage] panel with the current settings[cage]
        """
        if not self.settingsCages:
            defaultCages = copy.deepcopy(self.settings['camMap']['name'])
            cage = 0
            for cage in defaultCages:
                defaultCages[cage] = copy.deepcopy(self.settings)
            self.settingsCages = copy.deepcopy(defaultCages)
            for cage in self.settingsCages:
                if self.settings['camMap']['name']:
                    self.settingsCages[cage]['camMap']['name'] = self.settings['camMap']['name']
                if self.settings['camMap']['camera']:
                    self.settingsCages[cage]['camMap']['camera'] = self.settings['camMap']['camera']
            self.defaultCager = True

        if self.cageSettingsText["cageCombo"].currentText().find("Select A Cage") != -1 and not self.defaultCager:
            #If the drop down menu contains a cage and 
            print("Please select a cage from the drop down menu. (Cage Settings)")
        elif self.cageSettingsText["cageCombo"].currentText().find(":") == -1 and not self.defaultCager:
            print('Please remove the special character \':\' from your cage name.')
        else:
            if self.defaultCager:
                if list(self.settingsCages)[0]:
                    cage = list(self.settingsCages)[0]
            else:
                substr = self.cageSettingsText["cageCombo"].currentText().split(':', 1)
                cage = substr[0]
            self.cageSettingsText["clip len"].setValue(self.settingsCages[cage]['len'])
            self.cageSettingsText["fps"].setValue(self.settingsCages[cage]['fps'])


            self.cageSettingsText["shutter speed"].setValue(self.settingsCages[cage]['shutter speed'])

            ##contraster$
            self.cageSettingsText["brightness"].setValue(self.settingsCages[cage]['brightness'])
            self.cageSettingsText["contrast"].setValue(self.settingsCages[cage]['contrast'])

            self.cageSettingsText["gain"].setValue(self.settingsCages[cage]['gain'])
            index = self.cageSettingsButtons["iso"].findText(self.settingsCages[cage]['iso'], QtCore.Qt.MatchFixedString)
            self.cageSettingsButtons["iso"].setCurrentIndex(index)
            self.cageSettingsButtons["compression"].setValue(self.settingsCages[cage]['compression'])
            self.cageSettingsButtons["color"].setChecked(self.settingsCages[cage]['color'])
            self.cageSettingsButtons["vflip"].setChecked(bool(id(self.settingsCages[cage]['vflip']) % 2))
            self.cageSettingsButtons["autogain"].setChecked(self.settingsCages[cage]['autogain'])
            index = self.cageSettingsButtons["reso"].findText(self.settingsCages[cage]['reso'], QtCore.Qt.MatchFixedString)
            self.cageSettingsButtons["reso"].setCurrentIndex(index)

    def setDefaultCageSettings(self) -> None:
        """ Set default settings for cages. """
        self.defaultCager = True
        defaultCages = copy.deepcopy(self.settings['camMap']['name'])
        cage = 0
        for cage in defaultCages:
            defaultCages[cage] = copy.deepcopy(self.defaultSett)
        self.settingsCages = copy.deepcopy(defaultCages)

        for cage in self.settingsCages:
            if self.settings['camMap']['name']:
                self.settingsCages[cage]['camMap']['name'] = self.settings['camMap']['name']
            if self.settings['camMap']['camera']:
                self.settingsCages[cage]['camMap']['camera'] = self.settings['camMap']['camera']
        self.setSettingsCages()
        if self.cageSettingsOpen['state']: 
            self.updaterCageSettings()

    def selectSaveLocationCageSettings(self) -> str:
        """
        Sets where the file will be saved
        """
        passed = False
        tempFile = QtWidgets.QFileDialog.getExistingDirectory(self.cageSettingsWindow, 'Select a directory', os.getenv('USERPROFILE'))
        utils.writeDefualtSavePath(tempFile)

        if tempFile and passed:
            self.cageSettingsWindow.saveLocationLineEdit.setText(tempFile)
            return tempFile
        else:
            return ""

    def updateCageList(self) -> None:
        """Updates the drop down list in the GUI of cages in the individual cage recording functionality."""
        cage = 0
        from collections import OrderedDict
        otherCages = dict(OrderedDict(sorted(self.cageMap.items())))
        for cage in self.cageMap:
            if self.buttonHolder == "In synch":
                strInsert = cage + ": is in synch"
            elif self.cageMap[cage]['isRecording']:
                strInsert = cage + ": is recording"
            elif not self.cageMap[cage]['isRecording']:
                strInsert = cage + ": is not recording"
            if self.cageSettingsOpen['state'] and strInsert:
                self.cageSettingsText["cageCombo"].addItem(strInsert)
            else:
                print("Neither self.cageListOpen nor self.cageSettingsOpen['state'] are true.")
    




