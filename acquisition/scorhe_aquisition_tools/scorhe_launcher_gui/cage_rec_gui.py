
# Noah Cubert July 2020 Intern: 
# All comments by this user will be denoted with an NC before the comment.
# For a single line comment denoted by '#' the following example will occur:
# # NC: This is a test comment
# For a block comment the following example will occur:
# '''
# NC: This is a test block comment
# '''


# This is called::

#       cage_set_gui.py

from PyQt5 import QtCore, QtWidgets
import copy
from typing import Callable, Dict, List, Tuple, Union

class SettingsWindowIndivid(QtWidgets.QDialog):
    def __init__(self, cageMap: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]]):
        #self.numcages = 0 if numcages is None else numcages
        self.cageMap = {'icage1': {'wellSelect': 'botLeftSelect', 'isRecording': False, 'main': '9e6b8f'}, 
                        'icage3': {'wellSelect': 'notInSelect', 'isRecording': False, 'main': '923210'}, 
                        'icage2': {'wellSelect': 'topRightSelect', 'isRecording': False, 'main': 'e6c71a'}, 
                        'icage4': {'wellSelect': 'topLeftSelect', 'isRecording': False, 'main': 'ab021a'}} if cageMap is None else cageMap
        QtWidgets.QDialog.__init__(self)
        self.resize(252, 350)
        self.setModal(True)
        self.gridLayout_4 = QtWidgets.QGridLayout(self)
        self.gridLayout_4.setObjectName("gridLayout_4")

        self.namesButton = QtWidgets.QPushButton(self)
        self.namesButton.setObjectName("namesButton")
        self.gridLayout_4.addWidget(self.namesButton, 3, 0, 1, 1)

        self.okayButton = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.okayButton.sizePolicy().hasHeightForWidth())
        self.okayButton.setSizePolicy(sizePolicy)
        self.okayButton.setObjectName("okayButton")
        self.gridLayout_4.addWidget(self.okayButton, 4, 2, 1, 1)
        self.recordButton = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.recordButton.sizePolicy().hasHeightForWidth())
        self.recordButton.setSizePolicy(sizePolicy)
        self.recordButton.setObjectName("recordButton")
        self.gridLayout_4.addWidget(self.recordButton, 4, 0, 1, 1)
        self.clipSettingsBox = QtWidgets.QGroupBox(self)
        self.clipSettingsBox.setObjectName("clipSettingsBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.clipSettingsBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.recordCageLabel = QtWidgets.QLabel(self.clipSettingsBox)
        self.recordCageLabel.setObjectName("recordCageLabel")
        self.gridLayout_2.addWidget(self.recordCageLabel, 1, 0, 1, 1)
        self.recCombo = QtWidgets.QComboBox(self.clipSettingsBox)
        self.recCombo.setObjectName("recCombo")
        self.recCombo.setMinimumSize(200, 30)
        self.recCombo.setMaximumSize(200, 30)
        cagename = 0
        self.recCombo.addItem("Select A Cage")
        self.gridLayout_2.addWidget(self.recCombo, 1, 1, 1, 1)
        self.gridLayout_4.addWidget(self.clipSettingsBox, 2, 0, 1, 3)
        self.retranslateUi()
        self.buttons = {"names": self.namesButton, "okay": self.okayButton, "record": self.recordButton}
        self.text = {"recCombo": self.recCombo}
         
    def retranslateUi(self):
        """Sets the text for all the UI elements."""
        self.setWindowTitle("Settings")
        self.namesButton.setText("Bundle Settings")
        self.okayButton.setText("OK")
        self.recordButton.setText("Record / Stop Recording")
        self.recordCageLabel.setText("Cage to Toggle Recording: ")



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SettingsWindowIndivid(None)
    window.show()
    sys.exit(app.exec_())
