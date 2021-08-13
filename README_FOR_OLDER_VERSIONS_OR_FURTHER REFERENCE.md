# SCORHE Video Acquisition Playback and Annotation

SCORHE (System for Continuous Observation of Rodents in Home-cage Environment)
is a system designed to monitor and analyze the behavior of animals in a
monitored environment, complete with video acquisition, editing and annotation
utilities.

## Getting Started

Each section of the SCORHE system is entirely self contained.

### Installation

The recommended way to install SCORHE is to download the installers for the
wanted parts. The installers are located in the `Output` folder within each
utility's folder. This installer requires admin privileges, and will install
each utility into `"C:\Program Files (x86)\SCORHE [name]"` with `name` being the
name of the utility.

If you do not have admin priviliges, or do not want to use them to install the
utilities, download the folder within the `dist` folder to wherever you would
like. To run the program, simply navigate into the folder and run the exe
located inside.

Alternatively, one could run the program from source, using the `run<name>.bat`
script (e.g. `runacquisition.bat` script for the Acquisition program).

The requirements to run for each utility from source vary by utility. Package
versions are recommended, newer versions for the same python version should work
but have not been tested. Ideally, we would use the newest versions of
all packages and python. Acquisition uses an older python version since pygi is
only available for python 3.4, as of January 2018.

#### Acquisition

Python Version: Python 3.4.4

Packages:
- [pygi 3.24.1](https://sourceforge.net/projects/pygobjectwin32/)
- [PyQt5 5.4.1](https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.1/)


#### Editor

Python Version: Python 3.6.2

Packages:
- [matplotlib 2.0.2](http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib)
- [numpy+mkl 1.13.1](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
- [PyQt5 5.9](https://pypi.python.org/pypi/PyQt5)
- [opencv-python 3.3.0.9](https://pypi.python.org/pypi/opencv-python)

#### Annotator

Python Version: Python 3.6.2

Packages:
- [numpy+mkl 1.13.1](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy)
- [PyQt5 5.9](https://pypi.python.org/pypi/PyQt5)
- [opencv-python 3.3.0.9](https://pypi.python.org/pypi/opencv-python)

Note: some of these packages use cython to install, and require Microsoft
Visual C++ build tools. Version 10.0 will be required for Python 3.4 and version
14.0 will be required for Python 3.6, per
[this](https://wiki.python.org/moin/WindowsCompilers).

To install the packages, run the following command:
```
"C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC\vcvarsall.bat" & pip install package
```
This command assumes you are using Python 3.4. If you are using Python 3.6,
replace `10.0` with `14.0`.

### Running

#### Acquisition

The acquisition program connects to multiple Raspberry Pi, with the associated
client program installed and a camera, over ethernet. As such, all the devices
should be connected a network with no other devices, or the internet.

The MUFFIN and SCORHE (Allentown and Thoren) systems are set up such that the 
user must simply connect an ethernet cable between their computer (the "server")
and the rack.

Currently, the program is only set to support MUFFIN setup. Immediately after
installation, the user must set an association between the clients/camera
streams and a location on the waffle, using the camera bundler available
through the settings menu. Once an association is made, the user can use the
corresponding button in the main window to select that stream for viewing. Note
that the user may be suppplied with such a configuration before recieving the
software and physical setup, but it can be changed at any time through the
bundler.

Once the cameras are set up correctly, the main window should state that there
are 24 cameras connected, and all of the buttons should be enabled. If this is
not the case, wait to ensure all the cameras have finished booting up, or
restart the program and the Pis. If that still does not fix the problem, try to
re-bundle the cameras. If this does not work, then there is a problem with the
software or the physical connection to the Pis.

If the program does set up correctly, the user can select a camera to view by
clicking the associated button. Note that the same button will be disabled for
the other views. If the button were to be pressed again, the preview will end,
and the button will be re-enabled for the rest of the views.

Once the user has confirmed that the settings and cameras are set up correctly,
they can start recording. They have two options to do so:
1. The "start recording" button.
   - This button starts recording from all of the cameras. The location of the
   recordings is, by default, in `%localappdata%\experiments\Untitled\`, and can
   currently only be changed in the source file `utils.py`.
2. Setting up an expriment.
   - The user can set up an experiment using the "Add Experiment" button. This
   allows the user to set an experiment to start and end at specific times, and
   to give the experiment a given name. The user can also set the folder to
   store the experiment files in. By default, the folder is
   `%localappdata%\experiments\`, but this can be customized, even to be in
   another hard drive. The video files will be stored in a folder inside the
   specified one, named identically to the experiment. For example, an
   experiment named `Testing` with the save folder set to
   `My Documents\Research\` will store its videos in the folder
   `My Documents\Research\Testing`.

Regardless of how the user started the recording, the filenames for the videos
will always be `{yyyy}-{MM}-{dd} {HH}h{mm}m{ss}s {cameraName}`, e.g.
`2017-12-25 17h59m03s B03`. Each video has an MP4 version that can be used for
processing or normal viewing, and an h264 version, which is the raw backup sent
from the cameras, in case of conversion issues.

The MP4 files can also be used, as is, in the Editor program, to select a
timeframe to store as a single file for each camera. More on this later.

## Authors
- Joshua "Tabs not spaces" Lehman
- Simeon "Thread everything" Anfinrud
- Ryan "C is better" Rinker
- Yoni "I angered IT again" Pedersen

### https://scorhe.nih.gov
