"""
Server main controller exists within this file. This file can be run bare-bones
command line or be started automatically through the server launcher. 
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
from collections import defaultdict
import ipaddress
import logging
import os
import platform
import queue
import re
import socket
import socketserver
import struct
import sys
import threading
import time
import copy
from typing import DefaultDict, Tuple, Callable, Optional, Any, Iterable, \
    Dict, List, Union

from scorhe_server import gpac, protocol, server_protocols
import utils

if platform.system() == 'Linux':
    import fcntl
#__name__ = "log_server.log"
logger = logging.getLogger(__name__)

logging.basicConfig(filename="log_server.log", level=logging.INFO)
NAME = 'SCORHE_server'
VERSION = '1.0.1'
CLIENT_VERSION = None
CLIENT_FOLDER = './client'

COUNTY = 0
def printHelp() -> None:
    """
    A function that prints the different parameters this file takes when run
    directly from the commandline.

    TODO: Either remove or replace with actual commandline parser.

    :return: Nothing
    """
    print('SCORHE server')
    print('Use the following arguments:')
    print('\t-d [directory]            (set the directory to record videos into)')
    print('\t-f [h264|mp4]             (set the file format to stream)')
    print('\t--push [true|false|t|f]   (push current client version to all connected cameras)')
    print('\thelp                      (display this help)')


class ClientOptions:
    """Object to store settings so IDE is more helpful when using settings.
    Also allows for listeners for settings if necessary.

    These are settings that will be sent to the clients.
    """
    __slots__ = ('_camMap', '_rotation', '_zoomLocation', '_fps', '_iso',
                 '_colorMode', '_compression', '_autogain', '_vflip', '_gain',
                 '_brightness', '_sendToSelect', '_sendToAll', '_zoomDimension',
                 '_camSelects', '_camSelectsIsActive', '_fpsCamMap', '_shutterspeed', '_contrast',
                 )

    def __init__(self,
                 sendToSelect: Callable[[str, str, str], Any],
                 sendToAll: Callable[[str, str], Any],
                 camMap: Optional[Dict[str, str]]=None,
                 rotation: Optional[DefaultDict[str, int]]=None,
                 zoomLocation: Optional[DefaultDict[str, Tuple[int, int]]]=None,
                 #fps: int=30,
                 fps: int=30,
                 iso: int=0,
                 colorMode: bool=False,
                 compression: float=1,
                 autogain: bool=True,
                 vflip: Optional[DefaultDict[str, bool]]=None,
                 gain: float=0,
                 brightness: int=50,
                 #zoomDimension: Tuple[int, int]=(1920, 1080),  #NC : changed from (1296, 972) to (1920, 1080) as RPi 3 support HD.
                 zoomDimension: Tuple[int, int]=(1280, 720),
                 shutterspeed: int=8333,
                 ##contraster$
                 contrast: int=0,
                 ):
        """Sets the settings for all cameras that are connected.

        Keep in mind that this doesnt actually send the settings to all cameras.
        To send the settings, use ``forcePush``.

        :param sendToSelect: The function used to send the values set here to
            select cameras.
        :param sendToAll: the function used to send the values set here to all
            cameras.
        :param camMap: A mapping between camera ids and their names.
        :param rotation: A mapping between camera ids and their rotation.
        :param zoomLocation: A mapping between camera ids and their zoom window.
        :param fps: The fps for all connected cameras
        :param iso: The ISO (sensitivity to light) for all connected cameras.
        :param colorMode: Whether all connected cameras should record in color
            or not.
        :param compression: The factor by which to compress the sides of the
            image for all cameras.
        :param autogain: Whether to enable autogain for all cameras.
        :param vflip: A mapping between camera id and whether they should be
            flipped vertically.
        :param gain: The gain for all cameras.
        :param brightness: The brightness for all cameras.
        :param zoomDimension: The size of the zoom window.
        """
        
        self._sendToSelect = sendToSelect
        self._sendToAll = sendToAll
        self._camMap = {} if camMap is None else camMap
        self._rotation = defaultdict(lambda: 0) if rotation is None else rotation  # type: DefaultDict[str, int]
        self._zoomLocation = defaultdict(lambda: (0, 0)) if \
            zoomLocation is None else zoomLocation  # type: DefaultDict[str, Tuple[int, int]]
        self._vflip = defaultdict(lambda: False) if vflip is None else vflip  # type: DefaultDict[str, bool]
        self._fps = fps
        self._iso = iso
        self._colorMode = colorMode
        self._compression = compression
        self._autogain = autogain
        self._gain = gain
        self._brightness = brightness
        self._zoomDimension = zoomDimension
        ##contraster$
        self._contrast = contrast
        self._camSelects = []
        self._camSelectsIsActive = {'isActive': False}
        self._fpsCamMap = {}
        self._shutterspeed = shutterspeed
    #def forcePushCage(self, cage: Dict[str, str]) -> None:

    def forcePush(self, cams: Optional[Iterable[str]]=None) -> None:
        """Pushes the current settings to all connected cameras.

        Keep in mind that, in general, setting any item explicitly updates the
        cameras. Use this only when you have to send everything.

        :param cams: What cameras to send the message to, or ``None`` to send
            to all the cameras
        :return: Nothing
        """
        if cams is None:
            self._sendToAll('Camera', 'set camMap')
            self._sendToAll('Camera', 'set rotation')
            self._sendToAll('Camera', 'set zoom points')
            self._sendToAll('Camera', 'set vflip')
            self._sendToAll('Camera', 'set FPS')
            self._sendToAll('Camera', 'set ISO')
            self._sendToAll('Camera', 'set color mode')
            self._sendToAll('Camera', 'set compression')
            self._sendToAll('Camera', 'set autogain')
            self._sendToAll('Camera', 'gain')
            self._sendToAll('Camera', 'set brightness')
            self._sendToAll('Camera', 'set shutter speed')
            ##contraster$
            self._sendToAll('Camera', 'set contrast')
        else:
            for cam in cams:
                self._sendToSelect('Camera', 'set camMap', cam)
                self._sendToSelect('Camera', 'set rotation', cam)
                self._sendToSelect('Camera', 'set zoom points', cam)
                self._sendToSelect('Camera', 'set vflip', cam)
                self._sendToSelect('Camera', 'set FPS', cam)
                self._sendToSelect('Camera', 'set ISO', cam)
                self._sendToSelect('Camera', 'set color mode', cam)
                self._sendToSelect('Camera', 'set compression', cam)
                self._sendToSelect('Camera', 'set autogain', cam)
                self._sendToSelect('Camera', 'gain', cam)
                self._sendToSelect('Camera', 'set brightness', cam)
                self._sendToSelect('Camera', 'set shutter speed', cam)
                ##contraster$
                self._sendToSelect('Camera', 'set contrast', cam)


    def _updateDefaultdict(self,
                           key: str,
                           old: DefaultDict[str, Any],
                           new: DefaultDict[str, Any],
                           ) -> None:
        """Sends updates to all cameras that changed value between old and new.

        The setting that changed and is being set is defined by ``key``.

        :param key: What setting changed.
        :param old: The old defaultdict setting values for the cameras.
        :param new: The new defaultdict setting values for the cameras.
        :return: Nothing
        """
        keys = set(new.keys()) | set(old.keys())
        for k in keys:
            if old[k] != new[k]:
                if self._camSelects and self._camSelectsIsActive['isActive']:
                    for i in self._camSelects:
                        if i == k:
                            self._sendToSelect('Camera', 'set ' + key, k)
                else:
                    self._sendToSelect('Camera', 'set ' + key, k)

    # region Properties of the client settings
    @property
    def camMap(self) -> Dict[str, str]:
        """A dictionary mapping the IDs of clients to their names.

        A missing camera ID means that its name had not been set, and therefore
        the name that should be shown is the camera ID itself.

        Setting this value (but no updating individual mappings) will send a
        message to all cameras whose name been added, changed or removed to
        update their own name.

        :return: A dictionary mapping camera IDs to their names.
        """
        return self._camMap

    @camMap.setter
    def camMap(self, value: Dict[str, Dict[str, str]]) -> None:
        old = self._camMap
        self._camMap = value['camera']
        camKeys = set(value.keys()) | set(old.keys())
        for cam in camKeys:
            if cam not in old or cam not in value or old[cam] != value[cam]:
                if self._camSelects and self._camSelectsIsActive['isActive']:
                    for i in self._camSelects:
                        if i == cam:
                            self._sendToSelect('Camera', 'set camMap', cam)
                else:
                    self._sendToSelect('Camera', 'set camMap', cam)

    @property
    def rotation(self) -> Dict[str, int]:
        """A defaultdict mapping the IDs of the clients to their rotation.

        A missing camera ID mean that its rotation is the default value of the
        defaultdict (``0`` by default).

        Setting this value (but not updating individual mappings) will send a
        message to all cameras whose rotation has been added, changed or
        removed to update their own rotation.

        To set the value, pass a regular dict with the default value set under
        the key ``default`` and the actual mapping under ``camera``.

        Rotations are all multiples of 90. Values under 0 and above 360 are
        allowed.

        :return: A defaultdict mapping camera IDs to their names, and
            specifying the default rotation.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value: Dict[str, Union[int, Dict[str, int]]]) -> None:
        old = self._rotation  # type: DefaultDict[str, int]
        t = defaultdict(lambda: value['default'])  # type: DefaultDict[str, int]
        t.update(value['camera'])
        self._rotation = t
        self._updateDefaultdict('rotation', old, t)

    @property
    def zoomLocation(self) -> Dict[str, Tuple[int, int]]:
        """A defaultdict mapping the IDs of clients to the location of their zoom window.

        A missing camera ID means that its zoom window is the default value of
        the defaultdict (``(0, 0)`` by default).

        Setting this value (but not updating individual mappings) will send a
        message to all cameras whose zoom window has been added, changed, or
        removed to update their own zoom window.

        To set the value, pass a regular dict with the default value set under
        the key ``default`` and the actual mapping under ``camera``.

        A zoom window/zoom points is a 2-tuple of int which represents the x
        and y coordinates of the top-left corner of the window.

        :return: A defaultdict mapping the IDs of clients to their zoom window,
            and specifying the default zoom window.
        """
        return self._zoomLocation

    @zoomLocation.setter
    def zoomLocation(self, value: Dict[str, Union[Tuple[int, int], Dict[str, Tuple[int, int]]]]) -> None:
        old = self._zoomLocation  # type: DefaultDict[str, Tuple[int, int]]
        t = defaultdict(lambda: value['default'])  # type: DefaultDict[str, Tuple[int, int]]
        t.update(value['camera'])
        self._zoomLocation = t
        self._updateDefaultdict('zoom points', old, t)

    @property
    def vflip(self) -> Dict[str, bool]:
        """A default dict mapping the IDs of clients to their vflip value.

        A missing camera ID means that its zoom window the default value of
        the defaultdict (``False`` by default).

        Setting this value (but not updating individual mappings) will send a
        message to all cameras whose vflip value has been added, changed or
        removed to update their own vflip value.

        To set the value, pass a regular dict with the default value set under
        the key ``default`` and the actual mapping under ``camera``.

        Vflip refers to whether the camera's view should be flipped vertically
        or not. A value of ``True`` means it should be flipped, and ``False``
        means it should not.

        :return: A defaultdict mapping the IDs of clients to their vflip value,
            and specifying the default vflip value.
        """
        return self._vflip

    @vflip.setter
    def vflip(self, value: Dict[str, Union[bool, Dict[str, bool]]]) -> None:
        old = self._vflip  # type: DefaultDict[str, bool]
        t = defaultdict(lambda: value['default'])   # type: DefaultDict[str, bool]
        t.update(value['camera'])    
        self._vflip = t
        self._updateDefaultdict('vflip', old, t)

    @property
    def fps(self) -> int:
        """The fps for all cameras connected to this server.

        When this value is set directly, a message is sent to all cameras to
        set their fps, which should take effect in the next call to record or
        preview.

        :return: The fps for all cameras connected to this server.
        """
        return self._fps

    @fps.setter
    def fps(self, value: int) -> None:
        self._fps = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set FPS', cam)
        else:   
            self._sendToAll('Camera', 'set FPS')


    
    @property
    def iso(self) -> int:
        """The ISO for all cameras connected to this server.

        Setting this value send a message to all cameras to set their ISO. As
        per the picamera documentation, this value represents how sensitive the
        camera is to light, where a higher value is more sensitive. 0 is auto.

        :return: The ISO for all cameras connected to this server
        """
        return self._iso

    @iso.setter
    def iso(self, value: int) -> None:
        self._iso = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set ISO', cam)
        else:        
            self._sendToAll('Camera', 'set ISO')

    @property
    def colorMode(self) -> bool:
        """Whether the cameras are recording in color or grayscale.

        This property specifies whether to record in color (``True``) or in
        grayscale (``False``).

        Setting this value sends a message to all the connected cameras to set
        their values.

        :return: Whether the cameras are recording in color or grayscale.
        """
        return self._colorMode

    @colorMode.setter
    def colorMode(self, value: bool) -> None:
        self._colorMode = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set color mode', cam)
        else:        
            self._sendToAll('Camera', 'set color mode')

    @property
    def compression(self) -> float:
        """Sets the factor with which to reduce the sides of the image.

        Setting this value sends a message to all cameras to set their
        compression.

        Note that since this modifies how the `sides` of the image are
        compressed, the entire frame is compressed by a factor of
        ``compression`` squared.

        :return: The factor with which to reduce the sides of the image.
        """
        return self._compression

    @compression.setter
    def compression(self, value: float) -> None:
        self._compression = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set compression', cam)
        else:
            self._sendToAll('Camera', 'set compression')

    @property
    def autogain(self) -> bool:
        """Enables or disables the autogain of the cameras.

        If this property is ``False`` autogain is disabled. If this property is
        ``True``, autogain is enabled.

        Setting this value sends a message to all connected cameras to set
        their autogain.

        :return: Whether autogain is enabled for the cameras.
        """
        return self._autogain

    @autogain.setter
    def autogain(self, value: bool) -> None:
        self._autogain = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set autogain', cam)
        else:
            self._sendToAll('Camera', 'set autogain')

    @property
    def gain(self) -> float:
        """Sets the gain for all the cameras connected to this server.

        Setting this value sends a message to all connected cameras to set
        their gain.

        :return: The gain of all cameras connected to this server.
        """
        return self._gain

    @gain.setter
    def gain(self, value: float) -> None:
        self._gain = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set gain', cam)
        else:
            self._sendToAll('Camera', 'set gain')

    @property
    def brightness(self) -> int:
        """Sets the brightness of the cameras connected to the server.

        Setting this value sends a message to all connected cameras to set
        their brightness.

        :return: The brightness of the cameras connected to the server.
        """
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._brightness = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set brightness', cam)
        else:
            self._sendToAll('Camera', 'set brightness')

    ##contraster$
    @property
    def contrast(self) -> int:
        return self._contrast
    ##contraster$
    @contrast.setter
    def contrast(self, value: int) -> None:
        self._contrast = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set contrast', cam)
        else:
            self._sendToAll('Camera', 'set contrast')

    @property
    def zoomDimension(self) -> Tuple[int, int]:
        """Sets the dimension of the camera view for all clients.

        Setting this value sends a message to all connected cameras to set
        their zoom dimension.

        The last 2-tuple of ints represents the zoom window's width and height
        in pixels. The pis get stuck when set to a viewport with an extreme
        aspect ratio, so the protocol rejects viewport with an aspect ratio
        that is not within 0.5 and 2.

        :return: The dimension of the zoom window of the clients.
        """
        return self._zoomDimension

    @zoomDimension.setter
    def zoomDimension(self, value: Tuple[int, int]) -> None:
        self._zoomDimension = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set zoom points', cam)
        else:
            self._sendToAll('Camera', 'set zoom points')

    @property
    def shutterspeed(self) -> int:
        """ Sets the shutter speed of camera """

        return self._shutterspeed

    @shutterspeed.setter
    def shutterspeed(self, value: int) -> None:
        self._shutterspeed = value
        if self._camSelects and self._camSelectsIsActive['isActive']:
            for cam in self._camSelects:
                self._sendToSelect('Camera', 'set shutter speed', cam)
        else:
            self._sendToAll('Camera', 'set shutter speed')
    # endregion 1




class ServerOptions:
    """Object to store settings so IDE is more helpful when using settings.
    Also allows for listeners for settings if necessary.

    These are settings that will not be sent to the clients.
    """
    __slots__ = ('segmentSize', 'captureWidth', 'captureHeight',
                 'baseDirectory', 'format', 'clientFolder', 'clientVersion',
                 'pushUpdates', 'activeCams',
                 )

    def __init__(self,
                 segmentSize: int=2,
                 #captureWidth: int=640,
                 #captureHeight: int=480,
                 captureWidth: int=1280,
                 captureHeight: int=720,                 
                 baseDirectory: str='',
                 videoFormat: str='h264',
                 clientFolder: str='./client',
                 clientVersion: str='0.0.0',
                 pushUpdates: bool=True,
                 activeCams: Optional[Iterable[str]]=None
                 ):
        """

        :param segmentSize: The number of minutes in each segment, as an int.
        :param captureWidth: The width of the video capture. Used for
            conversion of the videos.
        :param captureHeight: The height of the video capture. Used for
            conversion of the videos.
        :param baseDirectory: The location to store the experiments in.
        :param videoFormat: The format of the videos. Currently ignored and
            h264 remains the default for the cameras.
        :param clientFolder: The folder where the current code for the clients
            are at.
        :param clientVersion: The version the current clients are on.
        :param pushUpdates: Whether to push updates to the clients.
        :param activeCams: A list of camera IDs that are to be counted as
            active, that is to tell when to start and stop recording.
        """
        self.segmentSize = segmentSize
        self.captureWidth = captureWidth  # type: int
        self.captureHeight = captureHeight  # type: int
        self.baseDirectory = baseDirectory  # type: str
        self.format = videoFormat  # type: str
        self.clientFolder = clientFolder  # type: str
        self.clientVersion = clientVersion  # type: str
        self.pushUpdates = pushUpdates  # type: int
        self.activeCams = [] if activeCams is None else activeCams
        """:type activeCams: Iterable[str]"""
        


def parseArgv(argv: List[str]) -> ServerOptions:
    """
    Initializes the options and parses the command line options. If there is an
    error in the command line options, the help-text is printed, and after user
    input, the program is exited.

    TODO: Switch to using this to parse the settings json rather than in acquisition

    :param argv: A list of the commandline options passed to this program.
    :return: An object representing the the options for the server.
    """
    options = ServerOptions()
    try:
        while argv:
            arg = argv.pop(0)
            if arg == '-d':
                #if not argv.pop(0):
                #    options.baseDirectory = os.path.join(utils.APPDATA_DIR, "experiments", "Untitled", "")
                #    if not os.path.exists(options.baseDirectory):
                #        os.makedirs(options.baseDirectory)
                #else:
                    options.baseDirectory = argv.pop(0)
            elif arg == '-f':
                options.format = argv.pop(0)
            elif arg == '--push':
                arg = argv.pop(0)
                if arg == 'true' or arg == 't':
                    options.pushUpdates = True
                elif arg == 'false' or arg == 'f':
                    options.pushUpdates = False
                else:
                    raise Exception()
        if options.clientFolder and os.path.isdir(options.clientFolder):
            files = os.listdir(os.path.join(options.clientFolder, 'source'))
            files = set([os.path.basename(p) for p in files])
            expected = {'protocol.py', 'client.py',
                        'screen.py', '__main__.py'}
            if not expected.issubset(files):
                options.pushUpdates = False
                return options
            with open(os.path.join(options.clientFolder, 'source', 'client.py'), 'r') as f:
                eqs = ['=', ' =', '= ', ' = ']
                regexps = [re.compile('(?<=VERSION{}[\'"])[a-zA-Z0-9_.]+(?=[\'"]\\s*)'.format(eq)) for eq in eqs]
                # noinspection PyTypeChecker
                for line in f:
                    for regex in regexps:
                        options.clientVersion = regex.search(line)
                        if options.clientVersion is not None:
                            options.clientVersion = options.clientVersion.group()
                            break
                    if options.clientVersion is not None:
                        break
        else:
            options.pushUpdates = False
    except (Exception, IndexError, IOError) as e:
        logger.exception(e)
        printHelp()
        input()
        exit(1)
    return options


class RecordingOrStreamException(Exception):
    """Exception used for identifying a problem in streaming video."""
    pass


class ServerThread(threading.Thread):
    """Runs the actual server object.

    This is kept on a separate thread to protect against errors.
    """

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.server = server

    def run(self) -> None:
        """
        Serve until an explicit shutdown is called by the controller.

        :return: Nothing
        """
        logger.info('Starting server...')
        self.server.serve_forever()
        logger.info('Server shut down')
################################################################################################################################################################################################################################################################
class CameraServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """A TCP server that keeps track of SCORHE clients and applications.

    A number of event callbacks are provided to invoke common operations,
    like telling cameras to record or notify the applications that a file is
    finished downloading.
    """
    HOLDY = 0
    def __init__(self, port, controller, serverOptions):
        #print("Port line 674: {}".format(port))
        # Start TCP server on predetermined port
        socketserver.TCPServer.__init__(self, ('', port),
                                        ClientRequestHandler)
        logger.debug('Port: {}'.format(port))
        self.daemon_threads = True
        # Reference to clients
        self.clients = ClientConnections()
        logger.info('Port: {}'.format(port))
        logger.info("clients line 683: {}".format(self.clients.clients))
        #print(self.clients)
        # Reference to server controller
        self.controller = controller
        # Reference to command line options (if needed)
        self.options = serverOptions  # type: ServerOptions
        self.clientOptions = ClientOptions(self.sendToSelect, self.sendToAll)  # type: ClientOptions
        self.expName = None
        self.startTime = None
        self.endTime = None
        self.camNum = None
        # General recording info
        self.recording = False
        self.previewing = False
        self.cameraSettingsSet = False
        self.clientVersion = CLIENT_VERSION
        self.clientFolder = CLIENT_FOLDER
        
        # Asynchronous recording info
        self.cageSelect = ""
        self.cageMapper = {}
        self.settingsCagesStore = {}
        self.asynchSettings = False
        self.cageSettingsOn = False
        self.cageSettingsSet = False
        
        self.cageMappy = {}
        self.mappy = {}

   


    def sendToAll(self, clientType: str, messageID: str, *args) -> None:
        """Sends a message to all clients of the given type.

        :param clientType: The type of the client to send to (Unregistered or
            Camera)
        :param messageID: The id of the message (i.e. the key that is the index
            for the handler that should be called).
        :return: Nothing
        """
        self.clients.sendToAll(self, clientType, messageID, *args)

    def sendToSelect(self, clientType: str, messageID: str, cameraID: str, *args) -> None:
        """Sends a message to a select client of the given type and ID.

        :param clientType: The type of the client to send to (Unregistered or
            Camera)
        :param messageID: The id of the message (i.e. the key that is the index
            for the handler that should be called).
        :param cameraID: The id of the camera to send the message to.
        :return: Nothing
        """
        self.clients.sendToSelect(self, clientType, messageID, cameraID, *args)

    def sendToSelects(self, clientType: str, messageID: str, cameraIDs: Iterable[str], *args) -> None:
        """Sends a message to select clients of a given type and of each of the
        IDs.

        :param clientType: The type of the client to send to (Unregistered or
            Camera)
        :param messageID: The id of the message (i.e. the key that is the index
            for the handler that should be called).
        :param cameraIDs: A list of ids for the cameras to send the message to.
        :return: Nothing
        """
        self.clients.sendToSelects(self, clientType, messageID, cameraIDs, *args)

    def sendExpInfoMessages(self) -> None:
        """Sends a message to all cameras with the experiment information."""
        logger.info('Send Exp Info')
        self.sendToAll('Camera', 'send exp')

    def sendStartRecordingMessages(self) -> None:
        """Tells cameras to start recording."""
        if not self.cameraSettingsSet:
            if not self.cageSettingsSet:
                self.sendSetSettingsMessages()
                self.cameraSettingsSet = True
                self.cageSettingsSet = False
        if not self.cageSettingsSet:
            if not self.cameraSettingsSet:
                other = 0
                for other in self.settingsCagesStore:
                    self.sendSetCagesMessages(other, cageMappy, mappy)
                self.cageSettingsSet = True
                self.cameraSettingsSet = False
        if self.recording:
            raise RecordingOrStreamException(
                    'Cannot start recording when already recording')
        self.recording = True
        camListStart = self.updateCageMap()
        logger.info('Start recording')

        #try:
        #    self.sendStopPreviewingMessages()
        #except Exception as e:
        #    print(e)

        for cam in camListStart:
            self.sendToSelect('Camera', 'start recording', cam, time.strftime('%Y-%m-%d %Hh%Mm%Ss'))

    def sendSplitRecordingMessages(self) -> None:
        """Tells cameras to continue to record, but into a new file."""
        if not self.recording:
            raise RecordingOrStreamException(
                    'Cannot split recording when not recording')
        camListSplit = self.updateCageMap()
        logger.info('Split recording')
        for cam in camListSplit:
            self.sendToSelect('Camera', 'start recording', cam, time.strftime('%Y-%m-%d %Hh%Mm%Ss'))

    def sendStopRecordingMessages(self) -> None:
        """Tells cameras to stop recording."""
        if not self.recording:
            raise RecordingOrStreamException(
                    'Cannot stop recording when not recording')
        self.recording = False
        camListStop = self.updateCageMap()
        #self.setCamsRecording # NC edit
        logger.info('Stop recording')


        for cam in camListStop:
            self.sendToSelect('Camera', 'stop recording', cam)
        #try:
        #    self.sendStartPreviewingMessages()
        #except Exception as e:
        #    print(e)
        #self.sendToAll('Camera', 'stop recording')
    # def forceStop(self) -> None:
        # self.recording = False
        # camListStop = self.updateCageMap()
        # #self.setCamsRecording # NC edit
        # logger.info('Stop recording')       
        # for cam in camListStop:
            # self.sendToSelect('Camera', 'stop recording', cam)


    def sendStopRecordingAllMessages(self) -> None:
        for cage in self.cageMapper:
            self.cageMapper[cage]['isRecording'] = False

        self.recording = False
        self.sendToAll('Camera', 'stop recording')
        try:
            self.sendStartPreviewingMessages()
        except Exception as e:
            print(e)
        logger.info('Stop recording ALL')

    def updateCageMap(self) -> list():
        i = 0
        makerList = []
        for i in self.cageMapper:
            if bool(self.cageMapper[i]['wellSelect']) and self.cageMapper[i]['wellSelect'] != 'notInSelect':
                self.cageMapper[i]['isRecording'] = self.recording
                if 'main' in self.cageMapper[i]:
                    makerList.append(self.cageMapper[i]['main'])
                if 'front' in self.cageMapper[i]:
                    makerList.append(self.cageMapper[i]['front'])
                if 'rear' in self.cageMapper[i]:
                    makerList.append(self.cageMapper[i]['rear'])     
                    
        return makerList


    def sendStartRecordingMessagesCage(self) -> None:
        """ Tells a specified cage to start recording. """
       
        cage = self.cageSelect
        if not cage:
           raise RecordingOrStreamException('Cage does not exist, in sendStartRecordingMessagesCage.')

        if not self.cameraSettingsSet:
            if not self.cageSettingsSet:
                self.sendSetSettingsMessages()
                self.cameraSettingsSet = True
                self.cageSettingsSet = False
        if not self.cageSettingsSet:
            if not self.cameraSettingsSet:
                other = 0
                for other in self.settingsCagesStore:
                    self.sendSetCagesMessages(other, cageMappy, mappy)
                self.cageSettingsSet = True
                self.cameraSettingsSet = False

        if self.cageMapper[cage]['isRecording']:
            raise RecordingOrStreamException(
                'Cannot start recording cage when already recording for camera cage {}'.format(cage))
        self.cageMapper[cage]['isRecording'] = True
        logger.info('Started recording for cage: {}'.format(cage))
        listCamsRec = []
        i = 0
        if 'main' in self.cageMapper[cage]:
            listCamsRec.append(self.cageMapper[cage]['main'])
        if 'front' in self.cageMapper[cage]:
            listCamsRec.append(self.cageMapper[cage]['front'])
        if 'rear' in self.cageMapper[cage]:
            listCamsRec.append(self.cageMapper[cage]['rear'])
        if len(set(listCamsRec)) != len(listCamsRec): # Checking for unique elements 
           raise RecordingOrStreamException(
               "The listCamsRec is not made unique cameras, Error in server.py sendStartRecordingMessagesCage")
        #try:
        #    self.sendStopPreviewingMessages()
        #except Exception as e:
        #    print(e)


        for cam in listCamsRec:
            self.sendToSelect('Camera', 'start recording', cam, time.strftime('%Y-%m-%d %Hh%Mm%Ss'))
           
    def sendSplitRecordingMessagesCage(self, cage: str) -> None:
        """ Tells a specifed cage to continue recording, but into a new file."""
        #cage = self.cageSelect
        print("sendSplitRecordingMessagesCages called for cage: {}".format(cage))
        if not cage:
            raise RecordingOrStreamException(
                'This should not happen Error in server.py sendSplitRecordingMessagesCage')
        if not self.cageMapper[cage]['isRecording']: #and self.camsRecording[wellSelect] == False):
               raise RecordingOrStreamException(
                    'Cannot split recording for individual cage when not recording individual cage {}'.format(cage))
        listCamstoSplit = []
        logger.info('Split recording for cage: {}'.format(cage))
        i = 0
        if 'main' in self.cageMapper[cage]:
            listCamstoSplit.append(self.cageMapper[cage]['main'])
        if 'front' in self.cageMapper[cage]:
            listCamstoSplit.append(self.cageMapper[cage]['front'])
        if 'rear' in self.cageMapper[cage]:
            listCamstoSplit.append(self.cageMapper[cage]['rear'])
        if len(set(listCamstoSplit)) != len(listCamstoSplit): # Checking for unique elements 
           raise RecordingOrStreamException(
               'The listCamstoSplit is not made unique cameras, Error in server.py sendSplitRecordingMessagesCage')
        for cam in listCamstoSplit:
            self.sendToSelect('Camera', 'start recording', cam, time.strftime('%Y-%m-%d %Hh%Mm%Ss'))


    def sendStopRecordingMessagesCage(self) -> None:
        """ Tells specified cage to stop recording. """

        cage = self.cageSelect
        if not cage:
            raise RecordingOrStreamException('This should not happen Error in server.py sendStopRecordingMessagesCage')
        if not self.cageMapper[cage]['isRecording']:
            #print("CageMapper2: %s" % self.cageMapper)
            try:
                raise RecordingOrStreamException(
                        'Cannot stop recording for individual cage when not recording individual cage {}'.format(cage))
            except RecordingOrStreamException as err:
                logger.info('Will try stop recording for cage: {} just in case. Error: {}'.format(cage, err))
        self.cageMapper[cage]['isRecording'] = False
        logger.info('Stopped recording for cage: {}'.format(cage))
        listCamsToStop = []
        i = 0

        try:
            if 'main' in self.cageMapper[cage]:
                listCamsToStop.append(self.cageMapper[cage]['main'])
            if 'front' in self.cageMapper[cage]:
                listCamsToStop.append(self.cageMapper[cage]['front'])
            if 'rear' in self.cageMapper[cage]:
                listCamsToStop.append(self.cageMapper[cage]['rear'])
            if len(set(listCamsToStop)) != len(listCamsToStop): # Checking for unique elements 
                raise RecordingOrStreamException(
                    "The listCamsToStop is not made unique cameras, Error in server.py sendStopRecordingMessagesCage")
            for cam in listCamsToStop:
                self.sendToSelect('Camera', 'stop recording', cam)
        except Exception as err:
            logger.info("Tried to stop recording for cage: {} but failed. Error: {}".format(cage, err))
        #try:
        #    self.sendStartPreviewingMessages()
        #except Exception as e:
        #    print(e)

    def sendRebootMessageCage(self) -> None:
        """ Tells an individual well of cameras to reboot. """
        if bool(self.cageMapper):
            cage = self.cageSelect
            listCamsToReboot = []
            if 'main' in self.cageMapper[cage]:
                listCamsToReboot.append(self.cageMapper[cage]['main'])
            if 'front' in self.cageMapper[cage]:
                listCamsToReboot.append(self.cageMapper[cage]['front'])
            if 'rear' in self.cageMapper[cage]:
                listCamsToReboot.append(self.cageMapper[cage]['rear'])
            if bool(listCamsToReboot):
                for cam in listCamsToReboot:
                    self.sendToSelect('Camera', 'reboot', cam)


    def sendRestartMessageCage(self) -> None:
        """ Tells an individual well of cameras to restart. """
        if bool(self.cageMapper):
            cage = self.cageSelect
            listCamsToRestart = []
            if 'main' in self.cageMapper[cage]:
                listCamsToRestart.append(self.cageMapper[cage]['main'])
            if 'front' in self.cageMapper[cage]:
                listCamsToRestart.append(self.cageMapper[cage]['front'])
            if 'rear' in self.cageMapper[cage]:
                listCamsToRestart.append(self.cageMapper[cage]['rear'])
            if bool(listCamsToRestart):
                for cam in listCamsToRestart:
                    self.sendToSelect('Camera', 'restart', cam)  

    def sendSetCagesMessages(self, cage: str, cageMap: Dict[str, Union[str, Dict, bool]], settingsCages: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]]) -> None:
        listCamsSet = []
        camLinked = False

        if 'main' in cageMap[cage]:
            camLinked = True
            listCamsSet.append(cageMap[cage]['main'])
        if 'front' in cageMap[cage]:
            camLinked = True
            listCamsSet.append(cageMap[cage]['front'])
        if 'rear' in cageMap[cage]:
            camLinked = True
            listCamsSet.append(cageMap[cage]['rear'])

        if not camLinked:
            print("No cameras linked to cages.")
            self.settingsCagesStore = settingsCages

            #return
        else:
            self.settingsCagesStore = settingsCages

        self.clientOptions._camSelects = listCamsSet
        self.clientOptions._camSelectsIsActive['isActive'] = True
        self.clientOptions.fps = settingsCages[cage]['fps']
        self.clientOptions.iso = settingsCages[cage]['iso']
        self.clientOptions.colorMode = settingsCages[cage]['color']
        self.clientOptions.compression = settingsCages[cage]['compression']
        self.clientOptions.autogain = settingsCages[cage]['autogain']
        self.clientOptions.rotation = settingsCages[cage]['rotation']
        self.clientOptions.zoomLocation = settingsCages[cage]['zoom location']
        self.clientOptions.brightness = settingsCages[cage]['brightness']
        ##contraster$
        self.clientOptions.contrast = settingsCages[cage]['contrast']
        self.clientOptions.zoomDimension = settingsCages[cage]['zoom dimension']
        self.clientOptions.vflip = settingsCages[cage]['vflip']
        self.clientOptions.gain = settingsCages[cage]['gain']
        self.clientOptions.camMap = settingsCages[cage]['camMap']


        self.clientOptions.shutterspeed = settingsCages[cage]['shutter speed']
        self.sendToAll('Camera', 'sync clocks')
        if bool(listCamsSet):
            for cam in listCamsSet:
                
                
                self.sendToSelect('Camera', 'set color mode', cam)
                self.sendToSelect('Camera', 'set rotation', cam)
                self.sendToSelect('Camera', 'set vflip', cam)
                self.sendToSelect('Camera', 'set brightness', cam)
                ##contraster$
                self.sendToSelect('Camera', 'set contrast', cam)
                self.sendToSelect('Camera', 'set ISO', cam)
                self.sendToSelect('Camera', 'set compression', cam)
                self.sendToSelect('Camera', 'set autogain', cam)
                self.sendToSelect('Camera', 'set gain', cam)
                self.sendToSelect('Camera', 'set zoom points', cam)
                self.sendToSelect('Camera', 'set zoom points', cam)
                self.sendToSelect('Camera', 'set camMap', cam)
                self.sendToSelect('Camera', 'set shutter speed', cam)
        logger.info('Set settings asynch')
        self.clientOptions._camSelectsIsActive['isActive'] = False
            #COUNTY = -1
            #self.clientOptions._camSelects = []
            #self.sendStartPreviewingMessages()
        if not camLinked: 
            self.cageSettingsSet = False
            self.cameraSettingsSet = True
        else:
            self.cageSettingsSet = True
            self.cameraSettingsSet = False    

    def sendStartPreviewingMessages(self) -> None:
        """Tells cameras to start previewing."""
        if not self.cameraSettingsSet:
            if not self.cageSettingsSet:
                self.sendSetSettingsMessages()
                self.cameraSettingsSet = True
                self.cageSettingsSet = False
        if not self.cageSettingsSet:
            if not self.cameraSettingsSet:
                other = 0
                for other in self.settingsCagesStore:
                    self.sendSetCagesMessages(other, cageMappy, mappy)
                self.cageSettingsSet = True
                self.cameraSettingsSet = False
 
        if self.previewing:
            raise RecordingOrStreamException(
                    'Cannot start previewing when already previewing')
        self.previewing = True
        logger.info('Start Previewing')
        self.sendToAll('Camera', 'start previewing')

    def sendStopPreviewingMessages(self) -> None:
        """Tells cameras to stop previewing."""
        if not self.previewing:
            raise RecordingOrStreamException('Cannot stop previewing when not previewing')
        self.previewing = False
        logger.info('Stop Previewing')
        self.sendToAll('Camera', 'stop previewing')

    def mappySetter(self, cageMappy: Dict[str, Union[str, Dict, bool]], mappy: Dict[str, Union[str, int, float, Tuple, Dict, List, bool]]) -> None:
        self.cageMappy = cageMappy
        self.mappy = mappy

    def sendSelectStartPreviewingMessage(self, cameraID: str) -> None:
        """Tells one camera that is provided to start previewing.

        :param cameraID: The id of the camera that should start previewing.
        :return: Nothing
        """
        if not self.cageMappy and not self.mappy:
            if not self.cameraSettingsSet and not self.cageSettingsOn:
                self.sendSetSettingsMessages()
                self.cameraSettingsSet = True
                self.cageSettingsSet = False
        else:
            if not self.cameraSettingsSet:
                if not self.cageSettingsSet:
                    self.sendSetSettingsMessages()
                    self.cameraSettingsSet = True
                    self.cageSettingsSet = False
            if not self.cageSettingsSet:
                if not self.cameraSettingsSet:
                    other = 0
                    for other in self.settingsCagesStore:
                        self.sendSetCagesMessages(other, self.cageMappy, self.mappy)
                    self.cageSettingsSet = True
                    self.cameraSettingsSet = False

        self.sendToSelect('Camera', 'start previewing', cameraID)
        logger.info('Started Previewing ' + str(cameraID))


    def searchForCage(self, cameraID: str) -> str:
        for cage in self.cageMapper:
            if 'main' in self.cageMapper[cage]: 
                if cameraID == self.cageMapper[cage]['main']:
                    return cage
            if 'front' in self.cageMapper[cage]:
                if cameraID == self.cageMapper[cage]['front']:
                    return cage
            if 'rear' in self.cageMapper[cage]:
                if cameraID == self.cageMapper[cage]['rear']:
                    return cage
        return ""

    def sendSelectStopPreviewingMessage(self, cameraID: str) -> None:
        """Tells the one camera that is provided to stop previewing.

        :param cameraID: The id of the camera that should stop previewing.
        :return: Nothing
        """

        self.sendToSelect('Camera', 'stop previewing', cameraID)
        logger.info('Stopped Previewing ' + str(cameraID))

    def sendSetSettingsMessages(self) -> None:
        """Sets all video viewing settings"""
        if not self.cageSettingsOn:
            #self.clientOptions.zoomDimension = (640, 480)
            self.sendToAll('Camera', 'sync clocks')
            self.sendToAll('Camera', 'set stream format')
            self.sendToAll('Camera', 'set FPS')
            self.sendToAll('Camera', 'set ISO')
            self.sendToAll('Camera', 'set shutter speed')
            #self.sendToAll('Camera', 'set dimension')
            self.sendToAll('Camera', 'set brightness')
            ##contraster$
            self.sendToAll('Camera', 'set contrast')
            self.sendToAll('Camera', 'set autogain')
            self.sendToAll('Camera', 'set zoom points')
            self.sendToAll('Camera', 'set color mode')
            self.sendToAll('Camera', 'set compression')
            self.sendToAll('Camera', 'set vflip')
            self.sendToAll('Camera', 'set gain')
            for cam in self.clientOptions.camMap:
                self.sendToSelect('Camera', 'set camMap', cam)
            for cam in self.clientOptions.rotation:
                self.sendToSelect('Camera', 'set rotation', cam)
            logger.info('Set settings')
            self.cameraSettingsSet = True
            self.cageSettingsSet = False

    def sendRebootMessage(self) -> None:
        """Tells whole system to reboot"""
        self.sendToAll('Camera', 'reboot')

    def sendRestartMessage(self) -> None:
        """Tells software to restart"""
        self.sendToAll('Camera', 'restart')

    def sendSetCageName(self) -> None:
        """Sets the cages of the cameras"""
        if not self.cageSettingsOn:
            for cam in self.clientOptions.camMap:
                self.sendToSelect('Camera', 'set camMap', cam)

    def sendSetView(self) -> None:
        """Sets the views of the cameras"""
        self.sendToAll('Camera', 'set view')

    def sendSyncClocks(self) -> None:
        """Syncs system time with clients"""
        self.sendToAll('Camera', 'sync clocks')


    #def delTempVids(self, filename: str, numFrames: int, _timestamp: str) -> None:
    #    import glob
    #    logger.info('Finished {}: {} frames'.format(
    #            utils.truncateFilename(filename), numFrames))

    #    path_mod = os.getenv("USERPROFILE") + r"\AppData\Local\Temp\gpac_*"
    #    for f in glob.glob(path_mod):
    #        print("removing file {}".format(f))
    #        try:
    #            os.remove(f)
    #        except Exception as err:
    #            print("Still using file {}. Error: {}".format(f, err))
                
        #pre = filename[:-4] #+ ".h264"
        ##otherName = filename.split('/', 0)
        ##print(otherName)
        #if os.path.isfile(pre + ".mp4") and os.path.isfile(pre + ".h264"):
        #    try:
        #        os.remove(pre + ".h264")
        #        p = pre + ".h264"
        #        print("Removing file: {}".format(p))
        #    except Exception as err:
        #        logger.info("Error in gpac.py: {}".format(err))
        ##print("other {}".format(other))

        #print('Finished {}: {} frames'.format(
        #        utils.truncateFilename(filename), numFrames))
    @staticmethod
    def error(client: 'ClientController', message: str) -> None:
        """Prints an error message to the console.

        :param client: The client that sent the error message.
        :param message: The error message sent by the client.
        :return: Nothing
        """
        #global COUNTY
        #if message.find('Unable to set frame rate of camera') != -1:
        #    COUNTY = -1
        print('{}: {}'.format(client.socket.getpeername(), message))
        logger.error('{}: {}'.format(client.socket.getpeername(), message))

    @staticmethod
    def downloadFinished(filename: str, numFrames: int, _timestamp: str) -> None:
        """Tells applications that a video has finished downloading.

        :param filename: The file where the download finished.
        :param numFrames: The number of frames in the file.
        :param _timestamp: The timestamp the download finished. Unused.
        :return: Nothing
        """
        import glob
        logger.info('Finished {}: {} frames'.format(
                utils.truncateFilename(filename), numFrames))

        path_mod = os.getenv("USERPROFILE") + r"\AppData\Local\Temp\gpac_*"
        for f in glob.glob(path_mod):
            print("removing file {}".format(f))
            try:
                print("file time since modified {}".format(os.path.getmtime(f)))
                print("time {}".format(time.time()))
                os.remove(f)
            except Exception as err:
                print("Still using file {}. Error: {}".format(f, err))


    def storeData(self, client: 'CameraClient', datatype: str, data: float) -> None:
        """Stores data from the client.

        :param client: The client the data came from.
        :param datatype: What kind of data is passed.
        :param data: The data being passed from the client.
        :return: Nothing
        """
        
        name = client.cameraID
        try:
            name = "{} {}".format(self.clientOptions.camMap[name], name)
        except KeyError:
            pass
        ln = "{} [{}]: {} = {}".format(time.strftime('%Y-%m-%d %H:%M:%S'), name,
                                       datatype, data)
        with open(os.path.join(self.options.baseDirectory, 'data.log'), 'a') as f:
            print(ln, file=f)


class CameraServerController(threading.Thread):
    """Controller for the SCORHE server application.

    Provides a number of controls associated with user actions.

    This is literally a queue wrapper for the user input.

    This thread can be bypassed by calling the serverThread directly (not
    threadsafe).
    """

    __slots__ = ('server', 'splitScheduler', 'recordStartTime', 'asyncQueue')

    def __init__(self, serverOptions):
        threading.Thread.__init__(self)
        # Reference to the server thread
        self.server = CameraServer(24461, self, serverOptions)  # type: CameraServer
        # Scheduler for splitting recordings (default is 120 seconds)
        self.splitScheduler = None
        # Variable to sync recordings
        self.recordStartTime = None
        # Reference to the asynchronous queue to run functions, well, asynchronously
        self.asyncQueue = protocol.AsyncFunctionQueue()
        # Dictionaries to schedule for splitting recordings and recording times of each individual cage.
        self.splitSchedulerCage = {}
        self.recordStartTimeCage = {}
        self.synch = False
    def run(self) -> None:
        """Run a protocol using a thread-safe queue to register events."""
        self.asyncQueue.start()
        logger.info('Controller shut down')

    def startRecording(self) -> None:
        """Invoke this to have the cameras start recording."""
        #self.server.ca
        try:
            self.recordStartTime = time.time() + 1
            self.asyncQueue.call(self.server.sendStartRecordingMessages)
            self.splitScheduler = threading.Timer(
                    self.server.options.segmentSize*60 , self.splitRecording)
            self.splitScheduler.start()
        except RecordingOrStreamException as err:
            logger.error(err)

    def splitRecording(self) -> None:
        """Called periodically to make the cameras record into a new file."""
        try:
            self.recordStartTime = time.time()
            self.asyncQueue.call(self.server.sendSplitRecordingMessages)
            self.splitScheduler = threading.Timer(
                    self.server.options.segmentSize*60, self.splitRecording)
            self.splitScheduler.start()
        except RecordingOrStreamException as err:
            logger.error(err)

    def stopRecording(self) -> None:
        """Invoke this to have the cameras stop recording."""
        try:
            self.asyncQueue.call(self.server.sendStopRecordingMessages)
            self.splitScheduler.cancel()
        except RecordingOrStreamException as err:
            logger.error(err)


    def toggleRecording(self, cageMap: Dict[str, Union[str, Dict, bool]], recordAll=False) -> None:
        """Invoke this to have the cameras switch between recording and not."""

        #self.synch = not(self.synch)
        #if recordAll:
        #    if not bool(self.server.cageMapper):
        #        self.server.cageMapper = copy.deepcopy(cageMap)
        #else:
        #    print(cageMap)
        if not bool(self.server.cageMapper):
            self.server.cageMapper = copy.deepcopy(cageMap)
        if self.server.recording:
            self.stopRecording()
        else:
            self.startRecording()

#****************************************************************Asynchronous Recording Methods******************************************************
    def startRecordingCage(self, cage: str, cageMap: Dict[str, Union[str, Dict, bool]]) -> None:
        try:
            self.recordStartTimeCage[cage] = time.time() + 1 
            self.asyncQueue.call(self.server.sendStartRecordingMessagesCage)
            segSize = self.server.options.segmentSize
            if self.server.settingsCagesStore:
               if self.server.settingsCagesStore[cage]['len']:
                   segSize = self.server.settingsCagesStore[cage]['len']

            holder = {cage: threading.Timer(segSize*60, self.splitRecordingCage, args=(cage, cageMap,))}
            self.splitSchedulerCage.update(holder)
            self.splitSchedulerCage[cage].start()
        except RecordingOrStreamException as err:
            logger.error(err)

    def splitRecordingCage(self, cage: str, cageMap: Dict[str, Union[str, Dict, bool]]) -> None:
        try:
            self.recordStartTimeCage[cage] = time.time()
            #self.recordStartTime = time.time()
            self.asyncQueue.call(self.server.sendSplitRecordingMessagesCage, cage)
            segSize = self.server.options.segmentSize
            if self.server.settingsCagesStore:
               if self.server.settingsCagesStore[cage]['len']:
                   segSize = self.server.settingsCagesStore[cage]['len']


            holder = {cage: threading.Timer(segSize*60, self.splitRecordingCage, args=(cage, cageMap,))}
            self.splitSchedulerCage.update(holder)
            
            self.splitSchedulerCage[cage].start()
            print("\n [[[[[[[[ self.splitSchedulerCage: {} \n".format(self.splitSchedulerCage))
        except RecordingOrStreamException as err:
            logger.error(err)

    def stopRecordingCage(self, cage: str, cageMap: Dict[str, Union[str, Dict, bool]]) -> None:
        try:
            self.asyncQueue.call(self.server.sendStopRecordingMessagesCage)
            #print(self.splitSchedulerCage)
            if self.splitSchedulerCage[cage] is not None and self.splitSchedulerCage[cage].isAlive():
                self.splitSchedulerCage[cage].cancel()
        except RecordingOrStreamException as err:
            logger.error(err)

    def toggleRecordingCage(self, cage: str, cageMap: Dict[str, Union[str, Dict, bool]]) -> None:
        """Invoke this to have the cameras switch between recording and not."""
        self.server.cageSelect = cage
        if self.synch:
            print("Cannot start recording on cage {} when in synchronous mode.".format(cage))
        else:
            if not bool(self.server.cageMapper):
                self.server.cageMapper = copy.deepcopy(cageMap)
            if cage and bool(cageMap):
                if self.server.cageMapper[cage]['isRecording']:
                    #self.stopRecordingCage(self.server.cageSelect, self.server.cageMapper)
                    self.stopRecordingCage(cage, self.server.cageMapper)
                else:
                    #self.startRecordingCage(self.server.cageSelect, self.server.cageMapper)
                    self.startRecordingCage(cage, self.server.cageMapper)
            elif (not cage) and (not bool(cageMap)):
                logger.error('Please insert a valid cage and create a cage.')
            elif not cage:
                logger.error('Please insert a valid cage.')
            else:
                logger.error('Please create a cage.')


    def stopRecordingAllCages(self, cageMap: Dict[str, Union[str, Dict, bool]]) -> None:
        if cageMap:
            for cage in cageMap:
                # if self.splitSchedulerCage:
                    # if self.splitSchedulerCage[cage] is not None and self.splitSchedulerCage[cage].isAlive():
                        # self.splitSchedulerCage[cage].cancel()
                if cageMap[cage]['isRecording'] or self.server.cageMapper[cage]['isRecording']:
                    self.server.cageSelect = cage
                    self.stopRecordingCage(cage, cageMap)
                    self.server.cageMapper[cage]['isRecording'] = False
                
        if self.server.recording:
            #self.server.recording = False
            self.stopRecording()
            self.server.recording = False
            

        #self.asyncQueue.call(self.server.sendStopRecordingAllMessages)

    def rebootCage(self, cage: str) -> None:
        """Sends a message to reboot an individual cage of cameras utilizing a specified cage. """
        self.server.cageSelect = cage
        self.asyncQueue.call(self.server.sendRebootMessageCage)

    def restartCage(self, cage: str) -> None:
        """Sends a message to restart an individual cage of cameras utilizing a specified cage. """
        self.server.cageSelect = cage
        self.asyncQueue.call(self.server.sendRestartMessageCage)




    def startPreviewing(self) -> None:
        """Invoke this to have the cameras start previewing."""
        try:
            self.asyncQueue.call(self.server.sendStartPreviewingMessages)
        except RecordingOrStreamException as err:
            logger.error(err)

    def stopPreviewing(self) -> None:
        """Invoke this to have the cameras stop previewing."""
        try:
            self.asyncQueue.call(self.server.sendStopPreviewingMessages)
        except RecordingOrStreamException as err:
            logger.error(err)

    def togglePreviewing(self) -> None:
        """Invoke this to have the cameras switch between previewing and not."""
        if self.server.previewing:
            self.stopPreviewing()
        else:
            self.startPreviewing()

    def reboot(self) -> None:
        """Sends a message to reboot all the cameras."""
        self.asyncQueue.call(self.server.sendRebootMessage)

    def restart(self) -> None:
        """Sends a message to restart all the cameras."""
        self.asyncQueue.call(self.server.sendRestartMessage)

    def close(self) -> None:
        """Gracefully shut down the server."""
        if self.server.recording:
            self.stopRecording()
        if self.server.previewing:
            self.stopPreviewing()
        self.asyncQueue.finish()
        self.server.shutdown()



class ClientRequestHandler(socketserver.StreamRequestHandler):
    """Handler class that keeps a connection between a client and the server.

    Handle is called once per object, and attempts to register the client.
    """

    def handle(self) -> None:
        """Handles a new connection.

        The client starts out as an UnregisteredClient, but then becomes a
        CameraClient or an ApplicationClient when a valid handshake is
        received.

        :return: Nothing
        """
        #print("REqurest {}".format(self.request))
        #logger.info('Server socket connection: {}'.format(self.request))
        logger.debug('Server socket connection: {}'.format(self.request))
        client = self.server.clients.getClient(self.request)
        #print("Called")
        
        if not client:
            client = self.server.clients.register(self.server,
                                                  self.request, 'Unregistered')
            
        try:
            while True:
                incomingMessage = self.request.recv(1024)
                if not incomingMessage:
                    #print("No incoming message")
                    logger.debug('No incoming message, exiting {}'.format(self.request.getpeername()))
                    return
                client = self.server.clients.getClient(self.request)
                client.handle(self.server, incomingMessage)
        except ConnectionResetError as e:
            logger.warning('{}: connection closed'.format(
                    client.socket.getsockname()[0]))
            
            self.server.clients.unregister(self.request,
                                           client.clientType)
        finally:
            self.request.close()


class ClientConnections:
    """A container object for all clients."""
    unregisteredProtocol = server_protocols.UnregisteredProtocol()
    cameraProtocol = server_protocols.CameraProtocol()

    def __init__(self):
        # Dictionary to keep track of client types
        self.clients = {'Unregistered': {},
                        'Camera': {}}  # type: dict[str: dict[str: ClientController]]
        # Dictionary to keep track of different protocols to be used
        self.protocols = {'Unregistered': ClientConnections.unregisteredProtocol,
                          'Camera': ClientConnections.cameraProtocol}
        #print("runbbbb")

    def register(self,
                 server: CameraServer,
                 sock: socket.socket,
                 clientType: str,
                 *args) -> 'ClientController':
        """Registers the given socket as a client of the given type.

        Prevent a potential DDOS attack that sends multiple handshakes by
        first checking that a client object isn't already registered.

        :param server: The server to register the client with.
        :param sock: The socket connecting to the client.
        :param clientType: The type of client being registered (Unregistered or
            Camera), being where it should be looked for in the future.
        :return: The client that got registered.
        """
        #print("called")
        logger.info("register was called ")
        if sock not in self.clients[clientType].keys():
            self.clients[clientType][sock] = makeClient(
                    server, sock, clientType, self.protocols[clientType], *args)
        return self.clients[clientType][sock]

    def unregister(self, sock: socket.socket, clientType: str) -> None:
        """Unregisters the socket as the given client type.

        :param sock: The socket of the client to remove.
        :param clientType: The type of the client to remove (Unregistered or
            Camera)
        :return Nothing
        """
        try:
            del self.clients[clientType][sock]
        except KeyError:
            logger.debug(self.clients)
            logger.debug(clientType)
            logger.debug(sock)
            pass

    def getClient(self, sock: socket.socket) -> Optional['ClientController']:
        """Returns a handle to the client with the given socket.

        If the socket has connected before, find it in the list of registered
        clients and return it.

        :param sock: The socket belonging to the client that is being looked up.
        :return: The client with the given socket, or None if the client cannot
            be found.
        """
        # noinspection PyTypeChecker
        
        for clients in self.clients.values():
            
            if sock in clients:
                return clients[sock]
        # Return None if the socket is not registered in any category
        return None

    def getClients(self, clientType: str) -> Iterable['ClientController']:
        """Returns a list of all clients of the given type.

        :param clientType: The type of client (Unregistered or Camera)
        :return: A list of all the clients of a given type.
        """
        return self.clients[clientType].values()

    def sendToAll(self,
                  server: CameraServer,
                  clientType: str,
                  messageID: str,
                  *args) -> None:
        """Send a message to all clients of the given type.

        :param server: The server object handling the clients.
        :param clientType: The type of the clients (Unregistered or Camera)
        :param messageID: The id of the message, i.e. the key for the protocol
            rule to run.
        :return: Nothing
        """
        # noinspection PyTypeChecker
        #if len(self.clients[clientType].values()) == 0:
        #    logger.info("Called sendToAll however values are empty")
        for client in self.clients[clientType].values():
            client.send(server, messageID, *args)
            #print("happened")
            if messageID == "stop previewing" and client.previewSocket is not None:
                client.previewSocket.close()

    def sendToSelect(self,
                     server: CameraServer,
                     clientType: str,
                     messageID: str,
                     cameraID: str,
                     *args) -> None:
        """Sends a message to a client with a specific type and id.

        Simply calls ``sendToSelects`` with a list of a single camera id.

        :param server: The server object handling the clients.
        :param clientType: The type of the client (Unregistered or Camera)
        :param messageID: The id of the message, i.e. the key for the protocol
            rule to run.
        :param cameraID: The camera ids for the clients to send the message to.
        :return: Nothing
        """

        self.sendToSelects(server, clientType, messageID, [cameraID], *args)

    def sendToSelects(self,
                      server: CameraServer,
                      clientType: str,
                      messageID: str,
                      cameraIDs: Iterable[str],
                      *args) -> None:
        """Sends a message to clients with a specific type with on of many ids.

        :param server: The server object handling the clients.
        :param clientType: The type of the clients (Unregistered or Camera)
        :param messageID: The id of the message, i.e. the key for the protocol
            rule to run.
        :param cameraIDs: A list of the camera ids for the clients to send the
            message to.
        :return: Nothing
        """
        #if len(self.clients[clientType].values()) == 0:
        #    logger.info("Called sendToSelects however values are empty")
        cameraIDs = set(cameraIDs)
        #print("cameraIDs: %s" % cameraIDs)
        # noinspection PyTypeChecker
        #print("self.clients in sendToSelects %s" % self.clients)
        for client in self.clients[clientType].values():
            if client.cameraID in cameraIDs:
                #print("client: %s" % client)
                #print("client.cameraID: %s" % client.cameraID)
                #print("cameraIDs: %s" % cameraIDs)
                client.send(server, messageID, *args)
                if messageID == "stop previewing" and client.previewSocket is not None:
                    client.previewSocket.close()


def makeClient(server: CameraServer,
               clientSocket: socket.socket,
               clientType: str,
               clientProtocol: protocol.Protocol,
               *args) -> 'ClientController':
    """A factory function for clients.

    This function is needed because when a client connects, its handshake
    introduces itself as a given type of client, and the string representing
    that client type needs to be mapped to the appropriate object.

    A camera client should have 4 or five extra parameters, where it should be
    cageID, cameraID, cameraView and cageName. If there are five parameters,
    it should come before all the others and be the client version, but is
    currently ignored.

    :param server: The server to register the client to.
    :param clientSocket: The socket used to communicate with the actual client.
    :param clientType: The type this client is (Unregistered or Camera).
    :param clientProtocol: The protocol that this client should use when
        communicating.
    :return: An UnregisteredClient if the type is Unregistered with the given
        parameters, or a CameraClient if the type is Camera with the given
        parameters and the additional args.
    """
    logger.info("client type (line 1713): {}".format(clientType))
    if clientType == 'Unregistered':
        #print("called")
        return UnregisteredClient(server, clientSocket, clientProtocol)
    elif clientType == 'Camera':
        return CameraClient(server, clientSocket, clientProtocol, *args)
    else:
        raise Exception('clientType must be either "Unregistered", ' +
                        '"Camera"')


class ClientController:
    """Parent class for client objects.

    All client controller objects can both send and handle (react to)
    messages.
    """

    def __init__(self, server, clientSocket, clientProtocol):
        # Relevant overall client information
        self.server = server  # type: CameraServer
        self.socket = clientSocket  # type: socket.socket
        self.protocol = clientProtocol  # type: protocol.Protocol
        self.buffer = b''  # type: bytes
        

    def send(self, server: CameraServer, messageID: str, *args) ->None:
        """Send a message with the given ID to the client.

        :param server: The server sending the message.
        :param messageID: The ID of the message, i.e. the key which is the
            index of the handler that is being requested.
        :return: Nothing
        """
        global COUNTY
        message = self.protocol.buildMessage(messageID, server, self, *args)
        try:
            self.socket.sendall(message)
            #if str(protocol.Syntax.formatMessage(message))[0:3] == 'set' :
            #    print('{} <- {}'.format(self.socket.getpeername()[0],
            #                            protocol.Syntax.formatMessage(
            #                                    message)))
            #    COUNTY += 1
            #    print('County: %s' % COUNTY)
            #    #print("self.server.clients: %s" % self.server.clients)
            #    #print("curr socket: %s" % self.socket)
            #    #print("self.server.clients.clients.values(): %s" % self.server.clients.clients.values())
            #    #print("server.clients.clients.values(): %s" % server.clients.clients.values())
            #    #print("server.clients.clients: %s" % server.clients.clients)
            #    #print("server.clients.clients camera: %s" % server.clients.clients['Camera'])
            #    #for c in server.clients.clients['Camera'].values():
            #        #if c.cameraID in 
            #        #    print(c)
            ##print(type(self.socket))
            ##print('{} <- {}'.format(self.socket.getpeername()[0], server.clients.getClient(self.socket) ))
            if logger.isEnabledFor(logging.DEBUG):

                logger.debug('{} <- {}'.format(self.socket.getpeername()[0],
                                               protocol.Syntax.formatMessage(
                                                       message)))
        except OSError:
            logger.error('ERROR sending message {} to {}'.format(messageID,
                                                                 self.socket))

    def handle(self, server: CameraServer, buffer: bytes) -> None:
        """Handle messages in the buffer.

        The buffer can contain multiple concatenated messages, or partial
        messages.

        :param server: The server object controlling this client and receiving
            the buffer.
        :param buffer: A buffer send from the client.
        :return: Nothing
        """
        self.buffer += buffer
        self.buffer = self.protocol.handleBuffer(self.buffer, server, self)
        if logger.isEnabledFor(logging.DEBUG):
            for message in \
                    protocol.Syntax.formatMessage(buffer).split(');')[:-1]:
                logger.debug('{} -> {}'.format(self.socket.getpeername()[0],
                                               message + ');'))


    def sendSpecial(self, server: CameraServer, messageID: str, *args) -> None:
        """Send a message with the given messageID to a specific client rather than all the clients.
        See send() for details on sending a messageID to all clients.
        :param server: The server sending the message
        :param messageID: The ID of the message, i.e. the key which is the
            index of the handler that is being requested.
        :return: Nothing
        """
        server.clients.getClient(self.socket)
       


class UnregisteredClient(ClientController):
    """A client whose type is unknown."""

    def __init__(self, server, clientSocket, clientProtocol):
        ClientController.__init__(self, server, clientSocket, clientProtocol)
        self.clientType = 'Unregistered'  # type: str


class CameraClient(ClientController):
    """A client connection to a Raspberry Pi camera unit."""

    def __init__(self, server, clientSocket, clientProtocol, *args):
        ClientController.__init__(self, server, clientSocket, clientProtocol)
        self.clientType = 'Camera'  # type: str
        # Time stamp queue
        logger.info("Args in CameraClient: {}".format(args))
        self.timestamps = queue.Queue()  # type: queue.Queue
        # socket for previewing (So we can close later)
        self.previewSocket = None  # type: socket.socket
        self.previewPort = None  # type: int
        if len(args) == 4:
            self.cageID = args[0]  # type: str
            self.cameraID = args[1]  # type: str
            self.cameraView = args[2]  # type: str
            self.cageName = args[3]  # type: str
        elif len(args) == 5:
            self.cageID = args[1]  # type: str
            self.cameraID = args[2]  # type: str
            self.cameraView = args[3]  # type: str
            self.cageName = args[4]  # type: str
        logger.info('Camera: {}'.format(self.cameraID))
        #print(self.cageName)
        # Send handshake response
        # THIS IS WHERE THE TRUE SETTINGS ARE SET *********&&&&&&
        #print("This is the server: %s  self socket: %s  clientSocket: %s" % (server, self.socket, clientSocket))
        self.send(server, 'handshake')
        #self.server.sendSetSettingsMessages()
        self.recording = False
        #self.send(server, 'set FPS')
        #self.send(server, 'set vflip')
        #self.send(server, 'set color mode')
        #self.send(server, 'set autogain')
        #self.send(server, 'set gain')
        #self.send(server, 'set ISO')
        #self.send(server, 'set brightness')
        #self.send(server, 'set rotation')
        #self.send(server, 'set zoom points')
        #self.send(server, 'set camMap')
        #self.send(server, 'set compression')
        # Notify this camera of siblings and vice-versa
        for sibling in server.clients.getClients('Camera'):
            if sibling.socket.getpeername()[0] != self.socket.getpeername()[0]:
                sibling.send(server, 'sibling',
                             self.socket.getpeername()[0])
                self.send(server, 'sibling', sibling.socket.getpeername()[0])

    def getFreeSocket(self) -> socket.socket:
        """Function will get a free socket that can be used.

        :return: A new socket after storing it in ``previewSocket``
        """
        freeSocket = socket.socket()
        freeSocket.bind(('', 0))
        self.previewSocket = freeSocket
        self.previewPort = freeSocket.getsockname()[1]
        return freeSocket

    def streamVideoToFile(self, filename: str, width: int, height: int) -> int:
        """Stream a video from this camera client to the given filename.

        This is done asynchronously because there is a scalable number of pis,
        and includes conversion from H.264 to MP4 video if necessary.

        :param filename: The name of the file to stream to.
        :param width: The width of the image being captured (used to create
            missing headers if they ever happen).
        :param height: The height of the image being captured (used to create
            missing headers if they ever happen).
        :return: The port of the socket for the stream.
        """
        cage = ""
        cager = {}
        def findSPSHeader(buffer: bytes) -> int:
            """Returns the location of the first SPS header in the buffer.

            :param buffer: The buffer to find the SPS header.
            :return: The index in the given buffer of the SPS header.
            """
            #print("StreamThread SPS Header: {}".format(StreamThread.SPSHE))
            return buffer.find(StreamThread.SPSHeader)

        class StreamThread(threading.Thread):
            """Asynchronous streaming thread for videos."""
            SPSHeader = bytes.fromhex('0000000127')
            #print(SPSHeader)
            PPSHeader = bytes.fromhex('0000000128')

            # noinspection PyShadowingNames
            def __init__(self, server, client, filename, clientSocket, width, height):
                threading.Thread.__init__(self)
                self.server = server  # type: CameraServer
                self.client = client
                self.filename = filename
                self.width = width
                self.height = height

                self.socket = clientSocket
                self.daemon = True
                self.byteRate = []
            def downloadVideo(self) -> bool:
                """Threads inner method to download a video. This method is called in run.

                :return: ``True`` if the download finished without exceptions.
                """
                connection = self.socket.accept()[0]
                inputStream = connection.makefile('br')
                outputFile = open(self.filename, 'bw')
                bytesReadSinceSPSHeader = 0

                buffer = inputStream.read(8196)


                logger.debug('File {} at time {}'.format(self.filename, time.strftime('%H:%M:%S')))
                while buffer:
                    spsHeaderIndex = findSPSHeader(buffer)
                    if spsHeaderIndex > -1:
                        bytesReadSinceSPSHeader += spsHeaderIndex
                        self.byteRate.append(bytesReadSinceSPSHeader)
                        bytesReadSinceSPSHeader = 0
                        #print("h")
                    outputFile.write(buffer)
                    buffer = inputStream.read(8196)
                    #print("ByteRate: {}".format(self.byteRate))
                    
                # Close everything up
                #print("lenBuffer: {}".format(lenBuffer)) # 192932
                connection.close()
                self.socket.close()
                outputFile.close()
                return True

            def run(self) -> None:
                """Start the thread to download a client's video"""
                if self.downloadVideo():
                    finishTime = self.client.timestamps.get()
                    self.client.timestamps.task_done()
                    if self.server.options.format == 'h264':
                        newfilename = self.filename.rstrip('h264') + 'mp4'
                        gpac.makeMP4(self.filename, newfilename,
                                     self.server.clientOptions.fps,
                                     self.width,
                                     self.height)
                        self.filename = newfilename
                    time.sleep(1)
                    numFrames = gpac.getNumFrames(self.filename)
                    print("numFrames {}".format(numFrames))
                    self.server.downloadFinished(
                            self.filename, numFrames, utils.convertTimestamp(
                                    finishTime))
                    #self.server.delTempVids(self.filename, numFrames, utils.convertTimestamp(finishTime))
                    #t1 = threading.Thread(target=self.server.delTempVids, args = [self.filename, numFrames, utils.convertTimestamp(finishTime)])
                    #t1.start()
                    #t1.join()

        streamSocket = socket.socket()
        streamSocket.bind(('', 0))
        streamSocket.listen(1)
        streamThread = StreamThread(self.server, self, filename, streamSocket,
                                    width, height)
        streamThread.start()
        return streamSocket.getsockname()[1]
        #    def downloadVideo(self) -> bool:
        #        """Threads inner method to download a video. This method is called in run.

        #        :return: ``True`` if the download finished without exceptions.
        #        """
        #        connection = self.socket.accept()[0]
        #        inputStream = connection.makefile('br')
        #        outputFile = open(self.filename, 'bw')

        #        bytesReadSinceSPSHeader = 0
        #        buffer = inputStream.read(8196)
        #        #buffer = inputStream.read()
        #        logger.debug('File {} at time {}'.format(self.filename, time.strftime('%H:%M:%S')))
        #        while buffer:
        #            spsHeaderIndex = findSPSHeader(buffer)
        #            if spsHeaderIndex > -1:
        #                bytesReadSinceSPSHeader += spsHeaderIndex
        #                self.byteRate.append(bytesReadSinceSPSHeader)
        #                bytesReadSinceSPSHeader = 0
        #            outputFile.write(buffer)
        #            #buffer = inputStream.read()
        #            buffer = inputStream.read(8196)
        #        # Close everything up
        #        connection.close()
        #        self.socket.close()
        #        outputFile.close()
        #        return True
        #    ################################################################################################################################COULD THE PROBLEM BE HERE
        #    def run(self) -> None:
        #        """Start the thread to download a client's video"""

        #        if self.downloadVideo():
        #            finishTime = self.client.timestamps.get()
        #            self.client.timestamps.task_done()
        #            #if self.client.cageID == 'cagerep':
        #            #    self.client.cageID = 'cage1'
        #            newfilename = self.filename.rstrip('h264') + 'mp4'
        #            if self.server.options.format == 'h264' and self.server.cageSettingsSet and bool(self.server.settingsCagesStore):

        #                substr = self.filename.split('/', 1)
        #                cage = (((substr[1].split('s ', 1))[1]).split(' ', 1))[0]
        #                #if cage == 'cage1':
        #                #    print(self.server.settingsCagesStore[cage]['fps'])
        #                gpac.makeMP4(self.filename, newfilename,
        #                                self.server.settingsCagesStore[cage]['fps'],
        #                                self.width,
        #                                self.height)
        #                self.filename = newfilename
        #            elif self.server.options.format == 'h264':
        #                gpac.makeMP4(self.filename, newfilename,
        #                                self.server.clientOptions.fps,
        #                                self.width,
        #                                self.height)
        #                self.filename = newfilename


        #        time.sleep(1)
        #        numFrames = gpac.getNumFrames(self.filename)
        #        print("print get numFrames in downloadVideo: %s" % numFrames)
        #        print("cage %s" % self.client.cageName)
        #        #if cage == 'cage1': finishTime = 1599230614.5451648
        #        print("finishTime %s" % finishTime)
        #        self.server.downloadFinished(
        #                self.filename, numFrames, utils.convertTimestamp(
        #                        finishTime))
                

        #streamSocket = socket.socket()
        #streamSocket.bind(('', 0))
        #streamSocket.listen(1)
        #if self.server.options.format == 'h264' and self.server.cageSettingsSet and bool(self.server.settingsCagesStore): 
        #    cager.update([(cage, StreamThread(self.server, self, filename, streamSocket,
        #                            width, height))])
        #    cager[cage].start()
        #elif self.server.options.format == 'h264':
        #    streamThread = StreamThread(self.server, self, filename, streamSocket,
        #                                width, height)
        #    streamThread.start()
        #return streamSocket.getsockname()[1]


class KeyboardThread(threading.Thread):
    """A thread handling command-line user input. This thread is technically not
    needed but can be used for debugging if the GUI breaks down.
    """

    def __init__(self, controller):
        threading.Thread.__init__(self)
        self.daemon = True
        self.controller = controller

    def run(self) -> None:
        """Loops infinitely listening for r to to toggle recording and q to quit."""
        try:
            while True:
                # Videos recorded will show up in the same folder as this file
                print('Press enter r to toggle recording \n Press q to close controller')
                print('Press m for more messages.')
                choice = input()
                if choice == 'r':
                    self.controller.toggleRecording()
                if choice == 'q':
                    self.controller.close()
                #if choice == 'm':
                #    self.server.show.Messages
                    #self.server.
                time.sleep(1)
        except KeyboardInterrupt:
            self.controller.close()


def getBroadcastAddress(address: str, mask: str) -> str:
    """Get address that will reach everyone on local network

    :param address: The address of a device on the network looking for a
        broadcast address.
    :param mask: The bitmask for the network, as either number of bits or
        formatted like an IP address (e.g. 24 vs 255.255.255.0)
    :return: the address to send a UDP broadcast packet to reach everyone on
        the local network
    """
    return ipaddress.IPv4Network(address + '/' + mask,
                                 False).broadcast_address.compressed


def get_ip_address(ifname: str='wlan0') -> Union[Dict[str, str], List[str]]:
    """
    This function is used to pull the local ip associated from an interface.
    This code is in the creative commons (CC-BY-SA) and can be found at
    http://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python

    :param ifname: The name of the network device to check (for linux).
    :return: A dict specifying the data related to the ip address of the
        computer.
    """

    if platform.system() == 'Windows':
        import subprocess
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        data = defaultdict(list)
        with subprocess.Popen('ipconfig', stdout=subprocess.PIPE) as sp:
            for line in sp.stdout.read().decode().splitlines():
                line = line.lstrip().rstrip()  # type: str
                if ': ' not in line:
                    continue
                if line.startswith('Connection-specific DNS Suffix'):
                    data['csds'].append(line.rsplit(': ', 1)[1])
                elif line.startswith('Link-local IPv6 Address'):
                    data['ipv6'].append(line.rsplit(': ', 1)[1])
                elif line.startswith('IPv4 Address'):
                    data['ipv4'].append(line.rsplit(': ', 1)[1])
                elif line.startswith('Subnet Mask'):
                    data['mask'].append(line.rsplit(': ', 1)[1])
                elif line.startswith('Default Gateway'):
                    data['gate'].append(line.rsplit(': ', 1)[1])
        if 'ipv4' not in data or 'mask' not in data:
            # probably not good
            pass

        return data
    elif platform.system() == 'Linux':
        import subprocess
        data = defaultdict(list)
        count = 0
        with subprocess.Popen(['ifconfig', '-a'], stdout = subprocess.PIPE) as sp:
            for line in sp.stdout.read().decode().splitlines():
                line = line.lstrip().rstrip()
                print(line)
                if line.startswith('eth0') and line.find('RUNNING'):
                    count = 2
                elif line.startswith('inet') and count == 2:
                    data['ipv4'].append(line.rsplit()[1])
                    data['mask'].append(line.rsplit()[3])
                    count = 1
                    break

        if count == 1:
            path = "/etc/resolv.conf"
            with open(path) as fp:
                all_line = fp.readline()
                cnt = 1
                while not all_line.startswith('search'):
                    all_line = fp.readline()
                else:
                    data['csds'].append(all_line.rsplit()[1])
                fp.close()
        if 'ipv4' not in data or 'mask' not in data:
            # probably not good
            pass

        return data
    else:
        raise OSError('SCORHE Acquisition does not support your system: {}'.format(platform.system()))

class AdvertThread(threading.Thread):
    """Advertises this server's IP address on the network

    Uses UDP broadcast packets to send alert to everyone on the network that
    the server is up and running. Computers running the SCORHE_client software
    will detect these messages and connect automatically.
    """

    def __init__(self, port=8890):
        threading.Thread.__init__(self)
        self.daemon = True
        self.port = port

    def run(self) -> None:
        """Resolves broadcast addresses on the network and broadcasts its ip and port infinitely."""
        ipData = get_ip_address()

        # this regex prevents broadcasting while connected to the nih network,
        # or any time the computer is connected to anything that isn't a linksys
        # router. in theory.
        csds_re = re.compile('router[0-9a-f]{6}\.com')
        if 'csds' not in ipData:
            logger.info('Not broadcasting.')
            return
        for i in range(0, len(ipData['csds'])):
            if csds_re.match(ipData['csds'][i]):
                break
        else:
            logger.info('Not broadcasting.')
            return
        ip = ipData['ipv4'][i]
        mask = ipData['mask'][i]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                          socket.IPPROTO_UDP)
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast = getBroadcastAddress(ip, mask)
        while True:
            s.sendto(ip.encode(), (broadcast, self.port))
            time.sleep(5)


        

class PokeThread(threading.Thread):
    """Send pokes to ensure connections are alive.

    This thread simply sends a "poke" message every minute to each client,
    ensuring that the connection is still alive (there are some rare
    circumstances where a socket can disconnect without notification, and a
    periodic poke can proactively detect such cases)
    """

    def __init__(self, server):
        threading.Thread.__init__(self)
        self.daemon = True
        self.server = server

    def run(self) -> None:
        """Pokes the client every 60 seconds, forever."""
        while True:
            time.sleep(60)
            self.server.sendToAll('Camera', 'poke')

##################################################################################################################################################################################################################################################################
def masterRunServer(argv: List[str]) -> Tuple[CameraServerController, ServerThread]:
    """Function that launches the whole server.

    :param argv: The command line arguments passed to the program. Used for
        dictating some settings for the server. See parseArgv for more details.
    :return: The threads for the controller and the server.
    """
    # Get args if running from command line
    serverOptions = parseArgv(argv)  # type: ServerOptions
    # Start Broadcasting out to whole network
    broadcastThread = AdvertThread()
    # Start the Server controller
    controllerThread = CameraServerController(serverOptions)
    # Start the actual server
    serverThread = ServerThread(controllerThread.server)
    # If the server is being launched via command line how to handle keyboard  
    keyboardThread = KeyboardThread(controllerThread)
    keyboardThread.start()  # doesnt broadcast, so it's ok
    # Keep the connections alive by poking
    pokeThread = PokeThread(controllerThread.server)

    broadcastThread.start()
    controllerThread.start()
    serverThread.start()
    pokeThread.start()

    return controllerThread, serverThread


def main(argv: List[str]) -> None:
    """This main method just runs the master start function.

    :param argv: The command line arguments passed to the program. Used for
        dictating some settings for the server. See masterRunServer and
        parseArgv for more details.
    """
    controllerThread, serverThread = masterRunServer(argv)
    for thread in [controllerThread, serverThread]:
        thread.join()
    logger.info('Shut down successful')


if __name__ == '__main__':
    print('{} v{}'.format(NAME, VERSION))
    main(sys.argv[1:])
