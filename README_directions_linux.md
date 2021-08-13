SCORHE (System for Continuous Observation of Rodents in Home-cage Environment) 
is a system designed to monitor and analyze the behavior of animals in a
monitored environment, complete with video acquisition, editing and annotation
utilities.

# SCORHE Video Acquisition Playback and Annotation v1.0.1 for Windows 10 and Linux (Ubuntu 18.04) as of 7/2020


# (*NOTE: this version is for monitoring mice and features synchronous recording and as of yet does not feature the asynchronous recording)

# HARDWARE NEEDED  
- 4 Raspberry Pi 3B (RPi)  (You can also utilize RPi 4B however different instructions may apply for display and microSD card requirments)
- 4 NoIR Camera V2
- Computer with Ethernet capabilities
- 1 or 2 Gigabit Routers (at least 7 open ethernet ports, one for each RPi, one for Host PC, and 2 as intermediaries between the two routers)
- Micro USB power cables (A-Male to Micro-B), with a current supply of at least 2 A (Amps) (possibly more for hooking up NoIR Cameras) or at least 3.5 Amps if using RPi 4B
- 7 Cat 6 Ethernet cables (depending one whether or not you have 1 or 2 Gigabit routers)
- USB keyboard and mouse (to connect to a RPi, via USB ports)
- HDMI Cable (to connect RPi to display)
- Display with HDMI capabilities 
- 4 microSD cards that are at least 16GB in size however I recommend 32GB as it is not signifficantly more expensive (about a $1 to $2 difference as of 2020) 
     and will work better with later versions of RPi's (such as RPi 4B)
- An microSD card to SD card adapter
-If your PC doesn't have an sd card port then please get a usb adapter that can both READ and WRITE with regards to the microSD card.
- FLASH DRIVE ( >32GB can cause problems if not formatted in FAT32 but as long as it is formatted with FAT32 and not exFAT or other format you should be fine)
- A seperate keyboard and mouse with USB plugs and connect to RPi




# SETTING UP SOFTWARE needed on PC with Ubuntu 18.04 Linux (Computer with Ethernet Capabilites)
(**Note whenever the terminal prompts you with:
	[sudo] password for <YOUR USERNAME>:
Type in your password to the computer, the password will not show up on the terminal even as you type it however the terminal is registering it. After you are done typing it in press enter**)

(** During this part you may get prompts such as
    Do you want to continue? [Y/n]
Please type in 'y' and hit enter **)


1. Go to /***REPLACE WITH REPOSITORY WEB LOCATION ***/ and download .zip
2. Copy the repository to your Documents folder.
3. Open up a  terminal (Cntrl + Alt  + T)
4. Type into terminal:
		> sudo apt-get upgrade
		> sudo apt-get update
		> sudo apt-get install python3-pip
5. Type into terminal:
		> sudo apt-get install python3-pyqt5
		> pip3 install numpy==1.15.0
		> pip3 install opencv-python==3.3.0.9
		> pip3 install paramiko==1.18.0
		> pip3 install matplotlib==2.0.2
		> pip3 install typing
		> pip3 install pygo
		> pip3 install pygi
		> sudo apt-get install git
		> sudo apt-get install emacs
		> cd
6. Now we must install python3.4 without messing up any of the other python distros (See full instructions here https://www.tutorialspoint.com/how-to-install-python-3-4-4-on-ubuntu)
	-Type into your terminal
	"""
	> sudo apt-get install build-essential checkinstall
	"""
	-Type 'y' when prompted
	"""
	> sudo apt-get install libgdbm-dev tk-dev libncursesw5-dev libssl-dev libsqlite3-dev libreadline-gplv2-dev libc6-dev libbz2-dev
	> cd /usr/src
	> sudo wget https://www.python.org/ftp/python/3.4.4/Python-3.4.4.tgz
	> sudo tar xzf Python-3.4.4.tgz
	> cd Python-3.4.4
	> sudo ./configure
	> sudo make altinstall
	> cd
	"""
	Now when you type in 'sudo python3.4 -V' into the terminal you shoud see:
	"
	Python 3.4.4
	"
7. Then type in the following and install gstreamer1.0
		> sudo apt-get install -f gstreamer1.0
		> sudo apt-get install -f gstreamer1.0-tools
	(The above may not always work so you may have to type in the gstreamer manually as seen in the following command line direction. In fact I recommend doing the following anyways just in case)
		> sudo apt-get install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio
	


8. Now we will install the MP4Box application and dependencies that are requried following directions found on https://gpac.wp.imt.fr/tag/mp4box/
   (***Update as of 7/17/2020 due to recent update by gpac MP4Box doesn't work please find the attached gpac in the file you downloaded or download an older version****)
	-Open a terminal and type
		"""
		> git clone https://github.com/gpac/gpac.git
		> cd gpac
		> ./configure --static-mp4box --use-zlib=no
		> make -j4
		> sudo make install
		> cd
		"""
	-In order to check that you have installed MP4Box type in "which MP4Box" into the terminal and you should see
		"""
		/usr/local/bin/MP4Box
		"""
9.  Then in your terminal typeff
		"""
		> cd Downloads/<INSERT the containing directory for VideoAPA_For_Host_PC>/VideoAPA_For_Host_PC/acquisition/
		> chmod +x linux_vr_run.sh
		> ./linux_vr_run.sh
		"""
10. The program should now run and you should see 4 black screens and a window open. Now close that window
11. (*NOTE at times you may get an error in server.py get_ip_address  this is due to the fact that your ethernet identifier may have been changed during your installation of ubuntu. You can check by going to command line and typing in
		> sudo apt-get install net-tools
	Type in:
		> ifconfig -a
	If you don't see anything called eth0 Follow further directions from the second answer at https://askubuntu.com/questions/767786/changing-network-interfaces-name-ubuntu-16-04
		> sudo nano /etc/default/grub
	Change to GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0"
		>sudo update-grub
	Reboot the computer


# SETTING UP THE RASPBERRY PI's  (**NOTE** if you are integrating a depth camera please go to instructions called "SETTING UP THE RPi4 with Ubuntu 18.04")
	(Steps 8-12 can be done on a Windows computer and if you wish to see those instructions please refer to README.md)
	1. Go to (https://www.raspberrypi.org/downloads/) on your PC and click on the Raspberry Pi Imager for Ubuntu and download.
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
			> sudo apt-get install -f gstreamer1.0
			> sudo apt-get install -f gstreamer1.0-tools
			> sudo apt-get install python3-pyqt5
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

**Further Instructions for Depth Camera


# SETTING UP THE SYSTEM
Now that you have all four RPi's setup with the software, as well as the PC set up we can hook up the ethernet cables.
	1. Turn off wifi on the host PC
	2. The only ports that you should be using on the gigabit routers are ones that have numbers next to them and are not WAN or LINK ports
	3. Have the PC hook up to 1 on the gigabit router. Then hook up RPi's 1, 2, 3 and 4 repectively if you have enough ports on your gigabit router
	4. If you only have 2 gigabit routers hook an ethernet cable as an intermediate between both routers and plug in the rest of the ethernet cables with the RPis

*Note: The RPi 3B's need at least 2 Amps of current each to operate, however 3 Amps is preferred if possible. (The RPi 4B however require a minimum of 3.5 Amps to operate normally)
	5. Make sure the NoIR cameras are inserted properly. The blue tab should be facing towards the Ethernet port on the RPis

***SETTING UP THE RPi4 with Ubuntu 18.04***
	Please note that these instructions pertain to installing an Ubuntu 18.04 image on an RPi4. You must have access to an ethernet port for internet
	1. Download the RPi imager from https://www.raspberrypi.org/downloads/ 
	2. Go to https://ubuntu.com/download/raspberry-pi and download the 64bit version of Ubuntu 18.04 for the RPi4
	3. When promtpted allow the program to automatically open in RPi imager and write to the specified microSD card
	4. After done writing insert microSD into RPi4 and connect ethernet cable to RPi4
	5. Turn on RPi4 and you will be greeted with a screen that will ask you for an ubuntu user name and password. Type in: "ubuntu" for both (without quotation marks).
	6. Now you will be prompted to create a new username and password. Type in ubuntu for the username and a chosen password.
	7. Then type:
		> sudo apt-get update
		> sudo apt-get upgrade
	 (**If you run into trouble with either one of these processes (ie a lock error) try rebooting or powering off the RPi4. Do not power off the RPi4 if you are fetching reading or downloading something)
	8. Once you have updated the software please type in:
		> sudo apt install ubuntu-desktop
	9. If prompted choose the default selection.
	10. Then once you see the command terminal prompt "ubuntu@ubuntu: " you can reboot your pi using sudo reboot
	11. Once you have connected and logined to the desktop please connect to wifi.
	12. Then open the terminal with (Cntrl + Alt + T) and type:
		> sudo nano /etc/netplan/50-cloud-init.yaml
	13. Edit the text to include the following: 
		
		network:
			renderer: NetworkManager
			ethernets:
				eth0:
					dhcp4: true
					optional: true
		version: 2
	14. Save the edits by pressing (Cntrl + X) and then typing: Y when prompted.
	15. Now type into the terminal:
		> sudo netplan apply
	16. You should now see an ethernet connection, and at this point unless you don't have wifi you can unplug the ethernet cable from the RPi4
	

# RUNNING THE SYSTEM on Linux
		1. Open a terminal (Cntrl + Alt + T)
		2. In the terminal type
			"""
			>cd Downloads/<INSERT the containing directory for VideoAPA_For_Host_PC>/VideoAPA_For_Host_PC/acquisition/
			>chmod +x linux_vr_run.sh
			>./linux_vr_run.sh
			"""
		3. Any Experiment Data and Settings data made in the SCORHE application will be found in the folder in Downloads labeled SCORHE
#***************IMPORTANT NOTE: Operation Features with visuals can be found on the document attached "SCORHE Video Acquisition User Guide"*************
	



## Authors

- Joshua "Tabs not spaces" Lehman
- Simeon "Thread everything" Anfinrud
- Ryan "C is better" Rinker
- Yoni "I angered IT again" Pedersen
- Noah Cubert

### https://scorhe.nih.gov
