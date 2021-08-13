"""A set of tests for the gpac file."""

import glob
import os
import re
import unittest
import shutil

from acquisition.scorhe_server import gpac


class TestGpacStateless(unittest.TestCase):
    def test_header_generator(self):
        """Tests the gpac script to make sure that it creates the correct sps header."""
        sps1280x720 = b'\x00\x00\x00\x01\'d\x00(\xac+@(\x02\xdd\x00\xf1"j'
        self.assertEqual(gpac.get_sps_header(1280, 720), sps1280x720,
                         'gpac.py does not generate a correct sps header for 1280x720.')


class TestGpac(unittest.TestCase):
    def setUp(self):
        """Sets up the paths to the data and temporary file directories."""
        self.dataFolder = os.path.join(os.path.dirname(__file__), 'gpac_data')
        self.tempFolder = os.path.join(os.path.dirname(__file__), '_test_temp')
        if not os.path.exists(self.tempFolder):
            os.mkdir(self.tempFolder)

    def tearDown(self):
        """Cleans up the test, removing generated files."""
        shutil.rmtree(self.tempFolder)

    def test_num_frames(self):
        """Tests that the correct number of frames is retrieved. """
        testFiles = glob.iglob(os.path.join(self.dataFolder, 'known_frames_*.mp4'))
        reg = re.compile('.*known_frames_(\d+)\.mp4')
        for file in testFiles:
            expectedFrames = int(reg.search(file).group(1))
            self.assertEqual(gpac.getNumFrames(file), expectedFrames,
                             'gpac.py does not get the correct number of frames for {}.'.format(file))

    def test_make_mp4(self):
        testFiles = glob.iglob(os.path.join(self.dataFolder, 'make_mp4_*.h264'))
        reg = re.compile('.*make_mp4_(\d+)_(\d+)_([tf])([tf]).*\.h264')
        for file in testFiles:
            matches = reg.search(file).groups()
            width = int(matches[0])
            height = int(matches[1])
            delete = matches[2] == 't'
            convert = matches[3] == 't'
            fname = os.path.split(file)[1].rstrip('.h264')
            destH264 = os.path.join(self.tempFolder, fname + '.h264')
            destMp4 = os.path.join(self.tempFolder, fname + '.mp4')
            finalH264 = shutil.copy(file, destH264)
            gpac.makeMP4(finalH264, destMp4, 30, width, height, delete, convert)
            if delete:
                self.assertFalse(os.path.exists(finalH264),
                                 'h264 with name {} not deleted when it should have been.'.format(finalH264))
            else:
                self.assertTrue(os.path.exists(finalH264),
                                'h264 with name {} deleted when it should not have been.'.format(finalH264))

            if convert:
                self.assertTrue(os.path.exists(destMp4),
                                'mp4 with name {} not created when it should have been.'.format(destMp4))

                # turns out comparing the raw contents of mp4s can change, even
                # with the exact same source file, whether copied or not.
                # TODO: Use opencv to check the contents of the mp4s?
                # self.assertTrue(filecmp.cmp(destMp4, file.rstrip('h264') + 'mp4', shallow=False),
                #                 'converting {} to mp4 failed.'.format(file))
            else:
                self.assertFalse(os.path.exists(destMp4),
                                 'mp4 with name {} created when it should not have been.'.format(destMp4))
