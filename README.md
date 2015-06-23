# vagrant_test
Configuration and automation for vagrant

General Instructions:
1.	Install vagrant from http://www.vagrantup.com/downloads.html  choose appropriate OS.
2.	Install Python 2.7.X from https://www.python.org/downloads. 
3.	Create a new directory to house the vagrant project. Will be referred to as C:\vagrant_project throughout these instructions.
4.	Navigate to the vagrant_project directory and run the command “vagrant init”. This will initialize a vagrant “repository” in the directory.
5.	Clone and extract the zip/GitHub TITLE in the directory. TODO: Nail down the exact step here
6.	A. Windows based: Run Automate_Vagrant_Config.exe.
B. Linux based: From terminal run python Automate_Vagrant_Config.py in the project directory.
7.	Make the appropriate choices for parameters.
8.	Run the command “vagrant up” from the command line while in the vagrant_project directory.
9.	Given a successful install approximately 10-20 minutes should pass.
10.	SSH in via “vagrant ssh” within the terminal if on Linux. However, if on Windows Putty must be installed. Using Putty SSH in to 127.0.0.1 with user:”vagrant” password:”vagrant”. 
11.	For easier access navigate to the vagrant project directory and double click on loadWF.html , to have the portal open in the browser.


Add Aditional Boxes:
1.	If one wants to add additional “desired” boxes. One must find the particular box id online at https://atlas.hashicorp.com/boxes/search . This is the official hashicorp repository . A boxes name is usually of the format x/y where x and y describe certain properties (Ex: hashicorp/precise64 is assembled by hashicorp and is 64 bit flavor of Ubuntu).
2.	Upon obtaining the official box id, one must open Automate_Vagrant_Config.py in their editor of choice.
3.	There are two locations where changes must be made. The first is in the global dictionary named OPERATING_SYSTEMS.  If the official box id of the newly desired box is X/Y the entry will look like this:
a.	“X/Y” : { “name” : ” X/Y”, “description” : “insert description here”} 
The second location is within a list in the main() function. There is a list named m_target_boxes , simple add the id of the box into the list as “X/Y”.
4.	The script will now automatically query your system for currently installed vagrant boxes and install boxes that are absent.  (Using the compiled .exe in the event you want to use the source code, you must have the required python-vagrant library)

