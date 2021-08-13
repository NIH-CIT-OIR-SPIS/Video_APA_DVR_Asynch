import fractions
import io
import logging
import os
import picamera
import pwd
import select
import shlex
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import copy

try:
    from PyQt5 import QtWidgets
except ImportError:
    try:
        from PyQt4 import QtGui as QtWidgets
    except ImportError:
        QtWidgets = None

import protocol
try:
    import screen
except ImportError:
    screen = None

# typing imports
try:
    from typing import Any, Union, Dict, Tuple
except ImportError:
    class _typing:
        def __getitem__(self, item):
            return item
    Union = _typing()
    Dict = _typing()
    Tuple = _typing()

logger = logging.getLogger(__name__)

NAME = 'VideoAPA_client'
VERSION = '1.0.4'
BITRATE = 25000000
BITRATE_PREV = 50000
#BITRATE = 25000000
# class StreamingOutput(object):
#     def __init__(self):
#         self.frame = None
#         self.buffer = io.BytesIO()
#         self.condition = Condition()
# 
#     def write(self, buf):
#         if buf.startswith(b'\xff\xd8'):
#             # New frame, copy the existing buffer's content and notify all
#             # clients it's available
#             self.buffer.truncate()
#             with self.condition:
#                 self.frame = self.buffer.getvalue()
#                 self.condition.notify_all()
#             self.buffer.seek(0)
#         return self.buffer.write(buf)
    
class ClientController(threading.Thread):
    """God object for the Raspberry Pi camera.

    This class controls when the camera is recording and when the server is
    connected.
    """

    def __init__(self,
                 window: 'screen.MainWindow',
                 cageID: str,
                 cageName: str,
                 cameraView: str,
                 cameraID: str,
                 ):
        threading.Thread.__init__(self)
        try:
            with open('siblings', 'r') as siblingsFile:
                self.siblings = set(line.strip() for line in siblingsFile)
        except IOError:
            logger.info('Siblings file not found')
            logger.info('Will create siblings file when siblings are added')
            self.siblings = set()
        # Just "initializing" the private vars so pycharm isn't complaining.
        self._cageName = None
        self._previewing = None
        self._recording = None
        self._expName = None
        self._startTime = None
        self._endTime = None
        self._camNum = None
        self.window = window
        self.cageID = cageID
        self.cageName = cageName
        self.cameraView = cameraView
        self.cameraID = cameraID
        self.server = ServerConnection(self)
        self.camera = picamera.PiCamera()
        self.camera.resolution = (1280, 720)
        self.camera.framerate = 60
        self.resolution = (1280, 720)
        self.camera.zoom = (0.0, 0.0, 1.0, 1.0)
        self.camera.sensor_mode = 6
        self.zoom = (0, 0, 1280, 720)

        
        
        self.compression = 1
        self.previewing = False
        self.recording = False
        self.preview = None
        self.socket = None
        # Create a daemon thread to stream all videos
        self.addressListener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addressListener.bind(('', 8890))
        #self.previewPort = None
#         self.camera = picamera.PiCamera()
#         self.camera.resolution = (1280, 720)
#         self.camera.fps = 60.0
#         self.camera.start_recording('/home/pi/test2.h264')
#         self.camera.wait_recording(5)
#         self.camera.stop_recording()

    @property
    def cageName(self) -> str:
        """The name of the cage this client is connected to.

        When set, the window is updated with the cage name.
        """
        return self._cageName

    @cageName.setter
    def cageName(self, name: str) -> None:
        self._cageName = name
        try:
            self.window.setText("cage", name)
        except AttributeError:
            pass

    @property
    def previewing(self) -> bool:
        """A bool stating whether the client is previewing/streaming to server.

        When set, the window is updated with the previewing status.
        """
        return self._previewing

    @previewing.setter
    def previewing(self, previewing: bool) -> None:
        print("previewing set to {}".format(previewing))
        self._previewing = previewing
        try:
            if previewing:
                self.window.setText("previewing", "Previewing")
            else:
                self.window.setText("previewing", "Not Previewing")
        except AttributeError:
            pass

    @property
    def recording(self) -> bool:
        """A bool stating whether the client is recording.

        When set, the window is updated with the recording status.
        """
        return self._recording

    @recording.setter
    def recording(self, recording: bool) -> None:
        self._recording = recording
        try:
            if recording:
                self.window.setText("recording", "Recording")
                self.window.colorRecording()
            else:
                self.window.setText("recording", "Not Recording")
                self.window.colorNotRecording()
        except AttributeError:
            pass

    @property
    def expName(self) -> str:
        """The name of the experiment currently running.

        When set, the window is updated with the experiment name.
        """
        return self._expName

    @expName.setter
    def expName(self, name: str) -> None:
        self._expName = name
        try:
            self.window.setText("exp name", name)
        except AttributeError:
            pass

    @property
    def startTime(self) -> str:
        """A string time stamp of the start time of the experiment.

        When set, the window is updated with the experiment start time.
        """
        #elf.server.error(self, 'startTime in {}'.format(self._startTime))
        return self._startTime

    @startTime.setter
    def startTime(self, start: str) -> None:
        self._startTime = start
        try:
            self.window.setText("start time", start)
        except AttributeError:
            pass

    @property
    def endTime(self) -> str:
        """A string time stamp of the end time of the experiment.

        When set, the window is updated with the experiment end time.
        """
        #self.server.error(self, 'endTime in {}'.format(self._endTime))
        return self._endTime

    @endTime.setter
    def endTime(self, end: str) -> None:
        self._endTime = end
        try:
            self.window.setText("end time", end)
        except AttributeError:
            pass

    @property
    def camNum(self) -> int:
        """The number of cameras in this experiment.

        When set, the window is updated with the number of connected cameras.
        """
        return self._camNum

    @camNum.setter
    def camNum(self, number: int) -> None:
        self._camNum = number
        try:
            self.window.setText("cam num", str(number))
        except AttributeError:
            pass

    @staticmethod
    def getCurrentEnvironment() -> Dict[str, str]:
        """Creates a dict with relevant environment information.

        The dict contains the home directory of the user under ``HOME``,
        the user name under ``LOGNAME`` and ``USER``, and the path to bash under
        ``PWD``.

        :return: A dict containing some environment information.
        """
        user_name = 'pi'
        pw_record = pwd.getpwnam(user_name)
        user_name = pw_record.pw_name
        user_home_dir = pw_record.pw_dir
        env = os.environ.copy()
        env['HOME'] = user_home_dir
        env['LOGNAME'] = user_name
        env['PWD'] = '/bin/bash'
        env['USER'] = user_name
        return env

    def getStreamPipe(self, previewPort: int) -> subprocess.Popen:
        """Creates a pipe to communicate with a gstreamer subprocess.

        This function starts a gstreamer program using subprocess.Popen and
        connects to its stdin so the pi camera can write to it.

        :param previewPort: The port on the server to write to.
        :return: A pipe with stdin writing to the host at the given address.
        """
#         cmd = 'gst-launch-1.0 -e fdsrc ! h264parse ! '
#         cmd += 'rtph264pay pt=96 config-interval=5 ! udpsink host = '
#         cmd += str(self.server.host)
#         cmd += ' port = '
#         cmd += str(previewPort)
#         env = self.getCurrentEnvironment()
#         pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True, env=env)
#         return pipe
        cmd = 'gst-launch-1.0 -e fdsrc ! h264parse ! '
        cmd += 'rtph264pay pt=96 config-interval=5 ! udpsink host = '
        cmd += str(self.server.host)
        cmd += ' port = '
        cmd += str(previewPort)
        env = self.getCurrentEnvironment()
        #self.server.error(self, 'default buffer size {}'.format(io.DEFAULT_BUFFER_SIZE))
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True, env=env)
        return pipe

    def getFileSock(self, streamPort: int) -> io.BytesIO:
        """Creates a file stream that writes to the server on the given port.

        :param streamPort: The port to connect the stream to.
        :type streamPort: int
        :return: A file stream that writes the server on the given port.
        :rtype: file
        """
        fileStreamSock = socket.socket()
        fileStreamSock.connect((self.server.host, streamPort))
        return fileStreamSock.makefile('wb')

    @staticmethod
    def handshake(handshake: str) -> None:
        """Handles the handshake from the server.

        Currently just prints the handshake.

        :param handshake: The string handshake sent from the server.
        :return: Nothing
        """
        logger.info('Received handshake: {}'.format(handshake))

    @staticmethod
    def poke() -> None:
        """Handles a poke message from the server

        :return: Nothing
        """
        logger.debug('Poke from server.')

    def startRecording(self, _seg_size: int, streamPort: int, serverTime: float) -> None:
        """Start recording and send an acknowledgement to the server.

        If the client is already recording, it will continue recording, but
        output into a new stream.

        :param: _seg_size: Segment size that gets sent, but ignored.
        :param streamPort: The port on the server to stream to.
        :param serverTime: The float representation of when the server requested
            to start recording. Used to make sure any logging is synced with
            server time.
        :return: Nothing
        """
#         self.server.error(self, '_seg_size {}'.format(_seg_size))
#         self.server.error(self, 'severTime {}'.format(serverTime))
#         self.server.error(self, 'sensor_mode {}'.format(self.camera.sensor_mode))
        if not self.recording:
            #self.stopPreviewing(serverTime)
            
            
            splitNotificationTime = time.time()
            offset = splitNotificationTime - serverTime
            fileStream = self.getFileSock(streamPort)
            if self.compression == 1.0: 
                self.camera.start_recording(
                        fileStream,
                        format='h264',
                        splitter_port=1,
                        sps_timing=True,
                )
            elif self.compression > 1.0:
                self.camera.start_recording(
                    fileStream,
                    format='h264',
                    resize = (int(self.camera.resolution[0]/self.compression),
                              int(self.camera.resolution[1]/self.compression)),
                    splitter_port=1,
                )
            else:
                self.server.error(self, 'Error with Compression, self.compression {} < 1.0. Therefore setting self.compression = 1.0'.format(self.compression))
                self.compression = 1.0
                self.camera.start_recording(
                        fileStream,
                        format='h264',
                        splitter_port=1,
                )                
            
            #                     resize =(int(self.camera.resolution[0]/self.compression),
#                              int(self.camera.resolution[1]/self.compression)),
            recordTimestamp = time.time() - offset
            #self.server.error(self, 'started At: {}'.format(recordTimestamp))
            self.server.send(self, 'recording started', recordTimestamp)
            logger.info('Started recording.')
            #self.server.error(self, 'shutter speed: {}'.format(self.camera.exposure_speed))
            self.recording = True
        else:
            splitNotificationTime = time.time()
            fileStream = self.getFileSock(streamPort)
            self.camera.split_recording(fileStream, splitter_port=1)
            offset = splitNotificationTime - serverTime
            recordTimestamp = time.time() - offset
            self.server.send(self, 'recording split', recordTimestamp)
            logger.info('Split recording.')
            self.recording = True

    def stopRecording(self, serverTime: float=0) -> None:
        """Stop recording and send an acknowledgement to the server.

        :param serverTime: The float representation of when the server requested
            to stop recording. Used to make sure any logging is synced with
            server time.
        :return: Nothing
        """
        stopNotificationTime = time.time()
#         self.server.error(self, 'framerate camera {} \n serverTime {} \n stopNotificationTime {}'.format(self.camera.framerate, serverTime, stopNotificationTime))
#         self.server.error(self, 'severTime stop recording{}'.format(serverTime))
#         self.server.error(self, 'self.zoom {}'.format(self.zoom))
#         self.server.error(self, 'self.camera.zoom: {}'.format(self.camera.zoom))
        #self.camera.stop_recording()
        if self.recording:
            try:
                self.camera.stop_recording(splitter_port=1)
                if serverTime:
                    offset = stopNotificationTime - serverTime
                    recordTimestamp = time.time() - offset
                    #self.server.error(self, 'stopped At: {}'.format(recordTimestamp))
                    self.server.send(self, 'recording stopped',
                                     recordTimestamp)
                logger.info('Stopped recording.')
            except Exception as err:
                self.server.error(
                        self, 'Error stopping recording: {}'.format(err))
                self.camera.close()
                self.camera = picamera.PiCamera()
        self.recording = False
        
        
#         if not (self.previewPort is None):
#             self.startPreviewing(self, self.previewPort, serverTime)
#         with picamera.PiCamera() as camera:
#             camera.resolution = (1280, 720)
#             camera.fps = 60.0
#             camera.start_recording('/home/pi/test2.h264')
#             camera.wait_recording(5)
#             camera.stop_recording()
        # self.window.setText("recording", "No")

    def startPreviewing(self, previewPort: int, serverTime: float=0) -> None:
        """Streams the current camera view over a gpac stream to the given port.

        If the camera is already previewing, this function does nothing.

        :param previewPort: The port on the server to stream to.
        :param serverTime: The float representation of when the server requested
            to start previewing. Used to make sure any logging is synced with
            server time.
        :return: Nothing
        """
        #self.previewPort = previewPort

        #return
        if not self.previewing:
            splitNotificationTime = time.time()
            offset = splitNotificationTime - serverTime
            self.preview = self.getStreamPipe(previewPort)
            
            prevsize = (100, 64)
            try:
                self.server.error(self, 'size :{}'.format(len(self.preview.stdin)))
            except Exception:
                self.server.error(self, 'size : no')
            
            if self.camera.resolution == (640, 480): prevsize = (640, 480)
#                 
#             if self.resolution[0] >= 1280 or self.resolution[1] >= 720:
                
            self.camera.start_recording(
                    self.preview.stdin,
                    format='h264',
#                     resize=(int(self.resolution[0]/(self.compression)),
#                             int(self.resolution[1]/(self.compression))),
                    resize=prevsize,
                    splitter_port=2,
                    #bitrate=BITRATE_PREV,
                    quality=10,
                    profile='baseline',
            )
            recordTimestamp = time.time() - offset
            logger.info('Start previewing')
            self.server.error(self, 'compression: {}'.format(self.compression))
            self.server.send(self, 'previewing started', recordTimestamp)
            self.previewing = True


    def stopPreviewing(self, serverTime: float=0) -> None:
        """Stops the client from previewing.

        If the camera is not previewing, this does nothing.

        :param serverTime: The time the server sent the notification.
        :return: Nothing
        """
        #return
        if self.previewing:
            splitNotificationTime = time.time()
            offset = splitNotificationTime - serverTime
            self.camera.stop_recording(splitter_port=2)
            os.kill(self.preview.pid, signal.SIGTERM)
            recordTimestamp = time.time() - offset
            logger.info('Stopped streaming live preview')
            self.server.send(self, 'previewing stopped', recordTimestamp)
            self.previewing = False
            # self.window.setText("previewing", "No")

    def listenForHost(self) -> str:
        """Wait for a notification that a server is up and running.

        The server uses UDP broadcast packets to advertise itself when it
        launches. The Raspberry Pi uses these packets to know when to attempt
        to connect to the server.

        :return: The host that was found.
        """
        while True:
            data, host = self.addressListener.recvfrom(4096)
            host = host[0]
            # Check that the host is valid
            if data.decode() != host or host == '':
                # Invalid host; try again
                continue
            logger.info('Found valid host: {}'.format(host))
            return host

    def purgeUDPSocket(self) -> None:
        """Purge the listen socket, which may have accumulated junk.

       When this process is done, the controller will be ready to
       listenForHost()

       :return: Nothing
       """
        self.addressListener.settimeout(1)
        while True:
            try:
                self.addressListener.recv(1024)
            except socket.timeout:
                self.addressListener.settimeout(None)
                break

    def run(self) -> None:
        """Cleans up then connects to the server.

        Once disconnected, this function also cleans up and starts over again.

        On a keyboard interrupt the function (should) exit.

        :return: Nothing
        """
        try:
            while True:
                # Remove temp files from previous runs
                for f in [file for file in os.listdir('.') 
                          if file.endswith('.h264') or file.endswith('.mp4')]:
                    print('Cleanup: Removing {} from previous run'.format(f))
                    os.remove(f)
                host = self.listenForHost()
                try:
                    self.server.connectToHost(host, 24461)
                    self.server.send(self, 'handshake', ';'.join(
                            ['Camera', VERSION, self.cageID, self.cameraID,
                             self.cameraView, self.cageName]))
                    self.server.interactWithHost(self)
                except (OSError, socket.error) as err:
                    logger.error('Socket error: {}'.format(err))
                    self.server.send(self, 'Socket error: {}'.format(err))
                finally:
                    self.stopPreviewing()
                    self.stopRecording()
                    self.server.close()
                    self.purgeUDPSocket()
        except KeyboardInterrupt:
            return

    def restart(self) -> None:
        """Restart the SCORHE_client2.py Python program."""
        if self.socket:
            self.socket.close()
        if self.addressListener:
            self.addressListener.close()
        if self.camera:
            self.camera.close()
        python = sys.executable
        logger.info('Restarting...')
        time.sleep(1)
        os.execl(python, python, *sys.argv)

    @staticmethod
    def reboot() -> None:
        """Reboot the Raspberry Pi hardware."""
        subprocess.call(['sudo', 'shutdown', '-r', 'now'])

    def saveCameraInfo(self) -> None:
        """Save the cage ID and name, plus the camera view of the camera."""
        f = open('camera_info', 'w')
        f.write(self.cageID + '\n')
        f.write(self.cageName + '\n')
        f.write(self.cameraView + '\n')
        f.close()

    def checkZoom(self) -> None:
        """Checks that the camera zoom is set correctly on the camera.

        Since zoom is applied on the camera after rotation on the pi, and I
        don't want that, I will do some math to apply zoom before rotation.

        :return: Nothing
        """
#         if self.camera.resolution == (1280, 720):
#             self.camera.sensor_mode = 6
        if self.camera.rotation % 180 > 0:
            # still need to flip width/height if we're at 90 deg relative to normal state
            x, y, height, width = self.zoom
        else:
            x, y, width, height = self.zoom
        # want a 4:3 aspect ratio, i.e. width/height = 4/3
        # so we compute the width and height of a 4:3 window
        # (why do we want a 4:3 ratio? because that's the actual camera resolution?)
        w2 = int((height*4)/3)
        h2 = int((width*3)/4)
#         if self.camera.resolution == (1280, 720):
#             w2 = int((height*16)/9)
#             h2 = int((width*9)/16)
        # pick the dimensions that give use the most pixels
        if w2 < width:
            self.resolution = (width, h2)
        elif h2 < height:
            self.resolution = (w2, height)
        elif w2 * height > width * h2:
            self.resolution = (width, h2)
        else:
            self.resolution = (w2, height)
        # find out how many pixels we gained or lost from changing the viewport size
        xdiff = int((width - self.resolution[0])/2)
        ydiff = int((height - self.resolution[1])/2)
        x = self.zoom[0] - xdiff
        y = self.zoom[1] - ydiff

#         # update the camera zoom window
#         self.server.error(self, 'self.camera.resolution in CheckZoom Now {}'.format(self.camera.resolution))
#         self.server.error(self, 'self.resolution in CheckZoom Now {}'.format(self.resolution))        
        camres = self.camera.resolution
        #self.server.error(self, 'camres {}'.format(camres))
        self.camera.zoom = (x / camres[0],
                            y / camres[1],
                            self.resolution[0] / camres[0],
                            self.resolution[1] / camres[1],
                            )
        self.server.error(self, 'camera.zoom {}'.format(self.camera.zoom))

    def setZoomPoints(self, x: int, y: int, width: int, height: int) -> None:
        """ Sets a rectangle on the screen to zoom in and stream from.
            Reduces bandwidth usage and storage """
        if self.camera.resolution != (width, height):
            self.camera.resolution = (width, height)
            if self.camera.resolution == (1280, 720):
                self.camera.sensor_mode = 6
            if self.camera.resolution == (640, 480):
                self.camera.sensor_mode = 0
            camres = self.camera.resolution
            self.camera.zoom = (x/camres[0], y/camres[1], width/camres[0], height/camres[1])
            self.resolution = (width, height)
            self.camera.zoom = (0.0, 0.0, 1.0, 1.0)
            self.zoom = (x, y, width, height)
        #self.server.error(self, 'Set zoom points to {}, {}'.format((x, y), (width, height)))
        #         if not (0 <= x < camres[0]):
        #             raise ValueError('Error setting zoom points: expected x in '
        #                              '[0, 1296), got {}.'.format(x))
        #         if not (0 <= y < camres[1]):
        #             raise ValueError('Error setting zoom points: expected y in '
        #                              '[0, 972), got {}.'.format(x))
        #         if not (0 < width <= camres[0]-x):
        #             raise ValueError('Error setting zoom points: expected width in '
        #                              '(0, 1296-x={}], got {}.'.format(camres[0]-x, width))
        #         if not (0 < height <= camres[1]-y):
        #             raise ValueError('Error setting zoom points: expected height in '
        #                              '(0, 972-y={}], got {}.'.format(camres[1]-y, height))
        #         if not (0.5 < (width / height) < 2):
        #             raise ValueError("Width is too different from height (ratio: {}).\n"
        #                              "Please make them closer. (This is a safeguard "
        #                              "against freezing the pi.) Try ratio between `2` "
        #                              "and `0.5`."
        #                              .format(width/height))
        #         self.zoom = (x, y, width, height)
        #         # might want to compute this in startRecording
        #         #self.checkZoom()
        #         #self.server.error(self, 'camera.zoom  before all this{}'.format(self.camera.zoom))

        
        #self.camera.resolutiion = (500, 720)
        logger.info('Set zoom points to {}, {}'.format((x, y), (width, height)))
        

    def setRotation(self, rotation: int) -> None:
        """Sets the rotation of the image being captured by the camera.

        Rotations can only be multiples of 90, i.e. the view can only be
        rotated by quarter-turns.

        This also updates the width and height of the viewport accordingly. If
        the rotation is not a multiple of 180, then the width and height must
        switch.
        """
        raise ValueError("Rotation is currently unstable and therefore disabled.")
        if rotation % 90 == 0:
            self.camera.rotation = rotation

            self.checkZoom()
            logger.info('Set rotation to {}'.format(rotation))
        else:
            raise ValueError("Error setting rotation: rotation must be a "
                             "multiple of 90, got {}.".format(rotation))

    def setFPS(self, fps: int) -> None:
        """Sets the framerate of the pi camera object.

        This affects the sensor used by the camera and only takes effect after
        the next call to start recording.

        :param fps: The fps to set the camera to.
        :return: Nothing
        """
        try:
            #self.camera.framerate = fractions.Fraction(fps, 1)
            self.camera.framerate = fps
            logger.info('Camera fps: {}'.format(fps))
            self.server.error(self, 'framerate camera {}'.format(self.camera.framerate))
            #self.server.error(self, 'framerate camera {}'.format(self.camera.framerate))
        except Exception as err:
            self.server.error(
                    self, 'Unable to set frame rate of camera to {}: {}'.format(
                            fps, err))
#             try:
#                 self.stopPreviewing(time.time())
#                 self.camera.framerate = fractions.Fraction(fps)
#                 self.startPreviewing(time.time())
#             except Exception as err:
#                 self.server.error(self, 'Unable to set frame rate to {}, even after fix attempt. ERROR: {}'.format(fps,err))

    def setStreamFormat(self, streamFormat: str) -> None:
        """Sets the format for the stream.

        If the client is recording, then an error is reported to the server.

        Currently, the format is ignored, and the stream is only in h264.

        :param streamFormat: A string representation of the format for the
            stream, e.g. 'h264', 'mp4', etc.
        :return: Nothing
        """

        if self.recording:
            self.server.error(self, 'Cannot set format while recording')
        else:
            # self.streamFormat = streamFormat
            logger.info('Stream format: {}'.format(streamFormat))

    def setVflip(self, vflip: bool) -> None:
        """Sets whether the camera's image should be flipped vertically.

        :param vflip: Whether the camera's image should be flipped vertically.
        :return: Nothing
        """
        self.camera.vflip = vflip
        # self.window.setText("vflip", vflip)

    def setColorMode(self, color: bool) -> None:
        """Sets whether the camera should record in color or grayscale.

        This can be set while recording.

        :param color: Whether to record in color or not.
        :return: Nothing
        """
        if color:
            self.camera.color_effects = None
            logger.info('Set color mode to color')
        else:
            self.camera.color_effects = (128, 128)
            logger.info('Set color mode to monochrome')

    def setView(self, view: str) -> None:
        """Sets the view associated with the current client object.

        The "view" is just an identifier to distinguish cameras and their
        recordings from each other when they view the same cage, in a system
        with multiple cameras per cage.

        For example, if a cage setup has a central camera to view most of the
        cage, and a secondary camera to capture the less important parts of the
        cage, The former might be called "center" or "main" and the latter
        might be called "edge" or "front" (if it is toward the front of the
        cage). So every cage with this setup can be analyzed correctly, where
        the recordings are both associated with each other and analyzed by the
        correct program.

        :param view: The name of the "view" that this camera can see.
        :return: Nothing
        """
        self.cameraView = view
        self.saveCameraInfo()
        logger.info('Set view to "{}"'.format(view))

    def setAutogain(self, autogain: bool) -> None:
        """Sets whether the camera will use autogain or not.

        See the documentation on awb_mode on the picamera for more detail
        (``True`` sets it to ``auto`` and ``False`` sets it to ``off``).

        :param autogain: Whether to enable autogain or not.
        :return: Nothing
        """
        self.camera.awb_mode = 'auto' if autogain else 'off'
        logger.info('Set awb_gains to {}'.format(self.camera.awb_mode))

    def setGain(self, gain: float) -> None:
        """Sets the gain for the camera.

        See the documentation on awb_gain on the picamera for more detail.
        :param gain: The gain value for the camera.
        :rtype: None
        """
        self.camera.awb_gains = gain
        logger.info('Set gain to {}'.format(gain))

    def setShutterSpeed(self, shutterSpeed: int) -> None:
        """Sets the speed at which the shutter closes for the camera.

        :param shutterSpeed: The speed of the shutter, in microseconds.
        :return: Nothing
        """
        self.server.error(self, 'shutterspeed {}'.format(shutterSpeed))
        self.camera.shutter_speed = shutterSpeed
        logger.info('Set shutter speed to {}'.format(shutterSpeed))

    def setISO(self, iso: int) -> None:
        """Sets the ISO for the camera.

        ISO is related to the camera's sensitivity to light, where a higher
        value is associated with higher sensitivity.

        :param iso: The ISO for the camera.
        :return: Nothing
        """
        self.camera.iso = iso
        logger.info('Set ISO to {}'.format(iso))

    def setBrightness(self, brightness: int) -> None:
        """Sets the brightness of the camera's images.

        :param brightness: The brightness of the image.
        :return: Nothing
        """
        self.camera.brightness = brightness
        logger.info('Set brightness to {}'.format(brightness))

    def syncClocks(self, year: int, month: str, day: int, hour: int,
                   minute: int, second: int, hostTime: float) -> None:
        localTime = time.time()
        cmd = shlex.split('sudo date --set "{} {} {} {}:{}:{}"'.format(
                day, month, year, hour, minute, second))
        process = subprocess.Popen(cmd)
        process.wait()
        logger.info('Set system time: {}'.format(time.strftime('%M-%d-%Y %h:%m:%s')))
        logger.info('Clock offset: {}'.format(localTime - hostTime))

    def bundle(self, cageName: str, cageID: str) -> None:
        """Sets the cage this camera is located in.

        This is only used for display on the client side.

        :param cageName: The name of the cage this camera is in.
        :param cageID: The unique ID of the cage this camera is in.
        :return: Nothing
        """
        self.cageName = cageName
        self.cageID = cageID
        self.saveCameraInfo()

        logger.info('Set cage to {}, ID: {}'.format(cageName, cageID))

    def setCompression(self, compression: float) -> None:
        """Sets the compression factor for the camera.

        This is used to shrink the sides of the image by the given factor.
        Thus, the compression of the image is actually compression^2

        :param compression: The factor by which to compress the sides of the
            image.
        :return: Nothing
        """

        if compression >= 1:
            self.compression = compression
            logger.info('Set compression factor to {}'.format(compression))
        else:
            raise ValueError(
                    'Error setting compression: '
                    'compression must be >= 1, got {}.'.format(compression))

    def sibling(self, siblingAddress: str) -> None:
        if siblingAddress not in self.siblings:
            self.siblings.add(siblingAddress)
            with open('siblings', 'a+') as file:
                file.write(siblingAddress + '\n')

    def setCamMap(self, camName: str) -> None:
        if " " in camName:
            camName = camName.rsplit(" ", 1)[0]
        self.cageName = camName
        logger.info('Set camera name to {}.'.format(camName))

    def sendExp(self,
                expName: str,
                startTime: str,
                endTime: str,
                numClients: int,
                ) -> None:
        self.expName = expName
        self.startTime = startTime
        self.endTime = endTime
        self.camNum = numClients
        logger.info('Set experiment {} with start {}, end {}, and {} cameras.'.
                    format(expName, startTime, endTime, numClients))


class ServerConnection:
    """An object representing a connection to the server."""

    def __init__(self, client: ClientController):
        self.socket = None
        self.host = None
        self.protocol = clientProtocol(self, client)
        self.buffer = b''

    def connectToHost(self, host: str, port: int) -> None:
        """Connects to the given host IP address at the given port number."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logger.info('Trying to connect to {}:{}...'.format(host, port))
        self.socket.connect((host, port))
        logger.info('Connected to {}:{}'.format(host, port))
        self.host = host

    def interactWithHost(self, client: ClientController) -> None:
        """Runs in a loop, receiving and responding to messages."""
        while self.socket:
            try:
                ready = select.select([self.socket], [], [], 120)
                if ready[0]:
                    buffer = self.socket.recv(1024)
                    # print(buffer)
                else:
                    raise Exception(
                            'Connection timed out: no pokes in 120 seconds')
            except socket.error:
                logger.info('Disconnected from server')
                self.socket.close()
                return
            except Exception as err:  # Internal logic exception
                self.error(client, '{}'.format(err))
                return
            try:
                self.handle(buffer)
            except ValueError as err:
                self.error(client, '{}'.format(err))

    def send(self, client: ClientController, messageID: str, *args) -> None:
        """Send a message to the server."""
        self.socket.sendall(
                self.protocol.buildMessage(messageID, self, client, *args))

    def handle(self, buffer: bytes) -> None:
        """Handle a buffer containing messages from the server.

        The buffer may include partial messages or more than one message.
        """
        self.buffer += buffer
        self.buffer = self.protocol.handleBuffer(self.buffer)

    def error(self, client: ClientController, message: str) -> None:
        """Print an error message and try to report the error to the server."""
        logger.error('ERROR: {}'.format(message))
        traceback.print_tb(sys.exc_info()[2])
        try:
            self.send(client, 'error', message)
        except socket.error:
            # Some errors will be because the socket itself is closed, in which
            # case we ignore that we couldn't send an error message. Just check
            # the console output
            pass

    def close(self) -> None:
        """Close the connection to the server."""
        if self.socket:
            self.socket.close()
            self.socket = None


def clientProtocol(server: ServerConnection,
                   client: ClientController,
                   ) -> protocol.Protocol:
    """A protocol that handles messages to and from the camera.
    See protocol.py for details on how SCORHE protocols work.
    """
    taskQueue = protocol.EventProtocol()
    thread = threading.Thread(target=taskQueue.start)
    thread.daemon = True
    thread.start()

    i = protocol.MessageHandler(taskQueue, client, server)
    i.assertHandler('handshake', 'S', client.handshake)
    i.assertHandler('poke', '', client.poke)
    i.assertHandler('start recording', 'iid', client.startRecording)
    i.assertHandler('stop recording', 'd', client.stopRecording)
    i.assertHandler('start previewing', 'id', client.startPreviewing)
    i.assertHandler('stop previewing', 'd', client.stopPreviewing)
    i.assertHandler('set FPS', 'i', client.setFPS)
    i.assertHandler('set stream format', 'S', client.setStreamFormat)
    i.assertHandler('set vflip', '?', client.setVflip)
    i.assertHandler('set color mode', '?', client.setColorMode)
    i.assertHandler('set view', 'S', client.setView)
    i.assertHandler('set autogain', '?', client.setAutogain)
    i.assertHandler('set gain', 'd', client.setGain)
    i.assertHandler('set shutter speed', 'i', client.setShutterSpeed)
    i.assertHandler('set ISO', 'i', client.setISO)
    i.assertHandler('set brightness', 'i', client.setBrightness)
    i.assertHandler('sync clocks', 'iSiiiid', client.syncClocks)
    i.assertHandler('bundle', 'SS', client.bundle)
    i.assertHandler('restart', '', client.restart)
    i.assertHandler('reboot', '', client.reboot)
    i.assertHandler('sibling', 'S', client.sibling)
    i.assertHandler('send exp', 'SSSi', client.sendExp)
    i.assertHandler('set zoom points', 'iiii', client.setZoomPoints)
    i.assertHandler('set rotation', 'i', client.setRotation)
    i.assertHandler('set camMap', 'S', client.setCamMap)
    i.assertHandler('set compression', 'd', client.setCompression)

    def buildMessage(_server: ServerConnection,
                     _client: ClientController,
                     *args: Union[str, int, float, bool]
                     ) -> Tuple[Union[str, int, float, bool], ...]:
        """Build a message form its arguments.

        Discards the first two arguments as they are always ``server`` and
        ``client`` and are useless as this generator is always stateless.

        :param _server: The server to which the message will be sent. Ignored.
        :param _client: The server to which the message will be sent. Ignored.
        :param args: The arguments to make the tuple from.
        :return: A tuple of the given arguments, except the first two.
        """
        return tuple(args)

    o = protocol.MessageBuilder()
    o.addRule('handshake', 'S', buildMessage)
    o.addRule('error', 'S', buildMessage)
    o.addRule('message', 'S', buildMessage)
    o.addRule('poke', '', buildMessage)
    o.addRule('recording started', 'd', buildMessage)
    o.addRule('recording split', 'd', buildMessage)
    o.addRule('recording stopped', 'd', buildMessage)
    o.addRule('previewing started', 'd', buildMessage)
    o.addRule('previewing stopped', 'd', buildMessage)
    o.addRule('data', 'Sd', buildMessage)
    return protocol.Protocol(i, o)


def getCameraInfo() -> Tuple[str, str, str]:
    """Open the camera_info file, or load the defaults if it doesn't exist.

    :return: A tuple of the camera's cage ID, name and the camera's view.
    """
    cageID = '??Unknown??'
    cageName = '??Unknown??'
    cameraView = '??Unknown??'
    try:
        f = open('camera_info', 'r')
        cageID = f.readline().strip()
        cageName = f.readline().strip()
        cameraView = f.readline().strip()
    except (IOError, FileNotFoundError):
        pass
    return cageID, cageName, cameraView


def getCameraID() -> str:
    """The camera ID is the truncated MAC address.

    The first two bytes of the MAC address are the same for all Raspberry Pis,
    so we don't need them in the ID. The remaining bytes are sufficient to
    create a unique identifier for the camera.

    :return: The ID for camera based on the MAC address of the pi.
    """
    mac = open('/sys/class/net/eth0/address').read()
    return mac[8:].replace(":", "").rstrip()


def main() -> None:
    """The main function that starts the client and sets up the UI.

    :return: Nothing
    """
    try:
        app = QtWidgets.QApplication([])
        window = screen.MainWindow()
    except AttributeError:
        app = None
        window = None

    cameraInfo = getCameraInfo()
    cameraInfo += getCameraID(),
    logger.info(cameraInfo[3])  # cameraID
    logger.info('Cage: {} (ID {})'.format(cameraInfo[1], cameraInfo[0]))
    logger.info('View: {}'.format(cameraInfo[2]))
    client = ClientController(window, *cameraInfo)
    try:
        window.showFullScreen()
    except AttributeError:
        pass
    try:
        client.start()
    finally:
        try:
            app.exec_()
        except AttributeError:
            pass
        client.join()
