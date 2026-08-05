# speedyspot
A simple and fast way to add a spot layer to an image. Could for example be used to generate spot a spot layer for dtf printers or other more complex printers that may require it. There seems to be no one-fits-all combination for the settings due to that many printers (and their RIP programs) have diffrent way to interpetate how the spot layer is represented in the image. Best way to find out what settings to use is to just test or ask manufacture (for example can the spot layer name be really hard to just find out by guessing)

The input image can be a PNG, TIFF or EPS and the output will be a TIFF image (either cmyk or rgb) with a spot layer.
---
### Running to program
To start the program you need to have python installed then install all the requried modules (can be done with following command: ```pip install -r requirements.txt```). Then you should be abble to just run the main.py file. If using the prebuilt .exe file, just dubble click to launch it. Jusst like you would start any other program. 

---
### EPS
Eps is supported with ghostscript and it can be installed in two ways. Way 1 is the recommended and the simpler way. However if way 2 is installed it will be prioritized.

#### Way 1 (Recommended)
Install it as standard, the program should find it. To check if it was found, press the "Select image" button and check if eps is listed as one of the formats that can be selected. If  don't: make sure it was added to the enviorment varibles. If it was not done by default: do it manually.

#### Way 2
*Only recommended if wanting a specific ghostscript version for this program or don't want to install ghostscript on computer*

1. Download ghostscript as standard and open the .exe file with a program like 7-zip. 

2. Find the following files:
    - gsdll64.dll
    - gsdll64.lib
    - gswin64c.exe

3. Copy the files into the data folder.

---
### ICC Profiles
To use a ICC profile place it in the data/presets folder that will be created upon running the script for the first time and select it from the dropdown. Might require a restart of the program for it to show up.

---
### Presets
Any saved preset will be found in the data/presets folder and can be transferred between to installations of the program. Simply move a copy of the preset's json file to the other program data/presets folder. You will need to restart the program to see the new presets after moving them into the folder.

---
### Compile the program
If you would want to compile the program by yourself to and .exe, use the following command: ```pyinstaller --name "Speedyspot" --onefile --icon "icon.ico" --noconsole --add-data=icon.ico:. main.py``` then look in the dist folder. For more documentation, look at the documentation for pyinstaller itself: https://pyinstaller.org/
