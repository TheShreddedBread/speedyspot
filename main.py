import customtkinter
import tkinter.filedialog 
import os
import program
import config
import json
import threading
from CTkMessagebox import CTkMessagebox
from PIL import Image
import handleEPS

config.setupProgram()

targetFile = None
programStarted = False
def select_file():
    acceptedfileTypes = []
    canHandleEPS = handleEPS.ghostScriptInstalled()
    if (canHandleEPS):
        acceptedfileTypes.append(("Image files","*.tif;*.tiff;*.png;*.eps"))
    acceptedfileTypes.append(("TIFF files", "*.tif;*.tiff"))
    acceptedfileTypes.append(("PNG files", "*.png"))
    if (canHandleEPS):
        acceptedfileTypes.append(("EPS files", "*.eps"))
        
    file_path = tkinter.filedialog.askopenfilename(filetypes=acceptedfileTypes, title="Select a file")
    global targetFile

    if file_path:
        name, ext = os.path.splitext(os.path.basename(file_path))
        if not ext.lower() in ['.tif', '.tiff', '.png', '.eps']:
            # Show an error message if the file is not TIFF or PNG
            CTkMessagebox(title="Invalid file type", message="Please select a valid TIFF, PNG or EPS file.", icon="cancel")
            targetFile = None # Remove saved file path
            chosenFile.configure(text="No file selected") # Update display text
            return
        chosenFile.configure(text=os.path.basename(file_path))
        targetFile = file_path
        button2.configure(command=start_process)
        button2.configure(fg_color="green")
    else:
        chosenFile.configure(text="No file selected")
        targetFile = None

def processImage():
    global targetFile
    if targetFile is None:
        return
    app.after(0, lambda: info.grid(row=1, column=1, padx=10, pady=10))
    app.after(0, lambda: info.configure(text="Processing..."))
    button2.configure(command=None)
    button2.configure(fg_color="black")
    try:
        marg = int(margin.get())
    except:
        marg = 0  # default value if conversion fails
    program.generateSpotImage(targetFile, program.getOutputName(targetFile), margin=marg, marginMode=int(marginmode.get()), smartSpot=[copywhite.get(), fillgaps.get()], previewColor=previewColor.get())  # Start the conversion process
    chosenFile.configure(text="No file selected")
    targetFile = None
    button3.configure(command=showPreview)
    button3.configure(fg_color="green")
    app.after(0, lambda: info.configure(text="Done!")) # Show "Done!" message
    app.after(5000, lambda: info.grid_forget())  # Hide after 5 seconds
    
# Start the conversion process in a separate thread
def start_process():
    threading.Thread(target=processImage, daemon=True).start()

def validate_int(text): # Make sure you can only enter integers in the margin input field
    return text.isdigit() or text == ""

def showPreview():
    program.showPreview()  # Show the preview of the generated spot image

def updateSettings(*args):
    global programStarted
    if (not programStarted):
        return
    try:
        MarginValue = int(margin.get())
    except (ValueError, tkinter.TclError):
        MarginValue = 0  # default value if conversion fails

    button3.configure(command=None)
    button3.configure(fg_color="black")
    settings = {
        "margin": MarginValue,
        "marginMode": marginmode.get(),
        "copywhite": bool(copywhite.get()),
        "fillgaps": bool(fillgaps.get()),
        "previewColor": previewColor.get()
    }
    config.updateSettings(settings)

def loadSettings():
    settings = config.getSettingsDict()
    backup = config.getStandardValues()

    margin.set(settings.get("margin", backup['margin']))
    marginmode.set(str(settings.get("marginMode", backup['marginMode'])))
    previewColor.set(str(settings.get("previewColor", backup['previewColor'])))

    if settings.get("copywhite", backup['copywhite']):
        copywhite.select()
    else:
        copywhite.deselect()

    if settings.get("fillgaps", backup['fillgaps']):
        fillgaps.select()
    else:
        fillgaps.deselect(0)


app = customtkinter.CTk()
app.title("Speedyspot")
app.geometry("400x340")
vcmd = app.register(validate_int)

button = customtkinter.CTkButton(app, text="Select File", command=select_file)
button.grid(row=0, column=0, padx=20, pady=0)

chosenFile = customtkinter.CTkLabel(app, text="No file selected", font=("Helvetica", 14, "bold"))
chosenFile.grid(row=1, column=0, padx=20, pady=0)

button2 = customtkinter.CTkButton(app, text="Add Spot To File!", fg_color="Black")  # single color name
button2.grid(row=0, column=1, padx=20, pady=0)

info = customtkinter.CTkLabel(app, text="Done", text_color='red', font=("Helvetica", 14, "bold"))
info.grid(row=1, column=1, padx=10, pady=10)
info.grid_forget()

# Labels
customtkinter.CTkLabel(app, text="Margin").grid(row=3, column=0, padx=10, pady=(10, 0))
customtkinter.CTkLabel(app, text="MarginMode").grid(row=3, column=1, padx=10, pady=(10, 0))

# Varibles for settings
margin = customtkinter.StringVar()
marginmode = customtkinter.StringVar()
previewColor = customtkinter.StringVar()

margin.set(2) # Default value
marginmode.set("1")  # Default value

margin.trace_add("write", updateSettings)
marginmode.trace_add("write", updateSettings)
previewColor.trace_add("write", updateSettings)

customtkinter.CTkEntry(app, textvariable=margin, validate="key", validatecommand=(vcmd, "%P")).grid(row=4, column=0, padx=10, pady=0)
customtkinter.CTkOptionMenu(app, values=["1", "2", "3"], variable=marginmode).grid(row=4, column=1, padx=10, pady=0)

customtkinter.CTkLabel(app, text="Smart Spot Options").grid(row=5, column=0, padx=0, pady=(30, 0))

copywhite = customtkinter.CTkSwitch(app, text="Copy White", command=updateSettings)
copywhite.grid(row=6, column=0, padx=10, pady=0)
fillgaps = customtkinter.CTkSwitch(app, text="Fill Gaps", command=updateSettings)
fillgaps.grid(row=6, column=1, padx=10, pady=0)

button3 = customtkinter.CTkButton(app, text="Show preview", fg_color="Black")  # single color name
button3.grid(row=7, column=0, padx=20, pady=30)
customtkinter.CTkOptionMenu(app, values=list(config.getPreviwColors().keys()), variable=previewColor).grid(row=7, column=1, padx=10, pady=30)

customtkinter.set_default_color_theme("dark-blue")

loadSettings() # Load settings from the file if it exists
program.cacheFunctions()  # Cache the functions for later use

handleEPS.baseApp = app
programStarted = True

app.update_idletasks()
app.mainloop()