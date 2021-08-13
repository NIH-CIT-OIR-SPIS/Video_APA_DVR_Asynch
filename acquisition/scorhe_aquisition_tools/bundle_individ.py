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



from functools import partial
import logging
from threading import Thread
from typing import Callable, Dict, Union

from PyQt5.QtWidgets import QInputDialog, QListWidget

from scorhe_server import server
from scorhe_aquisition_tools import gplayer
from scorhe_aquisition_tools.scorhe_launcher_gui import CameraLablerWindow, BundlerWindow

logger = logging.getLogger(__name__)


class Bundler:
    """
    The bundle tool is an object that helps group client cameras into cages.
    This information is then stored in a temporary variable that is later saved into a file.
    It also launches a separate GUI window to interact with.
    """

    def __init__(self,
                 camMap: Dict[str, Dict[str, Union[str, Dict[str, str]]]],
                 controllerThread: server.CameraServerController,
                 camPorts: Dict[str, int],
                 updater,
                 camUpdate: Callable[[], None],
                 groupType: str,
                 ):
        self.camMap = camMap
        self.controllerThread = controllerThread  # type: server.CameraServerController
        self.clients = controllerThread.server.clients
        self.camPorts = camPorts
        self.updater = updater
        self.camUpdate = camUpdate
        self.SCORHE = groupType.lower() == "scorhe"  
        # Window that contains the bundle tool
        if self.SCORHE:
            self.window = BundlerWindow()
        else:
            self.window = CameraLablerWindow()
        self.window.show()
        self.buttons = self.window.buttons
        self.lists = self.window.lists
        if not self.SCORHE:
            self.selectors = self.window.selectors
        # Window that contains a small pop up to enter group name
        self.addCageWindow = None
        # Bool keeps track if the GUI is showing a camera
        self.previewing = False
        # Reference to current player
        self.player = None
        # Reference to selected group
        self.selectedCage = None
        # Variable to help add groups to group organizer/GUI combobox
        self.groupCount = 3
        # Temp variable to keep track of cages that still need to be recorded
        self.cagesToAdd = []
        self.cagesToRemove = []
        self.cam = None

    def setUpWindow(self) -> None:
        """
        Function sets up the entire bundle window by linking up buttons and starting the cameras previewing if not
        already.
        """
        self.buttons["okay"].clicked.connect(self.exitBundler)
        camIds = [i.cameraID for i in self.clients.getClients("Camera")]
        if self.SCORHE:
            unassignedCams = []
            for cam in camIds:
                if cam not in self.camMap["camera"]:
                    unassignedCams.append(cam)
            for t in ["main", "rear", "front"]:
                self.buttons["set " + t].clicked.connect(partial(self.setCamera, t))
            self.buttons["remove cameras"].clicked.connect(self.removeCameraFromCage)
            self.lists["unassigned cameras"].addItems(unassignedCams)
            self.lists["unassigned cameras"].itemPressed.connect(
                    partial(self.bundlePreview, self.lists["unassigned cameras"]))
            self.lists["cage cameras"].itemPressed.connect(
                    partial(self.bundlePreview, self.lists["cage cameras"]))
            self.lists["cages"].clear()
            self.lists["cages"].addItem("No Selection")
            self.lists["cages"].addItems(sorted(list(self.camMap["name"].keys())))
            self.lists["cages"].addItems(["Delete Cage...", "Add New Cage..."])
            self.lists["cages"].setCurrentIndex(0)
            self.lists["cages"].currentIndexChanged.connect(self.cageSelected)
        else:
            # Connect buttons
            for key, button in self.selectors.items():
                button.clicked.connect(self.selectorClicked(key))
            self.buttons["clearAll"].clicked.connect(self.clearAll)
            self.buttons["reset"].clicked.connect(self.reset)
            self.buttons["okay"].clicked.connect(self.exitBundler)
            camIds = [i.cameraID for i in self.clients.getClients("Camera")]
            camNames = []
            for camId in camIds:
                if camId in self.camMap["camera"] and self.camMap["camera"][camId] in self.selectors:
                    camNames.append(camId + " " + self.camMap["camera"][camId])
                    self.selectors[self.camMap["camera"][camId]].setEnabled(False)
                else:
                    camNames.append(camId)
            self.lists["cameras"].addItems(camNames)
            self.lists["cameras"].currentItemChanged.connect(self.bundlePreview)

    def cageSelected(self) -> None:
        """Sets up the interface with the cameras associated with the selected cage.

        This allows the user to add, remove, or edit cameras in the cage.
        """
        try:
            cage = self.lists["cages"].currentText()
            self.lists["cage cameras"].clear()
            if self.lists["unassigned cameras"].selectedItems():
                for loc in ["main", "front", "rear"]:
                    self.buttons["set " + loc].setEnabled(False)
            self.buttons["remove cameras"].setEnabled(False)
            if cage == "No Selection":
                pass
            elif cage == "Delete Cage...":
                delCage, success = QInputDialog.getItem(self.window, "Delete a Cage", "Pick a cage to delete:",
                                                        self.camMap["name"].keys(), current=0, editable=False)
                if not success:
                    self.lists["cages"].setCurrentIndex(0)
                    return
                for camId in self.camMap["name"][delCage].values():
                    self.lists["unassigned cameras"].addItem(camId)
                    del self.camMap["camera"][camId]
                del self.camMap["name"][delCage]
                self.lists["cages"].setCurrentIndex(0)
                # delete the cage from the list
            elif cage == "Add New Cage...":
                addCage = None
                success = True
                while success and (addCage is None or addCage in self.camMap["name"]):
                    addCage, success = QInputDialog.getText(self.window, "Add a Cage", "Set the new cage's name:")
                if not success:
                    self.lists["cages"].setCurrentIndex(0)
                    return
                self.camMap["name"][addCage] = {}
                self.lists["cages"].clear()
                self.lists["cages"].addItem("No Selection")
                self.lists["cages"].addItems(sorted(list(self.camMap["name"].keys())))
                self.lists["cages"].addItems(["Delete Cage...", "Add New Cage..."])
                self.lists["cages"].setCurrentIndex(0)
            elif cage in self.camMap["name"]:
                for location, camId in self.camMap["name"][cage].items():
                    self.lists["cage cameras"].addItem(camId + ' ' + location)
        except Exception as e:
            logger.error(e)

    def setCamera(self, location: str) -> None:
        """Associates a camera with a cage. """
        if not self.cam or \
                self.lists["cages"].currentText() in ["No Selection", "Delete Cage...", "Add New Cage..."]:
            return
        currentCage = self.lists["cages"].currentText()
        if self.lists["unassigned cameras"].currentItem() and \
           self.lists["unassigned cameras"].currentItem().text() == self.cam:
            self.lists["unassigned cameras"].takeItem(self.lists["unassigned cameras"].currentRow())
            self.lists["cage cameras"].addItem(self.cam + " " + location)
            if self.lists["unassigned cameras"].count() == 0:
                for loc in ["main", "front", "rear"]:
                    self.buttons["set " + loc].setEnabled(True)
        else:
            oldCam = self.lists["cage cameras"].currentItem().text()
            oldLocation = oldCam.split(" ")[1]
            del self.camMap["name"][currentCage][oldLocation]
            self.lists["cage cameras"].currentItem().setText(self.cam + " " + location)
        self.camMap["name"][currentCage][location] = self.cam
        self.camMap["camera"][self.cam] = currentCage + " " + location

    def removeCameraFromCage(self) -> None:
        """ Removes the association between a camera and its cage.  """
        if not self.cam or \
                self.lists["cages"].currentText() in ["No Selection", "Delete Cage...", "Add New Cage..."]:
            return
        currentCage = self.lists["cages"].currentText()
        camId, location = self.lists["cage cameras"].currentItem().text().split(" ", 1)
        self.lists["cage cameras"].takeItem(self.lists["cage cameras"].currentRow())
        if self.lists["cage cameras"].count() == 0:
            self.buttons["remove cameras"].setEnabled(False)
        try:
            del self.camMap["name"][currentCage][location]
        except KeyError:
            pass
        if camId in self.camMap["camera"]:
            del self.camMap["camera"][camId]
        self.lists["unassigned cameras"].addItem(self.cam)

    def clearAll(self) -> None:
        """ Clears all associations between cameras and names. """
        if not self.lists["cameras"].currentItem():
            return
        self.camMap["name"] = {}
        self.camMap["camera"] = {}
        for key, button in self.selectors.items():
            button.setEnabled(True)
        self.lists["cameras"].clear()
        self.lists["cameras"].addItems([i.cameraID for i in self.clients.getClients("Camera")])

    def reset(self) -> None:
        """ Removes the association for the selected camera."""
        item = self.lists["cameras"].currentItem()
        if not item:
            return
        camera = item.text()
        if " " in camera:
            name = camera.split(" ")[1]
            camera = camera.split(" ")[0]
            del self.camMap["name"][name]
            del self.camMap["camera"][camera]
            item.setText(camera)
            self.selectors[name].setEnabled(True)

    def selectorClicked(self, selector: str) -> Callable[[], None]:
        """Creates function that handles a given selector being updated. """
        def x() -> None:
            """Handles a selector being updated.

            Removes the previous association for the selected camera and
            creates a new one.
            """
            if not self.lists["cameras"].currentItem():
                return
            self.selectors[selector].setEnabled(False)
            camera = self.lists["cameras"].currentItem().text()
            if " " in camera:
                split = camera.split(" ")
                camera = split[0]
                other = split[1]
                # the selected camera is no longer associated with this "name"/location
                del self.camMap["name"][other]
                del self.camMap["camera"][camera]  # isn't really necessary, but id like to do it anyway
                self.selectors[split[1]].setEnabled(True)
            self.lists["cameras"].currentItem().setText(camera + " " + selector)
            self.camMap["name"][selector] = camera
            self.camMap["camera"][camera] = selector

        return x

    def bundlePreview(self, camList: QListWidget) -> None:
        """
        Function handles previewing for the bundle GUI
        """
        try:
            if self.SCORHE:
                if camList == self.lists["cage cameras"]:
                    for loc in ["main", "front", "rear"]:
                        self.buttons["set " + loc].setEnabled(True)
                    self.buttons["remove cameras"].setEnabled(True)
                elif camList == self.lists["unassigned cameras"]:
                    for loc in ["main", "front", "rear"]:
                        self.buttons["set " + loc].setEnabled(True)
                    self.buttons["remove cameras"].setEnabled(False)

            # If GUI is already previewing, end that preview
            if self.previewing:
                self.player.quit(self.window.frame)
                t1 = Thread(target=self.controllerThread.server.sendSelectStopPreviewingMessage, args=(self.cam,))
                t1.start()
                t1.join()
            # Get selected camera information
            try:
                self.cam = camList.currentItem().text()
            except AttributeError:
                self.cam = camList.text()
            if " " in self.cam:
                self.cam = self.cam.split(" ")[0]

            t1 = Thread(target=self.controllerThread.server.sendSelectStartPreviewingMessage, args=(self.cam,))
            t1.start()
            t1.join()
            # Update all the preview ports
            t2 = Thread(target=self.updater.updatePreviewPorts)
            t2.start()
            t2.join()
            port = self.camPorts[self.cam]
            # Create a player for the camera
            self.player = gplayer.GPlayer(port, self.window.frame.winId(), 480, 320)
            self.player.start()
            self.previewing = True
        except Exception as e:
            logger.exception(e)

    def exitBundler(self) -> None:   #  *********** NC: ERROR Traceback here ************************************************************************************************************************************************************************
        """
        Function handles exiting the bundle GUI/tool, mostly clears things
        """
        if self.previewing:
            self.player.quit(self.window.frame)
        self.window.close()
        self.window = None
        self.camUpdate()
        self.controllerThread.server.sendStopPreviewingMessages()  #  *********** NC: ERROR Traceback here, error being thrown in 'server.py' line 694 *******************************************************************************
        self.controllerThread.server.clientOptions.camMap = self.camMap
        self.controllerThread.server.sendSetView()

    def runBundle(self) -> None:
        """
        Main run function
        """
        # Tell all cameras to preview
        # t1 = Thread(target=self.controllerThread.server.sendStartPreviewingMessages)
        # t1.start()
        # t1.join()
        # # Update all the preview ports
        # t2 = Thread(target=self.updater.updatePreviewPorts)
        # t2.start()
        # t2.join()
        # Launch the window
        self.setUpWindow()
