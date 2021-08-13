
# Noah Cubert July 2020 Intern: 
# All comments by this user will be denoted with an NC before the comment.
# For a single line comment denoted by '#' the following example will occur:
# # NC: This is a test comment
# For a block comment the following example will occur:
# '''
# NC: This is a test block comment
# '''




from PyQt5 import QtCore, QtWidgets


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self):
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
        self.defaultButton = QtWidgets.QPushButton(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.defaultButton.sizePolicy().hasHeightForWidth())
        self.defaultButton.setSizePolicy(sizePolicy)
        self.defaultButton.setObjectName("defaultButton")
        self.gridLayout_4.addWidget(self.defaultButton, 4, 0, 1, 1)
        self.clipSettingsBox = QtWidgets.QGroupBox(self)
        self.clipSettingsBox.setObjectName("clipSettingsBox")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.clipSettingsBox)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.clipLength = QtWidgets.QSpinBox(self.clipSettingsBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.clipLength.sizePolicy().hasHeightForWidth())
        self.clipLength.setSizePolicy(sizePolicy)
        self.clipLength.setMinimumSize(QtCore.QSize(50, 0))
        self.clipLength.setMaximumSize(QtCore.QSize(50, 16777215))
        self.clipLength.setBaseSize(QtCore.QSize(50, 0))
        self.clipLength.setObjectName("clipLength")
        self.gridLayout_2.addWidget(self.clipLength, 0, 1, 1, 1)
        self.minuteLabel = QtWidgets.QLabel(self.clipSettingsBox)
        self.minuteLabel.setObjectName("minuteLabel")
        self.gridLayout_2.addWidget(self.minuteLabel, 0, 2, 1, 1)
        self.segLengthLabel = QtWidgets.QLabel(self.clipSettingsBox)
        self.segLengthLabel.setObjectName("segLengthLabel")
        self.gridLayout_2.addWidget(self.segLengthLabel, 0, 0, 1, 1)
        self.gridLayout_4.addWidget(self.clipSettingsBox, 2, 0, 1, 3)
        self.videoSettingsBox = QtWidgets.QGroupBox(self)
        self.videoSettingsBox.setObjectName("videoSettingsBox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.videoSettingsBox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.colorLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.colorLabel.setObjectName("colorLabel")
        self.gridLayout_3.addWidget(self.colorLabel, 6, 0, 1, 1)
        self.isoLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.isoLabel.setObjectName("isoLabel")
        self.gridLayout_3.addWidget(self.isoLabel, 1, 0, 1, 1)
        self.compressionSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.compressionSlider.setObjectName("compressionSlider")
        self.compressionSlider.setValue(1)
        self.compressionSlider.setMinimum(1)
        self.compressionSlider.setMaximum(10)
        self.gridLayout_3.addWidget(self.compressionSlider, 2, 1, 1, 1)
        self.colorCombo = QtWidgets.QCheckBox(self.videoSettingsBox)
        self.colorCombo.setObjectName("colorCombo")
        self.gridLayout_3.addWidget(self.colorCombo, 6, 1, 1, 1)
        self.frameSec = QtWidgets.QSpinBox(self.videoSettingsBox)
        self.frameSec.setMinimum(15)
        self.frameSec.setSingleStep(1)
        self.frameSec.setMaximum(120)
        self.frameSec.setObjectName("frameSec")
        self.gridLayout_3.addWidget(self.frameSec, 0, 1, 1, 1)
        self.gain = QtWidgets.QSpinBox(self.videoSettingsBox)
        self.gain.setObjectName("gain")
        self.gridLayout_3.addWidget(self.gain, 7, 1, 1, 1)
        self.compressionLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.compressionLabel.setObjectName("compressionLabel")
        self.gridLayout_3.addWidget(self.compressionLabel, 2, 0, 1, 1)
        self.resolutionLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.resolutionLabel.setObjectName("resolutionLabel")
        self.gridLayout_3.addWidget(self.resolutionLabel, 3, 0, 1, 1)
        
        self.isoCombo = QtWidgets.QComboBox(self.videoSettingsBox)
        self.isoCombo.setObjectName("isoCombo")
        self.isoCombo.addItem("")
        self.isoCombo.addItem("")
        self.isoCombo.addItem("")
        self.isoCombo.addItem("")
        self.isoCombo.addItem("")
        self.isoCombo.addItem("")
        self.gridLayout_3.addWidget(self.isoCombo, 1, 1, 1, 1)

        #************************NC edit
        self.resolutionCombo = QtWidgets.QComboBox(self.videoSettingsBox)
        self.resolutionCombo.setObjectName("resolutionCombo")
        self.resolutionCombo.addItem("")
        self.resolutionCombo.addItem("")
        self.resolutionCombo.addItem("")
        self.gridLayout_3.addWidget(self.resolutionCombo, 3, 1, 1, 1)
        
        # Added 1-29-21
        self.shutterSpeedLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.shutterSpeedLabel.setObjectName("shutterSpeedLabel")
        self.gridLayout_3.addWidget(self.shutterSpeedLabel, 4, 0, 1, 1)

        self.shutterSpeedBox = QtWidgets.QSpinBox(self.videoSettingsBox)
        self.shutterSpeedBox.setMinimum(0)
        self.shutterSpeedBox.setSingleStep(10)
        self.shutterSpeedBox.setMaximum(200000000)
        self.shutterSpeedBox.setObjectName("shutterSpeedBox")
        self.gridLayout_3.addWidget(self.shutterSpeedBox, 4, 1, 1, 1)



        self.vflipCheck = QtWidgets.QCheckBox(self.videoSettingsBox)
        self.vflipCheck.setObjectName("vflipCheck")
        self.gridLayout_3.addWidget(self.vflipCheck, 5, 1, 1, 1)
        self.frameSecLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.frameSecLabel.setObjectName("frameSecLabel")
        self.gridLayout_3.addWidget(self.frameSecLabel, 0, 0, 1, 1)
        self.autogainCheck = QtWidgets.QCheckBox(self.videoSettingsBox)
        self.autogainCheck.setObjectName("autogainCheck")
        self.gridLayout_3.addWidget(self.autogainCheck, 5, 0, 1, 1)

        #********************** NC edit **************************
        #self.sdCheck = QtWidgets.QCheckBox(self.videoSettingsBox)
        #self.sdCheck.setObjectName("sdCheck")
        #self.gridLayout_3.addWidget(self.sdCheck, 5, 1, 1, 1)
        #**************************************************



        self.gainLabel = QtWidgets.QLabel(self.videoSettingsBox)
        self.gainLabel.setObjectName("gainLabel")
        self.gridLayout_3.addWidget(self.gainLabel, 7, 0, 1, 1)
        self.gridLayout_4.addWidget(self.videoSettingsBox, 1, 0, 1, 3)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_4.addItem(spacerItem, 4, 1, 1, 1)





        #************************ NC edit ******************************
        self.saveLocationLabel = QtWidgets.QLabel(self)
        self.gridLayout_3.addWidget(self.saveLocationLabel, 10, 0, 1, 2)
        self.saveLocationLineEdit = QtWidgets.QLineEdit(self)
        self.saveLocationLineEdit.setReadOnly(True)
        self.gridLayout_3.addWidget(self.saveLocationLineEdit, 11, 0, 1, 2)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem, 12, 0, 1, 1)
        self.saveLocationOpener = QtWidgets.QPushButton(self)
        self.gridLayout_3.addWidget(self.saveLocationOpener, 12, 1, 1, 1)

        ##contraster$
        self.brightnessLabel = QtWidgets.QLabel(self)
        self.brightnessLabel.setObjectName("brightnessLabel")
        self.gridLayout_3.addWidget(self.brightnessLabel, 8, 0, 1, 1)
        self.brightnessBox = QtWidgets.QSpinBox(self)
        self.brightnessBox.setObjectName("brightnessBox")
        self.brightnessBox.setMinimum(0)
        self.brightnessBox.setSingleStep(1)
        self.brightnessBox.setMaximum(100)
        self.gridLayout_3.addWidget(self.brightnessBox, 8, 1, 1, 1)
        self.contrastLabel = QtWidgets.QLabel(self)
        self.contrastLabel.setObjectName("contrastLabel")
        self.gridLayout_3.addWidget(self.contrastLabel, 9, 0, 1, 1)
        self.contrastBox = QtWidgets.QSpinBox(self)
        self.contrastBox.setObjectName("contrastBox")
        self.contrastBox.setMinimum(-100)
        self.contrastBox.setSingleStep(1)
        self.contrastBox.setMaximum(100)
        self.gridLayout_3.addWidget(self.contrastBox, 9, 1, 1, 1)


        #self.gain = QtWidgets.QSpinBox(self.videoSettingsBox)
        #self.gain.setObjectName("gain")
        #self.gridLayout_3.addWidget(self.gain, 7, 1, 1, 1)

        self.retranslateUi()
        self.buttons = {"names": self.namesButton, "okay": self.okayButton, "default": self.defaultButton,
                        "iso": self.isoCombo, "compression": self.compressionSlider, "color": self.colorCombo,
                        "vflip": self.vflipCheck, "autogain": self.autogainCheck,  "save": self.saveLocationOpener, "reso": self.resolutionCombo}


        self.text = {"clip len": self.clipLength, "fps": self.frameSec, "gain": self.gain, "brightness": self.brightnessBox, "contrast": self.contrastBox,
                     "compressionLabel": self.compressionLabel,  "save path": self.saveLocationLineEdit, "shutter speed": self.shutterSpeedBox}

    def retranslateUi(self):
        """Sets the text for all the UI elements.

        Supposedly used as a hook for QT to translate things while running (and
        is currently called at the end of init). We don't have localization
        (yet?) so we just run it once.
        """
        self.setWindowTitle("Settings")
        self.namesButton.setText("Bundle Settings")
        self.okayButton.setText("OK")
        self.defaultButton.setText("Default")
        self.clipSettingsBox.setTitle("Clip Settings")
        self.clipLength.setValue(2)
        self.minuteLabel.setText("minutes")
        self.segLengthLabel.setText("Video segment length:")
        self.videoSettingsBox.setTitle("Video Settings")
        
        
        self.colorLabel.setText("Color")
        #self.colorCombo.setText("Color")

        self.isoLabel.setText("ISO:")
        self.frameSec.setValue(60)
        self.compressionLabel.setText("Compression: 1x")


        self.shutterSpeedLabel.setText("Shutter speed in microseconds: ")
        self.shutterSpeedBox.setValue(8333)

        self.resolutionCombo.setItemText(0, "640x480")
        self.resolutionCombo.setItemText(1, "1280x720")
        self.resolutionCombo.setItemText(2, "1920x1080")
        self.resolutionLabel.setText("Resolution:")

        ##contraster$
        self.brightnessLabel.setText("Brightness (0 - 100):")
        self.brightnessBox.setValue(50)
        self.contrastLabel.setText('Contrast [-100, 100]:')
        self.contrastBox.setValue(0)


        self.isoCombo.setItemText(0, "0")
        self.isoCombo.setItemText(1, "100")
        self.isoCombo.setItemText(2, "200")
        self.isoCombo.setItemText(3, "400")
        self.isoCombo.setItemText(4, "800")
        self.isoCombo.setItemText(5, "1600")
        self.vflipCheck.setText("V-Flip")
        self.frameSecLabel.setText("Frames per second:")
        self.autogainCheck.setText("Auto-Gain")
        #self.sdCheck.setText("SD Video")  # NC edit
        self.gainLabel.setText("Gain:")
        
        # ***********************NC edit *******************************
        self.saveLocationLabel.setText("Set save location:")
        self.saveLocationLineEdit.setPlaceholderText("default:")
        self.saveLocationOpener.setText("Select Save Location")



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec_())
