from PyQt5 import QtCore, QtWidgets


class AddExpWindow(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setObjectName("ExpSetUp")
        self.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(self)

        # exp name
        self.expNameLabel = QtWidgets.QLabel(self)
        self.gridLayout.addWidget(self.expNameLabel, 0, 0, 1, 2)
        self.expName = QtWidgets.QLineEdit(self)
        self.gridLayout.addWidget(self.expName, 1, 0, 1, 2)

        # start and end time
        #self.startTimeLabel = QtWidgets.QLabel(self)
        #self.gridLayout.addWidget(self.startTimeLabel, 2, 0, 1, 2)
        #self.dateTimeEdit = QtWidgets.QDateTimeEdit(self)
        #self.gridLayout.addWidget(self.dateTimeEdit, 3, 0, 1, 2)
        #self.endTimeLabel = QtWidgets.QLabel(self)
        #self.gridLayout.addWidget(self.endTimeLabel, 4, 0, 1, 2)
        #self.dateTimeEdit_2 = QtWidgets.QDateTimeEdit(self)
        #self.gridLayout.addWidget(self.dateTimeEdit_2, 5, 0, 1, 2)

        # csv selection
        self.label_2 = QtWidgets.QLabel(self)
        self.gridLayout.addWidget(self.label_2, 6, 0, 1, 2)
        self.csvInputLineEdit = QtWidgets.QLineEdit(self)
        self.csvInputLineEdit.setReadOnly(True)
        self.gridLayout.addWidget(self.csvInputLineEdit, 7, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 8, 0, 1, 1)
        self.csvOpener = QtWidgets.QPushButton(self)
        self.gridLayout.addWidget(self.csvOpener, 8, 1, 1, 1)

        # save location selection
        self.saveLocationLabel = QtWidgets.QLabel(self)
        self.gridLayout.addWidget(self.saveLocationLabel, 9, 0, 1, 2)
        self.saveLocationLineEdit = QtWidgets.QLineEdit(self)
        self.saveLocationLineEdit.setReadOnly(True)
        self.gridLayout.addWidget(self.saveLocationLineEdit, 10, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 11, 0, 1, 1)
        self.saveLocationOpener = QtWidgets.QPushButton(self)
        self.gridLayout.addWidget(self.saveLocationOpener, 11, 1, 1, 1)

        self.camListLabel = QtWidgets.QLabel(self)
        self.gridLayout.addWidget(self.camListLabel, 0, 2, 1, 3)
        self.camList = QtWidgets.QListWidget(self)
        self.gridLayout.addWidget(self.camList, 1, 2, 10, 2)
        self.allCams = QtWidgets.QPushButton(self)
        from functools import partial

        def check(lst, on):
            for i in range(lst.count()):
                lst.item(i).setCheckState(QtCore.Qt.Checked if on else QtCore.Qt.Unchecked)
        self.allCams.clicked.connect(partial(check, self.camList, True))
        self.gridLayout.addWidget(self.allCams, 11, 2, 1, 1)
        self.noCams = QtWidgets.QPushButton(self)
        self.noCams.clicked.connect(partial(check, self.camList, False))
        self.gridLayout.addWidget(self.noCams, 11, 3, 1, 1)

        # next button, with spacer for alignment
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 12, 0, 1, 1)
        self.nextButton = QtWidgets.QPushButton(self)
        self.gridLayout.addWidget(self.nextButton, 12, 1, 1, 1)

        self.retranslateUi()
        self.buttons = {"selector": self.csvOpener, "next": self.nextButton,
                        "save": self.saveLocationOpener}
        self.text = {"exp name": self.expName, 
                     #"start": self.dateTimeEdit,
                     #"end": self.dateTimeEdit_2, 
                     "csv path": self.csvInputLineEdit,
                     "save path": self.saveLocationLineEdit}

    def retranslateUi(self):
        self.setWindowTitle("Form")
        self.expNameLabel.setText("Experiment Name")
        #self.startTimeLabel.setText("Start Time")
        #self.endTimeLabel.setText("End Time")
        self.label_2.setText("Please select a CSV for configuration:")
        self.csvInputLineEdit.setPlaceholderText("path to csv")
        self.csvOpener.setText("Select CSV")
        self.saveLocationLabel.setText("Set save location:")
        self.saveLocationLineEdit.setPlaceholderText("default:")
        self.saveLocationOpener.setText("Select Save Location")
        self.camListLabel.setText("Active Cameras:")
        self.allCams.setText("Select All")
        self.noCams.setText("Select None")
        self.nextButton.setText("Next")

    def addCamera(self, camStr, checked=True):
        item = QtWidgets.QListWidgetItem(camStr, self.camList)
        item.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        self.camList.addItem(item)


class Warn(QtWidgets.QWidget):
    def __init__(self, message):
        QtWidgets.QWidget.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.resize(150, 50)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(QtCore.QRect(20, 20, 171, 16))
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setGeometry(QtCore.QRect(600, 660, 400, 20))
        self.label.setText(message)
        self.label_2.setText("Beam me up Scotty, there's no intelligent life here...")


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = AddExpWindow()
    window.show()
    sys.exit(app.exec_())
