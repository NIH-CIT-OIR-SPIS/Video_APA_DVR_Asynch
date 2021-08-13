"""
File contains an object that can create a gplayer in a GUI frame
"""
import logging
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GObject, GstVideo
from PyQt5 import QtWidgets

GObject.threads_init()
Gst.init(None)

logger = logging.getLogger(__name__)


class GPlayer(QtWidgets.QWidget):
    """GPlayer object is used to create a Gstreamer player within a specified frame"""
    def __init__(self, port, winId, scaleWidth, scaleHeight):
        QtWidgets.QWidget.__init__(self)
        self.port = port
        """Port for gstreamer previewing"""
        self.winId = winId
        """winID of the frame the player will show in"""
        
        # Declare a GSt pipeline
        self.pipeline = Gst.Pipeline()

        # Create all the individual components of the pipeline to be linked
        self.udpsrc = Gst.ElementFactory.make('udpsrc', None)
        self.udpsrc.set_property('port', int(self.port))
        self.buff = Gst.ElementFactory.make('rtpjitterbuffer', None)
        self.depay = Gst.ElementFactory.make('rtph264depay', None)
        self.decoder = Gst.ElementFactory.make('avdec_h264', None)
        self.vidConverter = Gst.ElementFactory.make('videoconvert', None)
        self.scaler = Gst.ElementFactory.make('videoscale', None)
        self.sink = Gst.ElementFactory.make('autovideosink', None)
        
        # Add the components to the pipeline
        self.pipeline.add(self.udpsrc)
        self.pipeline.add(self.buff)
        self.pipeline.add(self.depay)
        self.pipeline.add(self.decoder)
        self.pipeline.add(self.vidConverter)
        self.pipeline.add(self.scaler)
        self.pipeline.add(self.sink)
        #try: 
        #    print(len(self.buff))
        #except Exception:
        #    print("no")
        # Link all the components together in order (essentially build the command)
        #self.udpsrc.link_filtered(self.depay, Gst.caps_from_string("application/x-rtp, payload=96"))
        self.udpsrc.link_filtered(self.depay, Gst.caps_from_string("application/x-rtp, payload=96"))
        self.depay.link(self.decoder)
        self.decoder.link(self.vidConverter)
        self.vidConverter.link(self.scaler)
        #print("scaleWidth {} scaleHeight{}".format(scaleWidth, scaleHeight))
        scaleStr = "video/x-raw, width=" + str(scaleWidth) + ",height=" + str(scaleHeight)
        self.scaler.link_filtered(self.sink, Gst.caps_from_string(scaleStr))

        # Set up signal communication
        self.bus = self.pipeline.get_bus()

        #try: 
        #    print(len(self.bus))
        #except Exception:
        #    print("no")
        #rint(self.bus.)
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)
        self.bus.connect('message::eos', self.on_eos)
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::element', self.on_sync_message)

    # -------Below are functions to handle certain signals from the player-----
    # They are pretty self-explanatory

    def on_sync_message(self, _bus, msg):
        """A function called when a synchronization message is sent by the gpac bus."""
        if msg.get_structure().get_name() == 'prepare-window-handle':
            # msg.src.set_property('force-aspect-ratio', True)
            msg.src.set_window_handle(self.winId)

    def quit(self, _player):
        """An external interface to close the pipeline. """
        self.pipeline.set_state(Gst.State.NULL)

    def on_eos(self, _bus, _msg):
        """A handler for the end of signal of the pipeline."""
        self.pipeline.seek_simple(
                Gst.Format.Time,
                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                0
        )

    def start(self):
        """An external interface to start the pipeline. """
        self.pipeline.set_state(Gst.State.PLAYING)

    @staticmethod
    def on_error(_bus, msg):
        """A handler for errors from the pipeline, which simply prints it."""
        logger.error('on_error():', msg.parse_error())
