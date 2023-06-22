# SCORHE Video Acquisition For Asynchronous Playback and Annotation for Linux

Version is for people who wish to take simultaneous video from all cameras connected, 
for Synchronous only version please see: https://github.com/NIH-CIT-OIR-SPIS/VideoAPA_DVR_Synch


## Link to Paper
https://doi.org/10.1016/j.ohx.2020.e00160

## Collaborators
Dr. Ghadi Salem, PhD, SPIS, NIH

Noah Cubert, Engineering Intern, NIH, NBIB

Niall Cope, Biomedical Engineer Research Fellow, FDA

Joshua Lehman

Simeon Anfinrud

Ryan Rinker

Yoni Pederson

SCORHE (System for Continuous Observation of Rodents in Home-cage Environment) 
is a system designed to monitor and analyze the behavior of animals in a
monitored environment, complete with video acquisition, editing and annotation
utilities.


# HARDWARE NEEDED
N = number of Raspberry Pis

- \<20 Raspberry Pi 3Bs (RPi)
- N Raspberry Pi Cameras
(Can be from only the follwoing type:
RPi Camera V2 or V2 NoIR, or Raspberry Pi High Quality Camera)
- Computer with Ethernet capabilities
- 1 [Linksys LRT224](https://www.linksys.com/lrt214-business-gigabit-vpn-router/LRT214.html) router and more Ethernet switches if need be (one ethernet for each RPi, and extra ports for Host PC, and extra ethernet cables as intermediaries between the two routers) 

- Micro USB power cables (A-Male to Micro-B), with a current supply of at least 2 A (Amps) (possibly more for hooking up cameras) or at least 3.5 Amps if using RPi 4B

- N Ethernet cables for each RPi and one more for the Host PC, and extra cables for external switches.
- USB keyboard and mouse (to connect to a RPi, via USB ports)
- HDMI Cable (to connect RPi to display)
- Display with HDMI capabilities (Or remote in to Raspberry pi's via SSH)
- N microSD cards that are at least 8GB in size however I recommend 32GB as it is not signifficantly more expensive (about a $1 to $2 difference as of 2020) 
and will work better with later versions of RPi's (such as RPi 4B)
- A microSD card to USB adapter (if your PC does not have a microSD card port)
- FLASH DRIVE ( >=32GB can cause problems if not formatted in FAT32 but as long as it is formatted with FAT32 and not exFAT or other format you should be fine)
- A seperate keyboard and mouse with USB plugs and connect to RPi (or SSH/VNC into RPi)


# SETTING UP SOFTWARE needed on PC with Ubuntu 18.04/20.04
(**Note whenever the terminal prompts you with:
	[sudo] password for <YOUR USERNAME>:

Type in your password to the computer, the password will not show up on the terminal even as you type it however the terminal is registering it. After you are done typing it in press enter**)

(** During this part you may get prompts such as
    Do you want to continue? [Y/n]
Please type in 'y' and hit enter **)

## Automatic Script Installation
As of 06-22-2023 there is a script called install_SCORHE.sh and it will install all the necessary software for you. Just run
```
sudo chmod +x install_SCORHE.sh && ./install_SCORHE.sh
```
and it will install all the necessary software for you.

(**Note** that this script will perform updates and upgrades on your computer)

## Manual Installation
1. Clone this https://github.com/NIH-CIT-OIR-SPIS/Video_APA_DVR_Asynch  repository to your computer, or download a compressed file of the code (Go to Code -> Download ZIP) to your computer and extract it.

```
git clone https://github.com/NIH-CIT-OIR-SPIS/Video_APA_DVR_Asynch.git
```

2. Copy the Video_APA_DVR_Asynch to your Downloads folder.

3. Open up a terminal (CTRL + ALT + T)

Make sure you have python3 installed on your computer by typing in the following into the terminal:

```
python3 --version
```

If you do not have python3 installed (specifically python3.8) then type in the following into the terminal:
```
sudo apt-get install python3
```


(*** Note that this was tested with python 3.8.10 and it is recommended you use this version all other versions are untested as of yet. ***)

4. Type into terminal:
```
sudo apt-get -y update && \
sudo apt-get -y upgrade && \ 
sudo apt-get install python3-pip && \
sudo apt-get install python3-pyqt5 && \
pip3 install numpy opencv-python paramiko typing matplotlib pygo pygi requests && \
sudo apt install net-tools
```


7. Then type in the following and install gstreamer1.0
```	
sudo apt-get install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio
```	


8. Now we will install the MP4Box application and dependencies that are requried following directions found on https://gpac.wp.imt.fr/tag/mp4box/


(Try downloading directly from the site first, only use wget if you know the exact link to the file you want to download)
```
wget https://download.tsi.telecom-paristech.fr/gpac/release/2.2.1/gpac_2.2.1-rev0-gb34e3851-release-2.2_amd64.deb
```

Once you have downloaded the file type in the following:	
```
sudo apt install ./gpac_2.2.1-rev0-gb34e3851-release-2.2_amd64.deb  # Or whatever you have corresponding to the correct release
```
In order to check that you have installed MP4Box type in 
```
which MP4Box
``` 
and you should see
```
/usr/bin/MP4Box
```
9.  Then in your terminal typeff
```
cd ~/Downloads/Video_APA_DVR_Asynch/acquisition/
```
If this is your first time running the program then type in the following:
```
chmod +x linux_vr_run.sh && ./linux_vr_run.sh
```
Otherwise type in the following:
```
./linux_vr_run.sh
```

10. The program should now run and you should see 4 black screens and a window open. Now close that window

From now on to run the program do in the acquisition folder:
```
./linux_vr_run.sh
```


# SETTING UP THE RASPBERRY PI's  

It is highly recommended to use the Attached Raspberry Pi 3B image (found in Releases) as it has all the necessary software installed and configured.



## Using Pre-made Raspberry Pi Image (Recommended)
For this part you will need:
A computer with Windows or Ubuntu
A microSD to USB adapter or a computer with a microSD card reader
A microSD card that is >8GB in size.

Go to the releases page and download the latest image (currently 1.0.1) 

Or click on this link to download the image directly: 
[Raspberry Pi 3B Image]()

You can use [7zip](https://www.7-zip.org/) to unzip the file (if on windows) or just extract it on Ubuntu by left clicking on the file and hitting 'Extract here'.

Please use [balenaEtcher](https://www.balena.io/etcher/) to write the image to the microSD card.



If you wish to setup the Raspberry Pi software manually please follow the instructions below.

## Manual Installation
(**NOTE** if you are integrating a depth camera please go to instructions called 
"SETTING UP THE RPi4 with Ubuntu 18.04")
	
(Steps 8-12 can be done on a Windows computer and if you wish to see those instructions please refer to README.md)
1. Go to (https://www.raspberrypi.org/downloads/) on your PC and click on the Raspberry Pi Imager for Ubuntu and download. (You must download the Buster image 32-bit (not anything newer))
2. If you have a previous version of RPi os on the microSD card do the following, Otherwise continue
		- Insert your microSD card into your computer and type in the computer application search bar 'Disks' and open the application that shows up
		- Scroll to your specified microSD card and click on the gear symbol on your specified microSD card
		- Click on the option "Format Partition".
				-Name the volume rpiBoot
				-Make sure the "Erase" Switch is gray not green
				-Under "Type" select the circle "For use with all systems and devices (FAT)" and click next
		-Then after the formating has finished go to the gear symbol again and this time select "Edit Partition"
		-From the type menu choose the option "Linux" and de-select Bootable
		-Click change
	3. Insert you microSD card into your computer, and open the RPi imager for Ubuntu. 
	4. Pick  Raspberry pi OS 32 bit and choose your SD card and write.
	5. After done downloading insert you microSD card into your RPi.

#	Setting up Software of RPi 


	6. Choose your countries settings for time and keyboard layout.
	7. Skip setup of password and user name
	8. Connect to a wifi network
	9. Update software as neccessary.
	10. After update and install reboot RPi.
	11. Now click on RPi symbol on top left and from the drop down menu click on Preferences->Raspberry Pi Configuration
		In the window that pops up go to Interfaces and Enable both Camera and SSH and reboot
	12. Now we will open the terminal (Crtl + Alt + T)
	13. In the terminal type in:
			'''
			sudo apt-get install -f gstreamer1.0
			sudo apt-get install -f gstreamer1.0-tools
			sudo apt-get install python3-pyqt5
			'''
			-(*Note) whenever you are prompted with the "Do you wish to continue [Y/N]" just type in 'y' and hit 'Enter'
	14. Now in the terminal type in:
			'''
			> sudo apt install python3.4
			'''
			(again hit 'y' if prompted with the "Do you wish to continue [Y/N]")
	15. Disable the wifi by clicking on the wifi symbol in the top right corner of the screen and clicking 'Turn off wifi'
	16. Turn off bluetooth in the same way
	17. Now in the terminal type in:
			'''
			> crontab -e
			'''
		and then type in 1 if prompted with somthing and hit enter
		Scroll to the bottom of the file (using the arrow keys only on the keyboard)
		Then type in exactly on the bottom 
			'''
			@reboot sleep 10; export XAUTHORITY=/home/pi/.Xauthority; export DISPLAY=:0.0; python3.4 /home/pi/scripts/
			'''
		(to exit hit Cntrl + X then 'y' then 'enter')

	18. Now in the terminal type in:
			'''
			> sudo nano /etc/lightdm/lightdm.conf
			'''
			Scroll using the arrows until you find the text '[Seat:*]'
			Underneath this text type in 'xserver-command=X -s 0 dpms'
			Then exit (Cntrl + X then 'y' then 'enter')
	19. Now in the terminal type in:
			'''
			> sudo nano /boot/config.txt
			
			'''
			Scroll to the line where you see " #hdmi_force_hotplug=1 " and delete the '#' symbol (****NOTE BE WEARY about doing this as with older RPi's, like RPi 4B, uncommenting this line can cause problems with the hdmi display)

			Scroll to the bottom and type in the following:
				'''
				dtoverlay=pi3-disable-bt
				dtoverlay=pi3-disable-wifi
				gpu_mem=700
				'''
			Save and exit
			(*note that this will make it so that automatically the pi cannot be connected to wifi at all or bluetooth, and the only way to reconnect them
			would be to delete the two lines written above in /boot/config.txt , the gpu_mem allows for more operation of RAM by gpu)
	21. Click "Advanced" and check "Minimize panel when not in use". 

			
	22. Two Options in this section either:
	a) Flash Drive Method (Easier method but flash drive must be formatted
		-Go back to your PC and insert your (8GB/16GB/32GB) flash drive. From this directory go to 'Place in RPi' and copy all files in that directory and place them on your flash drive.
		-Insert your flash drive into your RPi
		-A window should pop up on your RPi hit 'OK'
		-Then go to your terminal and type in:
				'''
				> cp -r /media/pi/<YOUR DRIVE NAME>/scripts /home/pi/
				'''
				Then type in:
				'''
				> ls 
				'''
				And you should see "scripts" listed as one of the new folders in the pi directory
		-Remove your flash drive (Eject can be found by going to the new symbol that popped up on the top right panel and clicking it and then clicking on your drive)
	b) File Transfer Method (no flash drive needed)
		-Add the provided "scripts" folder to the "/home/pi" directory using a file transfer client such as WinSCP or FileZilla using an SFTP connection. 
		 More information on this can be read at: https://www.raspberrypi.org/documentation/remote-access/ssh/sftp.md
23. Now turn off RPi take out the microSD.
24. You can make copies of the image you created (Assuming all microSD cards are the same size or greater) utilizing Win32 application (https://sourceforge.net/projects/win32diskimager/) 
25. More information about creating image copies can be found here (https://raspi.tv/2012/how-to-make-a-raspberry-pi-disk-image-to-sd-card-with-win32diskimager)
26. Create copies of the current microSD and place them on the other 3 microSD cards 


# SETTING UP THE SYSTEM
Now that you have all four RPi's setup with the software, as well as the PC set up we can hook up the ethernet cables.
	1. Turn off wifi on the host PC
	2. The only ports that you should be using on the gigabit routers are ones that have numbers next to them and are not WAN or LINK ports
	3. Have the PC hook up to 1 on the gigabit router. Then hook up RPi's 1, 2, 3 and 4 repectively if you have enough ports on your gigabit router
	4. If you only have 2 gigabit routers hook an ethernet cable as an intermediate between both routers and plug in the rest of the ethernet cables with the RPis

*Note: The RPi 3B's need at least 2 Amps of current each to operate, however 3 Amps is preferred if possible. (The RPi 4B however require a minimum of 3.5 Amps to operate normally)
	5. Make sure the NoIR cameras are inserted properly. The blue tab should be facing towards the Ethernet port on the RPis


# RUNNING THE SYSTEM on Linux
1. Open a terminal (Cntrl + Alt + T)
2. In the terminal type
```
cd ~/Downloads/Video_APA_DVR_Asynch/acquisition/
```
If this is your first time running the program then type in the following:
```
chmod +x linux_vr_run.sh && ./linux_vr_run.sh
```
3. Any Experiment Data and Settings data made in the SCORHE application will be found in the folder in Downloads labeled SCORHE
#***************IMPORTANT NOTE: Operation Features with visuals can be found on the document attached "SCORHE Video Acquisition User Guide"*************
	



## Authors

- Joshua "Tabs not spaces" Lehman
- Simeon "Thread everything" Anfinrud
- Ryan "C is better" Rinker
- Yoni "I angered IT again" Pedersen
- Noah Cubert

### https://scorhe.nih.gov
