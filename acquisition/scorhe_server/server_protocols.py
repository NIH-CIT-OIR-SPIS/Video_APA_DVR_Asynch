"""Defines protocols for the server.py

The protocols each have a MessageHandler (for incoming messages) and a
MessageBuilder (for outgoing messages). Each associates message IDs with a
function that responds to or constructs messages, respectively.
"""

import logging
import os
import paramiko
import socket
import threading
import time
import utils
import shutil
from typing import Tuple
import platform
import scorhe_server  # for type hinting :/
from scorhe_server import protocol
import utils

logger = logging.getLogger(__name__)


StartTime = 0
def buildHandshakeMessage(_server: 'scorhe_server.server.CameraServer',
                          _client: 'scorhe_server.server.CameraClient',
                          ) -> Tuple[str]:
    """Constructs a 1-tuple of the address of the server.

    This is the same for all protocols.

    We may want to make this more secure with a better validation method than
    checking against the hostname...

    :param _server: The server object performing the handshake. Ignored.
    :param _client: The client object performing the handshake. Ignored.
    :return: A 1-tuple of str, containing the hostname of the current computer.
    """
    return (socket.gethostname(),)


def UnregisteredProtocol() -> protocol.Protocol:
    """Factory method for a protocol for clients whose type is not yet known.

    :return: A protocol object that handles communication with unregistered
        clients, polling on a separate thread.
    """
    taskQueue = protocol.AsyncFunctionQueue()
    thread = threading.Thread(target=taskQueue.start)
    thread.daemon = True
    thread.start()

    def handleHandshakeMessage(server: 'scorhe_server.server.CameraServer',
                               client: 'scorhe_server.server.CameraClient',
                               handshake: str,
                               ) -> None:
        """Handles the handshake message from the client.

        The handshake includes the version of the client. If the client is out
        of date and the server is set to push updates, this function will also
        open an ftp connection to the client and upload the updated code to it.
        Currently does not update the python version.

        :param server: The server handling the message and registration of the
            client.
        :param client: The client that is performing the handshake
        :param handshake: The handshake message.
        :return: Nothing
        """
        message = handshake.split(';')
        if server.options.clientVersion is not None and \
                (len(message) < 6 or message[1] < server.options.clientVersion) \
                and server.options.pushUpdates:
            # client is out of date. let's fix that by copying over the current
            # version of the client code.
            def update_client(ip, clientFolder, socket: socket.socket, logger: logging.Logger):
                s = None  # type: paramiko.SSHClient
                install_dir = '/tmp/scorhe-install/'
                logger.info('Updating client {}...'.format(ip))
                start = time.time()
                try:
                    s = paramiko.SSHClient()
                    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    s.connect(ip,
                              port=22,
                              username='pi',
                              password='raspberry',
                              )
                    s.exec_command('sudo pkill python')
                    sftp = s.open_sftp()  # type: paramiko.SFTPClient
                    transport = {
                        'protocol.py', 'client.py',
                        'screen.py', '__main__.py',
                    }
                    try:
                        sftp.mkdir(install_dir)
                    except Exception as e:
                        print("Somethings Wrong 98")
                        pass
                    try:
                        sftp.mkdir(install_dir + 'source')
                    except Exception as a:
                        print("Somethings Wrong 103")
                        pass
                    
                    for file in transport:
                        src = os.path.join(clientFolder, 'source', file)
                        dest = install_dir + 'source/' + file
                        with sftp.open(dest, 'wU') as dest_file, open(src, 'rU') as src_file:
                            for line in src_file:
                                dest_file.write(line)
                    logger.debug('Updated source on {}'.format(ip))
                    # copy and run the install script to make sure everything is good
                    updates = ['needs-sudo.sh',
                               'needs-pi.sh',
                               # 'PyQt5_gpl-5.11.2.tar.gz',
                               # 'sip-4.19.12.tar.gz',
                               # 'Python-3.6.5.tgz',
                               # 'picamera-1.13.tar.gz',
                               ]
                    push = True
                    for file in updates:
                        push = push and os.path.exists(os.path.join(clientFolder, file))
                    if push:
                        for file in updates:
                            if file.rsplit('.', 1)[1] in ['sh']:
                                src = os.path.join(clientFolder, file)
                                dest = install_dir + file
                                with sftp.open(dest, 'wU') as dest_file, open(src, 'rU') as src_file:
                                    for line in src_file:
                                        dest_file.write(line)
                            else:
                                sftp.put(os.path.join(clientFolder, file),
                                         install_dir + file)
                        # running this could take upwards of 20 minutes. but it's ok,
                        # because this is running on a thread just for this client
                        logger.debug('Running install...')
                        s.exec_command('chmod +x {}needs-pi.sh'.format(install_dir))
                        s.exec_command('chmod +x {}needs-sudo.sh'.format(install_dir))
                        _, out, err = s.exec_command('sudo {}needs-sudo.sh'.format(install_dir))
                        for line in out:
                            logger.debug('{}'.format(line[:-1]))
                        errlines = err.readlines()
                        if errlines:
                            logger.error('Error updating {}: {}'.format(ip, ''.join(errlines)))
                        _, out, err = s.exec_command('{}needs-pi.sh'.format(install_dir))
                        for line in out:
                            logger.debug('{}'.format(line[:-1]))
                        errlines = err.readlines()
                        if errlines:
                            logger.error('Error updating {}: {}'.format(ip, ''.join(errlines)))
                        logger.debug('Finished install script on {}'.format(ip))
                        s.exec_command('sudo shutdown -r now')
                    else:
                        logger.error('Missing update files. Make sure you have '
                                     'python3.6.5 source, PyQt5 5.10.1 wheel, '
                                     'and picamera 1.13 package source in the '
                                     'client folder.')
                    # _, _, err = s.exec_command('sudo /sbin/reboot')
                    # errlines = err.readlines()
                    # if errlines:
                    #     logger.error('Error updating {}: {}'.format(ip, errlines))
                    s.close()
                except (EOFError, paramiko.ssh_exception.SSHException, IOError):
                    pass
                finally:
                    if s:
                        s.close()
                    diff = time.time() - start
                    m, s = ((int(diff // 60)), diff % 60)
                    logger.info('Finished updating client {} in {}m{}s'.format(ip, m, s))
                    socket.close()

            t1 = threading.Thread(target=update_client,
                                  args=(client.socket.getpeername()[0],
                                        server.clientFolder,
                                        client.socket,
                                        logger)
                                  )
            # server.clients.unregister(client.socket, 'Unregistered')
            t1.start()

        else:
            server.clients.unregister(client.socket, 'Unregistered')
            server.clients.register(server, client.socket, *message)

    def handleErrorMessage(server: 'scorhe_server.server.CameraServer',
                           client: 'scorhe_server.server.CameraClient',
                           message: str,
                           ) -> None:
        """Prints the error message and client camera id for a given error message

        :param server: Sever object receiving the error.
        :param client: The client that sent the error message.
        :param message: The error message.
        :return: Nothing
        """
        server.error(client, 'unregistered client error: ' + message)

    i = protocol.MessageHandler(taskQueue)
    i.addRule('handshake', 'S', handleHandshakeMessage)
    i.addRule('error', 'S', handleErrorMessage)

    o = protocol.MessageBuilder()
    o.addRule('handshake', 'S', buildHandshakeMessage)
    o.addRule('reboot')

    return protocol.Protocol(i, o)


def CameraProtocol() -> protocol.Protocol:
    """A factory function for protocols for camera clients.

    Cameras can send messages reporting the exact moment in time that recording
    of video started, split, or finished. A server can instruct a camera to
    configure various properties, such as framerate, resolution, and cage ID.

    :return: A protocol object communicating with a camera client, polling on a
        separate thread.
    """
    taskQueue = protocol.AsyncFunctionQueue()
    thread = threading.Thread(target=taskQueue.start)
    thread.daemon = True
    thread.start()

    def handleErrorMessage(server: 'scorhe_server.server.CameraServer',
                           client: 'scorhe_server.server.CameraClient',
                           message: str
                           ) -> None:
        """Prints the error message the client sent.

        :param server: The server object used to print the error.
        :param client: The client that sent the error message.
        :param message: The error message.
        :return: Nothing
        """
        #server.handlePreviewingError(client, message)
        server.error(client, message)

    def handleRecordingStartedMessage(_server: 'scorhe_server.server.CameraServer',
                                      client: 'scorhe_server.server.CameraClient',
                                      startTime: float,
                                      ) -> None:
        """Prints the time the client received the started recording message.

        :param _server: The server with which the client is communicating.
            Ignored.
        :param client: The client that sent the message that it started
            recording.
        :param startTime: The timestamp the client started recording.
        :return: Nothing
        """
        logger.info('camera recording started ' + str(client.cameraID) +
                    str(utils.convertTimestamp(startTime)))

    def handleRecordingSplitMessage(_server: 'scorhe_server.server.CameraServer',
                                    client: 'scorhe_server.server.CameraClient',
                                    splitTime: float,
                                    ) -> None:
        """Prints the time the client received the split recording message

        :param _server: The server with which the client is communicating.
            Ignored.
        :param client: The client that sent the message that it split recording.
        :param splitTime: The timestamp the client split recording.
        :return: Nothing
        """
        client.timestamps.put(splitTime)
        logger.info('camera recording split ' + str(client.cameraID) +
                    str(utils.convertTimestamp(splitTime)))

    def handleRecordingStoppedMessage(_server: 'scorhe_server.server.CameraServer',
                                      client: 'scorhe_server.server.CameraClient',
                                      stopTime: float,
                                      ) -> None:
        """Prints the time the client received the stopped recording message.

        :param _server: The server with which the client is communicating.
            Ignored.
        :param client: The client that sent the message that it stopped
            recording.
        :param stopTime: The timestamp the client stopped recording.
        :return: Nothing
        """
        client.timestamps.put(stopTime)
        logger.info('camera recording stopped ' + str(client.cameraID) +
                    str(utils.convertTimestamp(stopTime)))

    def handlePreviewingStartedMessage(_server: 'scorhe_server.server.CameraServer',
                                       client: 'scorhe_server.server.CameraClient',
                                       startTime: float,
                                       ) -> None:
        """Prints the time the client received the start previewing message.

        :param _server: Unused, required as part of the signature of a message
            handler.
        :param client: The client that sent the message that it started
            previewing.
        :param startTime: The timestamp the client started previewing.
        :return: Nothing
        """
        logger.info('camera previewing started ' + str(client.cameraID) +
                    str(utils.convertTimestamp(startTime)))

    def handlePreviewingStoppedMessage(_server: 'scorhe_server.server.CameraServer',
                                       client: 'scorhe_server.server.CameraClient',
                                       stopTime: float,
                                       ) -> None:
        """Prints the time a client received the stop previewing message.

        :param _server: Unused, required as part of the signature of a message
            handler.
        :param client: The client that sent the message that it stopped
            previewing.
        :param stopTime: The timestamp the client stopped previewing.
        :return: Nothing
        """
        client.timestamps.put(stopTime)
        logger.info('camera previewing stopped ' + str(client.cameraID) +
                    str(utils.convertTimestamp(stopTime)))

    def handleMessageMessage(_server: 'scorhe_server.server.CameraServer',
                             _client: 'scorhe_server.server.CameraClient',
                             message: str,
                             ) -> None:
        """Prints the message sent from a client connected to this server.

        :param _server: Unused, required as part of the signature of a message
            handler.
        :param _client: Unused, required as part of the signature of a message
            handler.
        :param message: A str message.
        :return: Nothing
        """
        logger.info(message)

    def handleDataMessage(server: 'scorhe_server.server.CameraServer',
                          client: 'scorhe_server.server.CameraClient',
                          datatype: str, data: float
                          ) -> None:
        """Handles any discrete data sent from the pis.

        Gets data from the pi (perhaps from environmental sensors) and logs them
        to a file, perhaps in the future uploading to the cloud.

        :param server: The server recording the message.
        :param client: The client emitting the message.
        :param datatype: A string description of the data.
        :param data: The data as a float.
        :return: Nothing
        """
        server.storeData(client, datatype, data)

    i = protocol.MessageHandler(taskQueue)
    i.addRule('error', 'S', handleErrorMessage)
    i.addRule('message', 'S', handleMessageMessage)
    i.addRule('poke')
    i.addRule('recording started', 'd', handleRecordingStartedMessage)
    i.addRule('recording split', 'd', handleRecordingSplitMessage)
    i.addRule('recording stopped', 'd', handleRecordingStoppedMessage)
    i.addRule('previewing started', 'd', handlePreviewingStartedMessage)
    i.addRule('previewing stopped', 'd', handlePreviewingStoppedMessage)
    i.addRule('data', 'Sd', handleDataMessage)



    def buildStartRecordingMessage(server: 'scorhe_server.server.CameraServer',
                                   client: 'scorhe_server.server.CameraClient',
                                   timeString: str,
                                   ) -> Tuple[int, int, float]:
        """Constructs a 3-tuple of the recording details for the camera.

        The details are the segment size (in seconds), the port to stream over,
        and the time the recording should start (current time).

        The client object is also prepped to record the video to a file.

        :param server: The server object with the relevant settings.
        :param client: The client object to prep for recording.
        :param timeString: The time string to identify the file.
        :return: A 3-tuple of the recording details: segment size, port and
            start time.
        """
        cameraID = client.cameraID
        width, height = server.clientOptions.zoomDimension
        try:
            cameraID = server.clientOptions.camMap[cameraID]
        except KeyError:
            pass
        #print("The Base direcotyr %s" % server.options.baseDirectory)

        if not server.options.baseDirectory:
            
            path = os.path.join(utils.APPDATA_DIR, "experiments", "")
            count = 0
            remove_path = ""
            if (not os.path.exists(path)) or len(os.listdir(path)) == 0:
                server.options.baseDirectory = os.path.join(utils.APPDATA_DIR, "experiments", "Untitled", "")
                if not os.path.exists(server.options.baseDirectory):
                    os.makedirs(server.options.baseDirectory)
            else:
                for i in os.listdir(path):
                    server.options.baseDirectory = os.path.join(path + "Untitled" + str(count), "")
                    if count == 60:
                        server.options.baseDirectory = os.path.join(path + "Untitled" + str(count - 1), "")
                        shutil.rmtree(server.options.baseDirectory)
                        os.makedirs(server.options.baseDirectory)
                        print("Max number of Untitled directories exist in path {}, deleting all experiments in experiment folder".format(path))
                        break
                    if not os.path.exists(server.options.baseDirectory):
                        os.makedirs(server.options.baseDirectory)
                        break
                    else:
                        count += 1

                if count == 60:
                    shutil.rmtree(path)
                    #print(textWord)
                    server.options.baseDirectory = os.path.join(utils.APPDATA_DIR, "experiments", "Untitled", "")
                    if not os.path.exists(server.options.baseDirectory):
                        os.makedirs(server.options.baseDirectory)
            
            #if remove_path:
            #    text_word = str(input("You have reached the max number of untitled experiments. \n If you wish to add more all past Untitled experiments will be deleted. Is this okay? [Y/N]: "))
            #    while text_word != 'y' or text_word != 'Y' or text_word != 'n' or text_word != 'N':
            #        text_word = str(input("Please input a valid character [Y/N]: "))
            #    if text_word == 'y' or text_word == 'Y':
            #        server.options.baseDirectory = os.path.join(utils.APPDATA_DIR, "experiments", "Untitled", "")
            #        if not os.path.exists(server.options.baseDirectory):
            #            os.makedirs(server.options.baseDirectory)
            #    else:
            #        server.options.baseDirectory = ''
            #    remove_path = ""

        filename = '{}/{} {}.{}'.format(server.options.baseDirectory,
                                       timeString, cameraID,
                                       server.options.format)
        port = client.streamVideoToFile(filename, width, height)
        #client.
        recordStartTime = time.time()
        global StartTime 
        StartTime = recordStartTime
        print("recordStartTime %s" % recordStartTime)
        print("timestr %s" % timeString)
        return (server.options.segmentSize, port, recordStartTime)

    def buildStopRecordingMessage(_server: 'scorhe_server.server.CameraServer',
                                  _client: 'scorhe_server.server.CameraClient',
                                  ) -> Tuple[float]:
        """Constructs a 1-tuple of the current time.

        This is used to communicate when the message was sent for the benefit of
        the camera to know when it was told to stop recording.

        :param _server: Unused, required as part of the signature of a message
            builder.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of float containing the current time in seconds
        """
        print("endTime %s" % time.time())
        other = float(time.time())-float(StartTime)
        print(other)
        return (time.time(),)

    def buildStartPreviewingMessage(_server: 'scorhe_server.server.CameraServer',
                                    client: 'scorhe_server.server.CameraClient',
                                    ) -> Tuple[int, float]:
        """Constructs a 2-tuple of the preview port and the current time.

        This is used to communicate when the message to start previewing was
        sent and to communicate what port is open for this preview.

        :param _server:Unused, required as part of the signature of a message
            builder.
        :param client: The client that dictates the port to communicate on.
        :return: A 2-tuple of int, float with port and current time in seconds
        """
        previewPort = client.getFreeSocket().getsockname()[1]
        previewStartTime = time.time()
        return (previewPort, previewStartTime)

    def buildStopPreviewingMessage(_server: 'scorhe_server.server.CameraServer',
                                   _client: 'scorhe_server.server.CameraClient',
                                   ) -> Tuple[float]:
        """Constructs a 1-tuple of the current time.

        This is used to communicate when the message was sent for the benefit of
        the camera to know when it was told to stop previewing.

        :param _server: Unused, required as part of the signature of a message
            builder.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of float containing the current time in seconds
        """
        return (time.time(),)

    def buildSetFPSMessage(server: 'scorhe_server.server.CameraServer',
                           _client: 'scorhe_server.server.CameraClient',
                           ) -> Tuple[int]:
        """Constructs a 1-tuple of the FPS the camera is expected to output.

        :param server: The server where fps is stored
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of int representing the expected fps of the cameras
        """
        return (server.clientOptions.fps,)


    def buildSetDimensionMessage(server: 'scorhe_server.server.CameraServer',
                                 _client: 'scorhe_server.server.CameraClient',
                                 ) -> Tuple[int, int]:
        """Constructs a 2-tuple of of to send the width and height of the capture.

        This method is deprecated in favor of setZoomPoints.

        :param server: The server where capture width and height are set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 2-tuple of int, int
        """
        return server.clientOptions.zoomDimension

    def buildSetStreamFormatMessage(server: 'scorhe_server.server.CameraServer',
                                    _client: 'scorhe_server.server.CameraClient',
                                    ) -> Tuple[str]:
        """Constructs a 1-tuple of the output format for the picamera.

        Currently, this does nothing on the client side, as the output is
        currently only h264.

        :param server: The server where format was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of str for format of the camera.
        """
        return (server.options.format,)

    def buildSetVFlipMessage(server: 'scorhe_server.server.CameraServer',
                             client: 'scorhe_server.server.CameraClient',
                             ) -> Tuple[bool]:
        """Constructs a 1-tuple for whether the camera should be flipped vertically.

        :param server: The server where autogain was set.
        :param client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of bool dictating the flip of the camera.
        """
        return (server.clientOptions.vflip[client.cameraID],)

    def buildSetColorModeMessage(server: 'scorhe_server.server.CameraServer',
                                 _client: 'scorhe_server.server.CameraClient',
                                 ) -> Tuple[bool]:
        """Constructs a 1-tuple for whether the Pi cameras records in color.

        ``True`` for color, ``False`` for grayscale.

        :param server: The server where color mode was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of bool for color mode of the camera.
        """
        return (server.clientOptions.colorMode,)

    def buildSetViewMessage(_server: 'scorhe_server.server.CameraServer',
                            client: 'scorhe_server.server.CameraClient',
                            ) -> Tuple[str]:
        """Constructs a 1-tuple with the view that the camera is looking at.

        Usually this would be something like "front" or "back" for cameras in a
        cage.

        :param _server: Unused, required as part of the signature of a message
            builder.
        :param client: The client object where the view is stored for the camera
        :return: A 1-tuple of str for the view of the camera.
        """
        return (client.cameraView,)

    def buildSetAutogainMessage(server: 'scorhe_server.server.CameraServer',
                                _client: 'scorhe_server.server.CameraClient',
                                ) -> Tuple[bool]:
        """Constructs a 1-tuple for whether autogain is on for the Pi cameras.

        :param server: The server where autogain was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of bool for autogain of the camera.
        """
        return (server.clientOptions.autogain,)

    def buildSetGainMessage(server: 'scorhe_server.server.CameraServer',
                            _client: 'scorhe_server.server.CameraClient',
                            ) -> Tuple[float]:
        """Constructs a 1-tuple with the gain for the Pi cameras.

        :param server: The server where gain was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of float for gain of the camera.
        """
        return (server.clientOptions.gain,)

    def buildSetShutterSpeedMessage(_server: 'scorhe_server.server.CameraServer',
                                    _client: 'scorhe_server.server.CameraClient',
                                    ) -> Tuple[int]:
        """Constructs a 1-tuple with the shutter speed for the Pi cameras.

        :param _server: The server where shutter speed was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of int for shutter speed of the camera.
        """
        return (_server.clientOptions.shutterspeed,)

    def buildSetISOMessage(server: 'scorhe_server.server.CameraServer',
                           _client: 'scorhe_server.server.CameraClient',
                           ) -> Tuple[int]:
        """Constructs a 1-tuple with the ISO for the Pi cameras.

        :param server: The server where ISO was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of int for ISO of the camera.
        """
        return (server.clientOptions.iso,)

    def buildSetBrightnessMessage(server: 'scorhe_server.server.CameraServer',
                                  _client: 'scorhe_server.server.CameraClient',
                                  ) -> Tuple[int]:
        """Constructs a 1-tuple with the brightness for the Pi cameras.

        :param server: The server where brightness was set.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 1-tuple of int for brightness of the camera.
        """
        return (server.clientOptions.brightness,)

    ##contraster$
    def buildSetContrastMessage(server: 'scorhe_server.server.CameraServer',
                                _client: 'scorhe_server.server.CameraClient',) -> Tuple[int]:
        return (server.clientOptions.contrast,)

    def buildClockSyncMessage(_server: 'scorhe_server.server.CameraServer',
                              _client: 'scorhe_server.server.CameraClient',
                              ) -> Tuple[int, str, int, int, int, int, float]:
        """Constructs a 7-tuple of the current time, to millisecond precision.

        :param _server: Unused, required as part of the signature of a message
            builder.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :return: A 7-tuple of the current year, month, day of the month, hour,
            minute, second and full, sub-millisecond precision, float time.
        """
        t = time.localtime()
        m = time.time()
        return (t.tm_year, time.strftime('%b', t), t.tm_mday, t.tm_hour,
                t.tm_min, t.tm_sec, m)

    def buildBundleMessage(_server: 'scorhe_server.server.CameraServer',
                           client: 'scorhe_server.server.CameraClient',
                           ) -> Tuple[str, str]:
        """Constructs a 2-tuple containing the given client's cage name and id.

        :param _server: Unused, required as part of the signature of a message
            builder.
        :param client: The client object dictating the cage name and id.
        :return: A 2-tuple of str, str containing a name and ID of a cage
        """
        return (client.cageName, client.cageID)

    def buildSiblingMessage(_server: 'scorhe_server.server.CameraServer',
                            _client: 'scorhe_server.server.CameraClient',
                            address: str,
                            ) -> Tuple[str]:
        """Constructs a 1-tuple containing the given address.

        This tuple is used to tell all the clients that a new client connected,
        with the given address.

        :param _server: Unused, required as part of the signature of a message
            builder.
        :param _client: Unused, required as part of the signature of a message
            builder.
        :param address: The address of a client, as a str
        :return: A 1-tuple of str that is the ip address of a a newly connected camera
        """
        return (address,)

    def buildSetExpMessage(server: 'scorhe_server.server.CameraServer',
                           _client: 'scorhe_server.server.CameraClient',
                           ) -> Tuple[str, str, str, int]:
        """Construct a 4-tuple dictating the experiment details to the clients.

        the tuple contains, in order, the name, start time, end time, and the
        number of participating cameras.

        This message does not actually tell the pi when to start or stop
        recording. That is handled by the startRecordingMessage and
        stopRecordingMessage.

        :param server: The server containing the experiment settings and
            clients.
        :param _client: Unused, but required as part of the signature of a
            message builder.
        :return: A 4-tuple of str, str, str, int for experiment name, start
            time, end time, and number of cameras.
        """
        return (server.expName, server.startTime, server.endTime,
                len(server.clients.getClients('Camera')))

    def buildSetZoomPointsMessage(server: 'scorhe_server.server.CameraServer',
                                  client: 'scorhe_server.server.CameraClient',
                                  ) -> Tuple[int, int, int, int]:
        """Constructs a 4-tuple which dictates what part of the image is recorded.

        The tuple contains the coordinates of the upper left corner and the
        width and height of the image that should be used to crop the video.
        Current RPis record at 1296x972, which makes the limits for the view the
        same.

        Keep in mind that the cropping is applied to the rotated image (which
        allows the user to dictate the crop points from the rotated image).
        The pi will also reject aspect ratios that are too large or too small,
        as it can cause it to freeze. As such, the ratio between with and height
        must be between 0.5 and 2.

        :param server: The server containing the settings for the camera zooms.
        :param client: The client object for the camera whose zoom must be set.
        :return: A 4-tuple of int dictating x,y of upper left corner and width,
            height.
        """
        h = tuple(server.clientOptions.zoomLocation[client.cameraID])
        d = tuple(server.clientOptions.zoomDimension)
        return h + d

    def buildSetRotationMessage(server: 'scorhe_server.server.CameraServer',
                                client: 'scorhe_server.server.CameraClient',
                                ) -> Tuple[int]:
        """Constructs a 1-tuple containing the rotation of the given client.

        If the camera does not have a specific rotation, the default is
        returned.

        The rotation is assumed to always be one of: 0, 90, 180, 270. This
        assumption is checked on the client side, as it is a limitation set by
        the PiCamera.

        :param server: The server object where the rotations are set.
        :param client: The client object for the camera to set  the rotation for.
        :return: A 1-tuple of an int which is the value set as the rotation for
            the given client.
        """
        try:
            return (server.clientOptions.rotation[client.cameraID],)
        except KeyError:
            return (server.clientOptions.rotation['default'],)

    def buildSetCamMapMessage(server: 'scorhe_server.server.CameraServer',
                              client: 'scorhe_server.server.CameraClient',
                              ) -> Tuple[str]:
        """Constructs a 1-tuple of the camera name or id.

        Retrieves the camera name from the server's client options.
        If the camera does not have a name set, its unique camera id is sent
        instead.

        :param server: The server object where the camMap is set.
        :param client: The client object for the camera whose name is retrieved.
        :return: A 1-tuple of a str which is either the given camera's
            user-defined name or the camera's ID, if the name was not set.
        """
        try:
            return (server.clientOptions.camMap[client.cameraID],)
        except KeyError:
            return (client.cameraID,)

    def buildSetCompressionMessage(server: 'scorhe_server.server.CameraServer',
                                   _client: 'scorhe_server.server.CameraClient',
                                   ) -> Tuple[float]:
        """Constructs a 1-tuple containing the user set compression factor.

        The compression must be a float, which dictates what factor to
        shrink each side of the video's frame.

        For example, a compression of 3.0 will shrink each side by a factor a 3
        (which results in an image 1/9th the size it would have been).

        :param server: The server object where the compression is set.
        :param _client: Unused, part of the default signature for builder functions
        :return: A 1-tuple containing a float.
        """
        return (server.clientOptions.compression,)

    o = protocol.MessageBuilder()
    o.addRule('handshake', 'S', buildHandshakeMessage)
    o.addRule('poke')
    o.addRule('start recording', 'iid', buildStartRecordingMessage)
    o.addRule('stop recording', 'd', buildStopRecordingMessage)
    o.addRule('start previewing', 'id', buildStartPreviewingMessage)
    o.addRule('stop previewing', 'd', buildStopPreviewingMessage)
    o.addRule('set FPS', 'i', buildSetFPSMessage)



    o.addRule('set dimension', 'ii', buildSetDimensionMessage) 



    o.addRule('set stream format', 'S', buildSetStreamFormatMessage)
    o.addRule('set vflip', '?', buildSetVFlipMessage)
    o.addRule('set color mode', '?', buildSetColorModeMessage)
    o.addRule('set view', 'S', buildSetViewMessage)
    o.addRule('set autogain', '?', buildSetAutogainMessage)
    o.addRule('set gain', 'd', buildSetGainMessage)
    o.addRule('set shutter speed', 'i', buildSetShutterSpeedMessage)
    o.addRule('set ISO', 'i', buildSetISOMessage)

    o.addRule('set brightness', 'i', buildSetBrightnessMessage)
    ##contraster$
    o.addRule('set contrast', 'i', buildSetContrastMessage)

    o.addRule('sync clocks', 'iSiiiid', buildClockSyncMessage)
    o.addRule('bundle', 'SS', buildBundleMessage)
    o.addRule('restart')
    o.addRule('reboot')
    o.addRule('sibling', 'S', buildSiblingMessage)
    o.addRule('send exp', 'SSSi', buildSetExpMessage)
    o.addRule('set zoom points', 'iiii', buildSetZoomPointsMessage)
    o.addRule('set rotation', 'i', buildSetRotationMessage)
    o.addRule('set camMap', 'S', buildSetCamMapMessage)
    o.addRule('set compression', 'd', buildSetCompressionMessage)
    return protocol.Protocol(i, o)
