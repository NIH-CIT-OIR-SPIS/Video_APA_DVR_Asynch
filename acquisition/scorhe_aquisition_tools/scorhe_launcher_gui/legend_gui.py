from PyQt5 import QtCore, QtWidgets

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtWidgets.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtWidgets.QApplication.translate(context, text, disambig)


class LegendGui(QtWidgets.QDialog):
    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.setObjectName(_fromUtf8("Dialog"))
        self.setModal(True)
        self.resize(400, 298)
        self.gridLayout_2 = QtWidgets.QGridLayout(self)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.scrollArea = QtWidgets.QScrollArea(self)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 380, 268))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.gridLayout_3 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.gridLayout_3.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout_2.addWidget(self.scrollArea, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.setSpacing(0)
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)
        for col in range(0, 8):
            text = QtWidgets.QLabel(self)
            text.setText(["A", "B", "C", "D", "E", "F", "G", "H"][col])
            text.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            text.setAlignment(QtCore.Qt.AlignCenter)
            if col == 0:
                text.setStyleSheet("border-style:solid;border-color:black;border-width:2px 1px 1px 2px;")
            elif col == 7:
                text.setStyleSheet("border-style:solid;border-color:black;border-width:2px 2px 1px 1px;")
            else:
                text.setStyleSheet("border-style:solid;border-color:black;border-width:2px 1px 1px 1px;")
            self.gridLayout.addWidget(text, 0, col + 1, 1, 1)
        for row in range(0, 12):
            text = QtWidgets.QLabel(self)
            text.setText(str(row + 1))
            text.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            text.setAlignment(QtCore.Qt.AlignCenter)
            if row == 0:
                text.setStyleSheet("border-style:solid;border-color:black;border-width:2px 1px 1px 2px;")
            elif row == 11:
                text.setStyleSheet("border-style:solid;border-color:black;border-width:1px 1px 2px 2px;")
            else:
                text.setStyleSheet("border-style:solid;border-color:black;border-width:1px 1px 1px 2px;")
            self.gridLayout.addWidget(text, row + 1, 0, 1, 1)
        self.widgets = [[QtWidgets.QWidget(self) for c in range(0, 8)] for r in range(0, 12)]
        for r in range(0, len(self.widgets)):
            for c in range(0, len(self.widgets[r])):
                self.widgets[r][c].setObjectName("widget_{}_{}".format(r, c))
                self.gridLayout.addWidget(self.widgets[r][c], r + 1, c + 1, 1, 1)
                if r == len(self.widgets) - 1 and c < len(self.widgets[r]) - 1:
                    self.widgets[r][c].setStyleSheet("#widget_" + str(r) + "_" + str(
                        c) + " {border-style:solid;border-color:black;border-width:1px 1px 2px 1px;}")
                elif r < len(self.widgets) - 1 and c == len(self.widgets[r]) - 1:
                    self.widgets[r][c].setStyleSheet("#widget_" + str(r) + "_" + str(
                        c) + " {border-style:solid;border-color:black;border-width:1px 2px 1px 1px;}")
                elif r == len(self.widgets) - 1 and c == len(self.widgets[r]) - 1:
                    self.widgets[r][c].setStyleSheet("#widget_" + str(r) + "_" + str(
                        c) + " {border-style:solid;border-color:black;border-width:1px 2px 2px 1px;}")
                else:
                    self.widgets[r][c].setStyleSheet("#widget_" + str(r) + "_" + str(c) + " {border:1px solid black;}")

        self.retranslateUi()
        # QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), self.accept)
        # QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), self.reject)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        self.setWindowTitle(_translate("Dialog", "Legend", None))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    ui = LegendGui()
    ui.show()
    sys.exit(app.exec_())
