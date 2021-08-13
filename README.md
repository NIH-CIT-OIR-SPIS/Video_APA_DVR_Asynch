# SCORHE Video Acquisition Playback and Annotation v1.0.1 for Windows 10 and Linux

### Version includes asynchronous video capture

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
- 4 Raspberry Pi 3B (RPi)  (You can also utilize RPi 4B however different instructions may apply for display and microSD card requirments)
- 4 NoIR Camera V2
- Computer with Ethernet capabilities
- 1 Linksys LRT224 router and more gigabit Routers if need be (at least 7 open ethernet ports, one for each RPi, one for Host PC, and 2 as intermediaries between the two routers)
- Micro USB power cables (A-Male to Micro-B), with a current supply of at least 2 A (Amps) (possibly more for hooking up NoIR Cameras) or at least 3.5 Amps if using RPi 4B
- 7 Cat 6 Ethernet cables (depending one whether or not you have 1 or 2 Gigabit routers)
- USB keyboard and mouse (to connect to a RPi, via USB ports)
- HDMI Cable (to connect RPi to display)
- Display with HDMI capabilities (Or remote in to Raspberry pi's via SSH)
- 4 microSD cards that are at least 16GB in size however I recommend 32GB as it is not signifficantly more expensive (about a $1 to $2 difference as of 2020) 
     and will work better with later versions of RPi's (such as RPi 4B)
- An microSD card to SD card adapter
-If your PC doesn't have an SD card port then please get a usb adapter that can both READ and WRITE to and from the microSD card.
- FLASH DRIVE ( >32GB can cause problems if not formatted in FAT32 but as long as it is formatted with FAT32 and not exFAT or other format you should be fine)
- A seperate keyboard and mouse with USB plugs and connect to RPi



# SETTING UP SOFTWARE needed on PC (Computer with Ethernet Capabilites)

1. Go to /***REPLACE WITH REPOSITORY WEB LOCATION ***/ and download .zip
2. Copy the repository to your downloads folder if on Windows. If on Linux copy to your Documents folder.
3. Open up a windows terminal by typing in 'cmd' into the bottom left search bar and clicking on the black screen
4. Go to  https://www.python.org/downloads/release/python-344/ to install python 3.4.4, scroll to bottom and click on Windows x86-64 bit installer and save to your downloads
	-Click on application and follow directions, remember to set path, Save in C:\Users\Python34\ new directory 
5. Download the following packages save each of them into C:\Users\Python34
	- [pygi 3.24.1](https://sourceforge.net/projects/pygobjectwin32/files/?source=navbar)
	- [PyQt5 5.4.1](https://sourceforge.net/projects/pyqt/files/PyQt5/PyQt-5.4.1/)

6. Follow advice given on https://developercommunity.visualstudio.com/content/problem/589489/i-need-the-2010-build-tools-for-visual-studio.html
	-Download Microsoft Visual Studios 10.0
	" If you want an older version, please go to https://visualstudio.microsoft.com/vs/older-downloads/, select a product and 
	click on the download button to log in to your Visual Studio (MSDN) subscription or join the free Dev Essentials program (https://visualstudio.microsoft.com/dev-essentials/), 
	to gain access to the older versions. You can get all Visual Studio 2010 products from https://my.visualstudio.com/Downloads?q=visual%20studio%202010&wt.mc_id=o~msft~vscom~older-downloads "
7. Type into the search bar next to the Windows icon on your PC 'cmd' and open the Command Prompt that shows up
8. You should see something like the following:
	C:\Users\[YOUR USERNAME]>
9. Then type in: '''
 	> pip install numpy==1.15.0
	> pip install opencv-python==3.3.0.9
	> pip install setuptools==18.2
	> pip install requests==2.23.0
	> pip install pytz==2020.1
	> pip install yaml==5.3.1
	> pip install urllib3==1.25.9
	> "C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC\vcvarsall.bat" && pip install crypto==1.4.1 
	> pip install paramiko==1.18.0
	> pip install matplotlib==2.0.2
	> pip install typing
	> pip install PyQt5 
	'''
10. If you can't find vcvarsall.bat search for it in file explorer where Microsoft Visual Studio 10.0 was downloaded
11. Now reopen 'Command Prompt' and type in cd C:\Users\[YOUR USERNAME]\Downloads\Repository_For_Video_APA-6-23-2020\VideoAPA_For_Host_PC\acquisition	
12. Now type in runacquistion.bat (or you can just click on runacquisition.bat
13. The program should now run and you should see 4 black screens and a window open. Now close that window

**IMPORTANT NOTE ABOUT STORAGE: OCCASIONALLY THE PC might get full of unwanted temporary files which are not deleted and 
**can cause storage issues in order to stop this go C:\Users\<your username>\AppData\Local\Temp. Sort by size and you will find many files starting with gpac_... then delete the TMP files which are greater than 0KB
# SETTING UP THE RASPBERRY PI's 

	14. Go to (https://www.raspberrypi.org/downloads/) on your PC and click on the Raspberry Pi Imager for Windows and download.
	15. If you have a previous version of RPi os on the microSD card do the following, Otherwise continue
		- Insert your microSD card into your computer and type in the windows search bar 'Create and Format hard disk partitions' and click on the app that pops up
		- Scroll to your specified microSD card and left click to delete all volumes on the disk until it is unallocated.
		-Left click on the unallocated disk and create a new simple volume and follow the instructions.
		-Continue on to next step.
	16. Insert you microSD card into your computer, and open the RPi imager for windows. 
	17. Pick Raspberry Pi OS 32 bit and choose your SD card and write.
	18. After done downloading insert you microSD card into your RPi.

#	Setting up Software of RPi
	19. Choose your countries settings for time and keyboard layout.
	20. Skip setup of password and user name
	21. Connect to a wifi network
	22. Update software as neccessary.
	23. After update and install reboot RPi.
	24. Now click on RPi symbol on top left and from the drop down menu click on Preferences->Raspberry Pi Configuration
		In the window that pops up go to Interfaces and Enable both Camera and SSH and reboot
	25. Now we will open the terminal (Crtl + Alt + T)
	26. In the terminal type in:
			'''
			> sudo apt-get install -f gstreamer1.0
			> sudo apt-get install -f gstreamer1.0-tools
			> sudo apt-get install python3-pyqt5
			'''
			-(*Note) whenever you are prompted with the "Do you wish to continue [Y/N]" just type in 'y' and hit 'Enter'
	27. Now in the terminal type in:
			'''
			> sudo apt install python3.4
			'''
			(again hit 'y' if prompted with the "Do you wish to continue [Y/N]")
	28. Disable the wifi by clicking on the wifi symbol in the top right corner of the screen and clicking 'Turn off wifi'
	29. Turn off bluetooth in the same way
	30. Now in the terminal type in:
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

	31. Now in the terminal type in:
			'''
			> sudo nano /etc/lightdm/lightdm.conf
			'''
			Scroll using the arrows until you find the text '[Seat:*]'
			Underneath this text type in 'xserver-command=X -s 0 dpms'
			Then exit (Cntrl + X then 'y' then 'enter')
	32. Now in the terminal type in:
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
	33. Right click on the desktop menu bar and click on "panel settings"
	34. Click "Advanced" and check "Minimize panel when not in use". 

			
	35. Two Options in this section either:
	a) Flash Drive Method (Easier method but flash drive must be formatted
		-Go back to your PC and insert your (8GB/16GB/32GB) flash drive. From this directory go to 'Place in RPi' or the clients/source folder to copy the folder and copy all files in that directory and place them on your flash drive.
		-Insert your flash drive into your RPi
		-A window should pop up on your RPi hit 'OK'
		-Then go to your terminal and type in:
				'''
				> cp -r /media/pi/[YOUR DRIVE NAME]/scripts /home/pi/
				'''
				Then type in:
				'''
				> ls 
				'''
				And you should see "scripts" listed as one of the new folders in the pi directory
		-Remove your flash drive (Eject can be found by going to the new symbol that popped up on the top right panel and clicking it and then clicking on your drive)
	b) File Tranfer Method (no flash drive needed)
		-Add the provided "scripts" folder to the "/home/pi" directory using a file transfer client such as WinSCP or FileZilla using an SFTP connection. 
		 More information on this can be read at: https://www.raspberrypi.org/documentation/remote-access/ssh/sftp.md
36. Now turn off RPi take out the microSD.
37. You can make copies of the image you created (Assuming all microSD cards are the same size or greater) utilizing Win32 application (https://sourceforge.net/projects/win32diskimager/) 
38. More information about creating image copies can be found here (https://raspi.tv/2012/how-to-make-a-raspberry-pi-disk-image-to-sd-card-with-win32diskimager)
39. Create copies of the current microSD and place them on the other 3 microSD cards 




# SETTING UP THE SYSTEM
Now that you have all four RPi's setup with the software, as well as the PC set up we can hook up the ethernet cables.
	40. Turn off wifi on the host PC
	41. The only ports that you should be using on the gigabit routers are ones that have numbers next to them and are not WAN or LINK ports
	42. Have the PC hook up to 1 on the Linksys 224 gigabit router. Then hook up RPi's 1, 2, 3 and 4 repectively if you have enough ports on your gigabit router
	43. If you only have 2 gigabit routers hook an ethernet cable as an intermediate between both routers and plug in the rest of the ethernet cables with the RPis
	44. Make sure you only have one ethernet connection connected directly to the computer (if you have multiple ethernet connections on the computer make sure they are clear)
	45. Make sure the ethernet connection is 'Private' in order to change it go to Settings > Ethernet > [The connected network] > Network Profile and make sure 'Private' is selected. 
	46. If you still don't get a connection go to Settings > Ethernet > Network Profile and under Related Settings select 'Change Adapter Options'. Then select the ethernet connection port which you are connected to and left click to select 'Diagnose'. If it sees any errors apply fix and shutdown the computer then turn it back on.
	
*Note: The RPi 3B's need at least 2 Amps of current each to operate, however 3 Amps is preferred if possible. (The RPi 4B however require a minimum of 3.5 Amps)
	44. Make sure the NoIR cameras are inserted properly. The blue tab should be facing towards the Ethernet port on the RPis
	46. As of right now the PC must be connected to the Linksys 224 gigabit router, mainly for security reasons. Any other connections to a raspberry pi or another gigabit router are connected through this router. If you wish to add more raspberry pi's to connect you can add another gigabit router and connect it to the linksys router and plug in new raspberry pi's via the new gigabit router.



# RUNNING THE SYSTEM on Windows
	45. Assuming everything is correct you should be able to just go to /VideoAPA_For_Host_PC/acquisition/ and double click on runacqisition.bat (you could also make a shortcut of runacqisition.bat by left clicking and then creating a shortcut to drag to the desktop.
	46. If you wish you can also run via the command line by typing 'cmd' into the Windows search bar and click on the Command Prompt application that shows up.
	47. Type in:
		'''
		> cd [DIRECTORY HOLDING FILES]\VideoAPA_For_Host_PC\acquisition\
		> runacquistion.bat
		'''
	48. Make sure to go to Control Panel -> Network and Internet -> View network status and tasks -> Change adapter settings and make sure that you see nothing that shows a virtual machine connection, mainly for security reasons.
	
	If you do have one you will need to disable it

#***************IMPORTANT NOTE: Operation Features with visuals can be found on the document attached "SCORHE Video Acquisition User Guide"*************
	




### https://scorhe.nih.gov
