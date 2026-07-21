# speedyspot
A simple and fast way to add a spot layer to an image. Could for example be used to generate spot color for dtf or uv printers. There seems to be no one-fits-all combination for the settings due to that many printer (and their RIP programs) have diffrent way to interpetate how the spot layer is represented in the image.

The input image can be a PNG, TIFF or EPS and the output will be a TIFF image (either cmyk or rgb) with a spot layer.

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