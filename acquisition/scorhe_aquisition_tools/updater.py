import os
import platform
import shutil
import socket
import threading
import time
from typing import Callable, Dict, List

from PyQt5 import QtWidgets

from scorhe_server import server


class Updater:
    """This object is used to update all information of the GUI.

    It also cannot be a thread, because the QWidgets are not thread safe. It
    does however use a timer to repeatedly call its update function.
    """
    def __init__(self,
                 camUpdate: Callable[[List[str]], None],
                 text: Dict[str, QtWidgets.QLabel],
                 controllerThread: server.CameraServerController,
                 camPorts: Dict[str, int],
                 #timeLeft: Dict[str, QtWidgets.QLabel]
                 ):
        #self.timeLeft = None
        self.camUpdate = camUpdate  # type: Callable[[server.CameraClient], None]
        self.text = text  # type: Dict[str, QtWidgets.QLabel]
        self.controllerThread = controllerThread  # type: server.CameraServerController
        # Object to how reference to the timer that calls the update function
        self.updateThread = None  # type: threading.Timer
        # Camera client information
        self.camPorts = camPorts  # type: Dict[str, int]
        # Number of cameras connected 
        self.numCam = 0  # type: int
        # Variable that keeps track of the last previewing state
        self.numCages = 0  # type: int
        self.camEdit = False  # type: bool

    def dateAndTime(self) -> None:
        """
        Function updates the date and time on the main GUI
        """
        self.text['curr date'].setText(time.strftime('%m/%d/%Y'))
        self.text['curr time'].setText(time.strftime('%H:%M:%S'))

    def IPAddress(self) -> None:
        """
        Sets the IP address text tag.
        """
        ip = 'unknown'
        if platform.system() == 'Windows':
            ip = str([a[4][0] for a in socket.getaddrinfo('', 0) if a[0] == socket.AF_INET][0])
        self.text['ip'].setText(ip)

    def updateCameras(self) -> None:
        """
        Function adds new/unseen cameras to the client info database
        """
        clients = self.controllerThread.server.clients.getClients('Camera')
        numClients = len(clients)
        self.text['cam num'].setText(str(numClients))
        # If there are more or less clients then last reported		
        if self.numCam != numClients:
            self.numCam = numClients
            # clients = self.controllerThread.server.clients.getClients('Camera')
            self.camUpdate([c.cameraID for c in clients])
            for client in clients:
                if client.cameraID not in self.camPorts.keys():
                    self.camPorts[client.cameraID] = 0
            self.camEdit = True

    def updatePreviewPorts(self) -> None:
        """
        Function updates client info with the ports needed for previewing
        """
        clients = self.controllerThread.server.clients.getClients('Camera')
        # Update each cameras port
        for client in clients:
            self.camPorts[client.cameraID] = str(client.previewPort)

    def remainingFreeSpace(self) -> None:
        """
        Function updates remaining hard drive space
        """
        GB = 1024 * 1024 * 1024
        storage_path = self.controllerThread.server.options.baseDirectory or os.getcwd()
        storage_path = os.path.abspath(storage_path)
        drive = os.path.splitdrive(storage_path)[0]
        location = 'unknown mount pt./drive'
        if platform.system() == 'Linux':
            if drive:
                location = 'on mount root'
            else:
                location = 'on mount {}'.format(drive)
        elif platform.system() == 'Windows':
            location = '{} drive'.format(drive)
        usage = shutil.disk_usage(storage_path)
        freegb = usage.free / GB
        self.text['space'].setText('{:.1f} GB ({})'.
                                   format(freegb, location))
        try:
            self.text['space'].setToolTip('To show the space on another '
                                          'drive, set the recording '
                                          'directory by setting up an '
                                          'experiment.')
        except AttributeError:
            pass

    def update(self) -> None:
        """
        Master update function, runs every 1 second thanks to the updateThread timer
        """
        self.remainingFreeSpace()
        self.dateAndTime()
        self.IPAddress()
        self.updateCameras()
        # 1 second recursive timer
        #a = callable(self.update)
        #print("A ;;;;;;;;;; %s" % a)
        self.updateThread = threading.Timer(1, self.update)
        #print(self.updateThread)
        self.updateThread.start()

    def stop(self) -> None:
        """ Stop the update timer """
        self.updateThread.cancel()
