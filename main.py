import customtkinter
import tkinter.filedialog 
import os
import program
import json
import threading
from CTkMessagebox import CTkMessagebox

targetFile = None
def select_file():
    file_path = tkinter.filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif;*.tiff"), ("PNG files", "*.png")], title="Select a file")
    global targetFile

    if file_path:
        name, ext = os.path.splitext(os.path.basename(file_path))
        if not ext.lower() in ['.tif', '.tiff', '.png']:
            # Show an error message if the file is not TIFF or PNG
            CTkMessagebox(title="Invalid file type", message="Please select a valid TIFF or PNG file.", icon="cancel")
            targetFile = None
            chosenFile.configure(text="No file selected")
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

    program.generateSpotImage(targetFile, program.getOutputName(targetFile), margin=marg, marginMode=int(marginmode.get()), smartSpot=[copywhite.get(), fillgaps.get()])  # Start the conversion process
    chosenFile.configure(text="No file selected")
    targetFile = None
    app.after(0, lambda: info.configure(text="Done!")) # Show "Done!" message
    app.after(5000, lambda: info.grid_forget())  # Hide after 5 seconds
    
# Start the conversion process in a separate thread
def start_process():
    threading.Thread(target=processImage, daemon=True).start()

def validate_int(text):
    return text.isdigit() or text == ""

def checkfolder():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists("data/settings.json"):
        with open("data/settings.json", "w") as settings_file:
            # Default settings upon first run
            settings = {
                "margin": 2,
                "marginMode": 3,
                "copywhite": False,
                "fillgaps": False
            }
            json.dump(settings, settings_file)

def updateSettings(*args):
    checkfolder()
    try:
        MarginValue = int(margin.get())
    except (ValueError, tkinter.TclError):
        MarginValue = 0  # default value if conversion fails

    with open("data/settings.json", "w") as settings_file:
        settings = {
            "margin": MarginValue,
            "marginMode": marginmode.get(),
            "copywhite": copywhite.get(),
            "fillgaps": fillgaps.get()
        }
        json.dump(settings, settings_file)

def loadSettings():
    checkfolder()
    try:
        with open("data/settings.json", "r") as settings_file:
            settings = json.load(settings_file)
            margin.set(settings.get("margin", 2))
            marginmode.set(str(settings.get("marginMode", 2)))

            if settings.get("copywhite", True):
                copywhite.select()
            else:
                copywhite.deselect()

            if settings.get("fillgaps", True):
                fillgaps.select()
            else:
                fillgaps.deselect()
    except FileNotFoundError:
        return

app = customtkinter.CTk()
app.title("Tiff Fix")
app.geometry("400x300")
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

customtkinter.CTkLabel(app, text="Margin").grid(row=3, column=0, padx=10, pady=(10, 0))
customtkinter.CTkLabel(app, text="MarginMode").grid(row=3, column=1, padx=10, pady=(10, 0))

margin = customtkinter.StringVar()
marginmode = customtkinter.StringVar()
margin.set(2) # Default value
marginmode.set("1")  # Default value

margin.trace_add("write", updateSettings)
marginmode.trace_add("write", updateSettings)

customtkinter.CTkEntry(app, textvariable=margin, validate="key", validatecommand=(vcmd, "%P")).grid(row=4, column=0, padx=10, pady=0)
customtkinter.CTkOptionMenu(app, values=["1", "2", "3"], variable=marginmode).grid(row=4, column=1, padx=10, pady=0)

customtkinter.CTkLabel(app, text="Smart Spot Options").grid(row=5, column=0, padx=0, pady=(30, 0))

copywhite = customtkinter.CTkSwitch(app, text="Copy White", command=updateSettings)
copywhite.grid(row=6, column=0, padx=10, pady=0)
fillgaps = customtkinter.CTkSwitch(app, text="Fill Gaps", command=updateSettings)
fillgaps.grid(row=6, column=1, padx=10, pady=0)

customtkinter.set_default_color_theme("dark-blue")

loadSettings()

app.update_idletasks()
app.mainloop()