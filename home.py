import customtkinter
import tkinter.filedialog 
import os
import program
import threading
from CTkMessagebox import CTkMessagebox
import handleEPS
import settingsHandler
from presets import PresetFrame

class Home(customtkinter.CTkFrame):
    def selectFile(self):
        acceptedfileTypes = []
        canHandleEPS = handleEPS.ghostScriptInstalled()
        if (canHandleEPS):
            acceptedfileTypes.append(("Image files","*.tif;*.tiff;*.png;*.eps"))
        else:
            acceptedfileTypes.append(("Image files","*.tif;*.tiff;*.png;*"))
        acceptedfileTypes.append(("TIFF files", "*.tif;*.tiff"))
        acceptedfileTypes.append(("PNG files", "*.png"))
        if (canHandleEPS):
            acceptedfileTypes.append(("EPS files", "*.eps"))
        # acceptedfileTypes.i
            
        filePath = tkinter.filedialog.askopenfilename(filetypes=acceptedfileTypes, title="Select a file")
        global targetFile

        if filePath:
            name, ext = os.path.splitext(os.path.basename(filePath))
            if not ext.lower() in ['.tif', '.tiff', '.png', '.eps']:
                # Show an error message if the file is not TIFF or PNG
                CTkMessagebox(title="Invalid file type", message="Please select a valid TIFF, PNG or EPS file.", icon="cancel")
                targetFile = None # Remove saved file path
                self.chosenFile.configure(text="No file selected") # Update display text
                return
            self.chosenFile.configure(text=os.path.basename(filePath))
            targetFile = filePath
            self.convertBtn.configure(command=self.startProcess)
            self.convertBtn.configure(fg_color="green")
        else:
            self.chosenFile.configure(text="No file selected")
            targetFile = None

    def processImage(self):
        global targetFile
        if targetFile is None:
            return
        self.after(0, lambda: self.info.grid())
        self.after(0, lambda: self.info.configure(text="Processing..."))
        self.convertBtn.configure(command=None)
        self.convertBtn.configure(fg_color="black")
   
        program.generateSpotImage(targetFile, program.getOutputName(targetFile))  # Start the conversion process
      
        self.chosenFile.configure(text="No file selected")
        targetFile = None
        self.previewBtn.configure(command=self.showPreview)
        self.previewBtn.configure(fg_color="green")
        self.after(0, lambda: self.info.configure(text="Done!")) # Show "Done!" message
        self.after(5000, lambda: self.info.grid_forget())  # Hide after 5 seconds
        
    # Start the conversion process in a separate thread
    def startProcess(self):
        threading.Thread(target=self.processImage, daemon=True).start()

    def validateInt(self, text): # Make sure you can only enter integers in the margin input field
        return text.isdigit() or text == ""

    def showPreview(self):
        program.showPreview()

    def onSettingsUpdate(self, *args):
        self.previewBtn.configure(command=None)
        self.previewBtn.configure(fg_color="black")
               
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.vcmd = self.master.register(self.validateInt)

        self.button = customtkinter.CTkButton(self, text="Select File", command=self.selectFile)
        self.button.grid(row=0, column=0, padx=20, pady=0)

        self.chosenFile = customtkinter.CTkLabel(self, text="No file selected", font=("Helvetica", 14, "bold"))
        self.chosenFile.grid(row=1, column=0, padx=20, pady=0)

        self.convertBtn = customtkinter.CTkButton(self, text="Add Spot To File!", fg_color="Black")
        self.convertBtn.grid(row=0, column=1, padx=20, pady=0)

        self.info = customtkinter.CTkLabel(self, text="Done", text_color='red', font=("Helvetica", 14, "bold"))
        self.info.grid(row=1, column=1, padx=10, pady=0)
        self.info.grid_remove()

        customtkinter.CTkLabel(self, text="Margin").grid(row=3, column=0, padx=10, pady=(10, 0))
        self.margin = customtkinter.StringVar()
        settingsHandler.addSetting("margin", self.margin)
        customtkinter.CTkEntry(self, textvariable=self.margin, validate="key", validatecommand=(self.vcmd, "%P")).grid(row=4, column=0, padx=10, pady=0)

        customtkinter.CTkLabel(self, text="DPI").grid(row=3, column=1, padx=10, pady=(10, 0))
        self.dpi = customtkinter.StringVar()
        settingsHandler.addSetting("dpi", self.dpi)
        customtkinter.CTkEntry(self, textvariable=self.dpi, validate="key", validatecommand=(self.vcmd, "%P")).grid(row=4, column=1, padx=10, pady=0)

        self.previewBtn = customtkinter.CTkButton(self, text="Show latest preview", fg_color="Black")
        self.previewBtn.grid(row=7, column=0, padx=20, pady=(30,5))
        
        self.presetFrame = PresetFrame(self)
        self.presetFrame.grid(row=8, column=0, columnspan=2, rowspan=2)
        
        settingsHandler.addFunctionToCallOnUpdate(self.onSettingsUpdate)
