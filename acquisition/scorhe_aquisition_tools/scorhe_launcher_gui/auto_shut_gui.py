
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

from PyQt5 import QtCore, QtWidgets, QtGui
#import copy
#from typing import Callable, Dict, List, Tuple, Union

class ShutdownGui(QtWidgets.QDialog):
    def __init__(self):
        ##self.numcages = 0 if numcages is None else numcages
        #self.cageMap = {'icage1': {'wellSelect': 'botLeftSelect', 'isRecording': False, 'main': '9e6b8f'}, 
        #                'icage3': {'wellSelect': 'notInSelect', 'isRecording': False, 'main': '923210'}, 
        #                'icage2': {'wellSelect': 'topRightSelect', 'isRecording': False, 'main': 'e6c71a'}, 
        #                'icage4': {'wellSelect': 'topLeftSelect', 'isRecording': False, 'main': 'ab021a'}} if cageMap is None else cageMap
        QtWidgets.QDialog.__init__(self)
        self.resize(252, 350)
        self.setModal(True)
        self.gridLayout_4 = QtWidgets.QGridLayout(self)
        self.gridLayout_4.setObjectName("gridLayout_4")

        self.autoShutdownToggle = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.autoShutdownToggle.sizePolicy().hasHeightForWidth())
        self.autoShutdownToggle.setSizePolicy(sizePolicy)
        self.autoShutdownToggle.setObjectName("autoShutdownToggle")
        self.gridLayout_4.addWidget(self.autoShutdownToggle)

        font = QtGui.QFont()
        # font.setPointSize(-1)
        font.setBold(True)
        font.setItalic(False)
        font.setWeight(87)
        self.autoShutdownToggle.setFont(font)
        self.autoShutdownToggle.setAutoFillBackground(False)
        self.autoShutdownToggle.setStyleSheet("QPushButton {\n"
                                       "background: #f00;\n"
                                       "background-color: qlineargradient(spread:pad, x1:0.489, y1:0.954, x2:0.494, "
                                       "y2:0.017, stop:0.0340909 rgba(91, 0, 0, 255), stop:1 rgba(255, 0, 0, 255));\n "
                                       "border-color: black;\n"
                                       "color: #fff;\n"
                                       "font: normal 700 24px/1 \"Calibri\", sans-serif;\n"
                                       "text-align: center;\n"
                                       "}\n"
                                       "")
        self.autoShutdownToggle.setAutoDefault(False)
        self.autoShutdownToggle.setDefault(False)
        self.autoShutdownToggle.setFlat(False)

        self.autoTimer = QtWidgets.QLabel(self)
        #self.autoTimer.setMinimumSize(160, 40)
        #self.autoTimer.setMaximumSize(160, 40)
        self.autoTimer.setFont(font)
        self.gridLayout_4.addWidget(self.autoTimer)




        self.retranslateUi()
        self.buttons = { "okay": self.autoShutdownToggle}
        self.text = {"timer": self.autoTimer}
         
    def retranslateUi(self):
        """Sets the text for all the UI elements."""
        self.setWindowTitle("Auto Shutdown Window")
        self.autoShutdownToggle.setText("Stop Auto Shutdown")
        self.autoTimer.setText("Seconds Left Till Shutdown: 30")




if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = ShutdownGui()
    window.show()
    sys.exit(app.exec_())
