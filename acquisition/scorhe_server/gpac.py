"""
The following is a file that will be used to convert h264 videos to mp4 format.
It also includes other helper methods to aid in the progress.
"""
import argparse
import glob
import logging
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import List

logger = logging.getLogger(__name__)

if platform.system() == 'Windows':
    _GPAC_SOURCE = os.path.join(os.path.dirname(__file__), 'mp4box', 'mp4box.exe').replace(os.sep, os.sep * 2)
    #print("GPAC SOURCE {}".format(_GPAC_SOURCE))
    if not os.path.isfile(_GPAC_SOURCE):
        raise RuntimeError('Bad windows install: mp4box could not be found. Should be at {}'.format(_GPAC_SOURCE))
elif platform.system() == 'Linux':
    _GPAC_SOURCE = 'MP4Box'
    if shutil.which(_GPAC_SOURCE) is None:
        raise RuntimeError('Bad linux configuration: This application requires that MP4Box is installed and in path.')
else:
    raise OSError('SCORHE Acquisition does not support your system: {}'.format(platform.system()))


class GPACException(Exception):
    """An exception specifying that the GPAC source had a problem."""
    pass


class SPSHeaderMissingException(GPACException):
    """An exception specifying that the given h264 file is missing its SPS header."""
    #print("SPSMISSING")
    pass


def get_sps_header(width: int, height: int) -> bytes:
    """Computes the sps header for a stream of width by height video.

    Assumes each macroblock is 16 pixels wide and each map unit is 16 pixels
    tall, meaning the value for the `pic_width_in_mbs_minus1` section of the
    header is width/16 - 1, and that the value for
    `pic_height_in_map_units_minus1` is height/16 - 1.

    If you want a more thorough walkthrough of the header, refer to the
    International Telecommunication Union's file on H.264:
    https://www.itu.int/rec/T-REC-H.264
    
    If that link doesn't work, try to find a spec of the H.264 format somewhere

    :param width: Width of the video frame in pixels
    :param height: Height of the video frame in pixels
    :return: A bytestream containing the SPS Header for the H.264 file with the
        given resolution.
    """
    # This part is in all headers, and is copied byte for byte from the H.264
    # from the streams that do work

    #print('width {}, height {}'.format(width, height))
    
    
    stream = [0x00,0x00, 0x00,0x01, 0x27,0x64, 0x00,0x28, 0xac,0x2b]
    width = int(width // 16)
    height = int(height // 16)
    size = '0100'  # these are also predetermined, but need to wait to be added
    # add width and height using Exp Golomb coding (check wikipedia).
    # keep in mind, sps header stores width and height as w-1, h-1, which also
    # makes Exp Golomb easier.
    size += '0' * (width.bit_length() - 1)
    size += str(bin(width))[2:]  # drop the '0b' part
    size += '0' * (height.bit_length() - 1)
    size += str(bin(height))[2:]  # drop the '0b' part
    # add the end in. Can't use bytestream since this can be offset any # of bits
    size += '11010000000011110001001000100110101'
    while len(size) > 8:
        nextByte = int(size[0:8], 2)
        size = size[8:]
        stream += [nextByte]
    while len(size) < 8:
        size += '0'
    stream += [int(size, 2)]
    #print("The bytes %s" % stream)
    return bytes(stream)


def convert(sourceFilename: str,
            destFilename: str,
            doConvert: bool,
            fps: int=30,
            ) -> bool:
    """Convert the source video into an MP4 video with the given destFilename.

    Use makeMP4() to run the full conversion routine, which removes the source
    video when done and patches in an SPS Header at the beginning of the video
    if it is missing.

    :param sourceFilename: The path to the source, including the extension.
    :param destFilename: Tje path to the destination file, including the
        extension.
    :param doConvert: Whether to actually convert the given file.
    :param fps: The number of frames per second the file is in.
    :return: True if the file was converted, False otherwise. So if
        ``doConvert`` is False, return must be False.
    """
    #print("my fps: {}".format(fps))
    if not doConvert:
        return False
    try:
        command = '{} -add "{}"%video -fps {} "{}"'.format(_GPAC_SOURCE, sourceFilename, fps, destFilename)
        #print(command)
        #command = '{} -fps {} -add "{}"%video -fps {} "{}"'.format(_GPAC_SOURCE, fps, sourceFilename, fps, destFilename)
        
        
        # Call an MP4Box subprocess and pipe its output to devnull so it doesn't
        # clutter the console
        with open(os.devnull, 'w') as nul:
            #print('command {}'.format(command))
            if subprocess.call(shlex.split(command), stderr=nul):
                # If the subprocess call doesn't return 0, something went wrong
                raise SPSHeaderMissingException(
                        'Failed to convert {} to {}'.format(sourceFilename,
                                                            destFilename))
            else:
                return True
    except FileNotFoundError as err:
        logger.error('{}: {}'.format(err, err.filename))
        logger.error('Error converting {}'.format(sourceFilename))
        return False


def add_sps(filename: str, width: int, height: int) -> None:
    """Creates a copy of the file, with an sps header in
    filename + 'fixed.h264'
    """
    with open(filename + 'fixed.h264', 'wb') as fixed:
        fixed.write(get_sps_header(width, height))
        with open(filename, 'rb') as file:
            buffer = file.read(8192)
            #buffer = file.read(32784)
            while buffer:
                fixed.write(buffer)
                buffer = file.read(8192)
                #buffer = file.read(32784)


def makeMP4(sourceFilename: str,
            destFilename: str,
            fps: int,
            width: int,
            height: int,
            delete: bool=True,
            doConvert: bool=True,
            ) -> None:
    """Convert source to MP4 and remove old version

    If the first attempt at converting the source video fails, it is assumed
    that it is missing an SPS header (a rare, but occasional event that is
    caused by a bug in picamera) and patches in an SPS header at the beginning
    of the file before trying again.
    """
    #print(sourceFilename)
    #success = False
    try:
        if convert(sourceFilename, destFilename, doConvert, fps) and delete:
            logger.debug('Deleting {} (no added header)'.format(sourceFilename))
            os.remove(sourceFilename)
            #print("getSpsHEader: {}".format(get_sps_header(width, height)))
        #return True
    except SPSHeaderMissingException as e:
        print(e)
        add_sps(sourceFilename, width, height)
        try:
            print("sourceFilename %s" % sourceFilename)
            if convert(sourceFilename + 'fixed.h264', destFilename, doConvert,
                       fps) and delete:
                logger.debug('Deleting {} (added header)'.format(sourceFilename))
                os.remove(sourceFilename)
            #return True
        except SPSHeaderMissingException as err:
            #substr = destFilename.split('/', 1)
            #fileName = substr[1]
            #if not os.path.exists(fileName):
            logger.error('Could not convert {} to {}, even after patching'.format(
                                sourceFilename, destFilename))
                #raise GPACException(
                        #'Could not convert {} to {}, even after patching'.format(
                        #        sourceFilename, destFilename))
            #return False
        finally:
            os.remove(sourceFilename + 'fixed.h264')
            #print("Finally happended")
            #print("destFileName: {}".format(destFilename))
            #return success


def getNumFrames(filename: str) -> int:
    """Returns an integer number of frames in the given MP4 file.

    If an error occurs, returns -1
    """
    try:
        process = subprocess.Popen(shlex.split(
                '{} -info "{}"'.format(_GPAC_SOURCE, filename)),
                stdout=open(os.devnull, 'w'),
                stderr=subprocess.PIPE)
        info = process.stderr.read().decode()
        match = re.search('- (\d+) samples', info)
        if match:
            return int(match.group(1))
    except FileNotFoundError as err:
        logger.error('{}'.format(err))
        logger.error('Error getting frame count for file: {}'.format(
                filename))
    return -1


class ValidDimension(argparse.Action):
    """An argparse Action that validates the dimensions passed for conversion."""
    def __call__(self, parser, namespace, values, option_string=None) -> None:
        if values[0] % 16 != 0:
            raise argparse.ArgumentError(self, "invalid value: '{}' (must be divisible by 16)".format(values[0]))
        setattr(namespace, self.dest, values[0])


def main(argv: List[str]) -> None:
    """This is the main function that runs the script from the command line args.

    This function constructs and argument parser to parse the passed parameters.
    After parsing the arguments, it scans the given directory for files and
    acts based on the given parameters. To check the usage of this function,
    run this file as a script or the function with parameter ``--help``.

    :param argv: The command line arguments split on spaces.
    :return Nothing
    """
    parser = argparse.ArgumentParser(prog='gpac.py', add_help=False)
    parser.add_argument('--help', action='help', default=argparse.SUPPRESS,
                        help='Show this help message and exit')
    parser.add_argument('-w', '--width', required=True, nargs=1, type=int,
                        help='Width of the video (in pixels)')
    parser.add_argument('-h', '--height', required=True, nargs=1, type=int,
                        help='Height of the video (in pixels)')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='Whether to delete h264 files')
    parser.add_argument('-n', '--no-convert', dest='convert', action='store_false',
                        help='Specify if you do not want to convert the files')
    parser.add_argument('-f', '--file', action='store', default='.', type=str,
                        help='The directory in which to look for files to convert')
    parser.add_argument('--fps', action='store', default=30, type=int,
                        help='The fps of the file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Prints all progress. Overrides --silent regardless of position.')
    parser.add_argument('-s', '--silent', action='store_true',
                        help='Suppresses all output.')
    args = parser.parse_args(argv)
    run(args.width, args.height, delete=args.delete, doConvert=args.convert,
        filesDir=args.file, fps=args.fps, verbose=args.verbose, silent=args.silent)


def run(width: int,
        height: int,
        *,
        delete: bool=False,
        doConvert: bool=True,
        filesDir: str='.',
        fps: int=30,
        verbose: bool=False,
        silent: bool=False) -> None:
    """

    :param width: Width of the video (in pixels).
    :param height: Height of the video (in pixels).
    :param delete: Whether to delete h264 files.
    :param doConvert: Specify if you do want to convert the files.
    :param filesDir: The directory in which to look for files to convert
    :param fps: The fps of the file.
    :param verbose: Whether to print all progress. Overrides ``silent``.
    :param silent: Whether to suppresses all output.
    """
    toConvert = set()
    if not silent:
        logger.info("Scanning for files to convert...")
    for file in glob.iglob(filesDir + "/*.h264"):
        pre = file.rsplit(".", 1)[0]
        if os.path.isfile(pre + ".h264") and os.path.isfile(pre + ".mp4"):
            if os.path.getsize(pre + ".mp4") <= os.path.getsize(pre + ".h264"):
                # since the mp4 is the h264 with some headers (about 15kb,
                # might want to use that fact too?), if the mp4 is not larger,
                # conversion failed before so it must be reconverted.
                os.remove(pre + ".mp4")
                toConvert.add(pre)
            elif delete:
                os.remove(pre + ".h264")
        else:
            toConvert.add(pre)

    counter = 0
    tot = len(toConvert)

    if not silent or verbose:
        logger.info("Converting {} files...".format(tot))
    for pre in toConvert:
        if os.path.isfile(pre + ".mp4"):
            counter += 1
            continue
        #print("fps {}, width {}, height {}".format(fps, width, height))
        makeMP4(pre + ".h264", pre + ".mp4", fps, width, height, delete, doConvert)
        counter += 1

        #print("pre {}, os.path {}".format(pre, os.path.isfile(pre + ".h264")))
        #print("makeMP4: {},  counter {}".format(ismp4, counter))
        if verbose:
            logger.debug("{}/{}".format(counter, tot))
    if verbose:
        logger.debug("~~~~~~~~~~~\n~~~~~~~~~~~")
    if not silent or verbose:
        counter = -1
        logger.info("Conversion finished.")


    #for pre in toConvert:
    #    if os.path.isfile(pre + ".mp4") and os.path.isfile(pre + ".h264") and counter == -1:
    #        try:
    #            os.remove(pre + ".h264")
    #            p = pre + ".h264"
    #            print("Removing file: {}".format(p))
    #        except Exception as err:
    #            logger.info("Error in gpac.py: {}".format(err))


if __name__ == '__main__':
    main(sys.argv)
