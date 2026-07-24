import customtkinter as ctk
import config
import settingsHandler

class Settings(ctk.CTkFrame):
    def validate_cordinate(self, text):
        if (len(text) > 0):
            if (text.startswith("-")):
                text = text[1:]
        return text == "" or text.isdigit()

    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.keyFilter = self.master.register(self.validate_cordinate)
            
        self.colorMode = ctk.StringVar()
        settingsHandler.addSetting("colorMode", self.colorMode)
        ctk.CTkLabel(self, text="Color mode").grid(row=0, column=0)
        ctk.CTkOptionMenu(self, values=["CMYK", "RGB"], variable=self.colorMode).grid(row=1, column=0, padx=10, pady=0)
        
        self.spotLayerName = ctk.StringVar()
        settingsHandler.addSetting("spotLayerName", self.spotLayerName)
        ctk.CTkLabel(self, text="Spot layer name").grid(row=0, column=1)
        self.spotNameEntry = ctk.CTkEntry(self, textvariable=self.spotLayerName)
        self.spotNameEntry.grid(row=1, column=1)
        
        ctk.CTkLabel(self, text="Spot Offset").grid(row=2, column=0)
        
        self.offsetRow = ctk.CTkFrame(self, width=300, height=30, fg_color="transparent")
        
        ctk.CTkLabel(self.offsetRow, text="X: ", width=2).grid(row=0, column=0, padx=0)
        self.offsetX = ctk.StringVar()
        self.guiOffsetX = ctk.CTkEntry(self.offsetRow, placeholder_text="X", validate="key", validatecommand=(self.keyFilter, "%P"), textvariable=self.offsetX)
        settingsHandler.addSetting("spotOffsetX", self.offsetX)
        self.guiOffsetX.grid(row=0, column=1)
        
        ctk.CTkLabel(self.offsetRow, text="Y: ", width=2).grid(row=0, column=2, padx=(20,0))
        self.offsetY = ctk.StringVar()
        self.guiOffsetY = ctk.CTkEntry(self.offsetRow, placeholder_text="Y", validate="key", validatecommand=(self.keyFilter, "%P"), textvariable=self.offsetY)
        settingsHandler.addSetting("spotOffsetY", self.offsetY)
        self.guiOffsetY.grid(row=0, column=3)
        
        self.offsetRow.grid(row=3, column=0, columnspan=2)
        
        ctk.CTkLabel(self, text="Margin Mode").grid(row=4, column=0, padx=10, pady=(10, 0))
        marginModeTranslation = {"Erode": 1, "Distans Transform": 2}
        self.marginmode = settingsHandler.TranslatorVar(marginModeTranslation)
        ctk.CTkOptionMenu(self, values=["Erode", "Distans Transform"], variable=self.marginmode).grid(row=5, column=0, padx=10, pady=0)
        settingsHandler.addSetting("marginMode", self.marginmode)

        
        self.alphaspot = ctk.CTkSwitch(self, text="Use alpha as spot", command=settingsHandler.updateConfigSettings)
        self.alphaspot.grid(row=5, column=1, padx=10, pady=0)
        settingsHandler.addSetting("alphaspot", self.alphaspot)
        
        
        ctk.CTkLabel(self, text="Smart Spot Options").grid(row=6, column=0, padx=0, pady=(30, 0))

        self.copywhite = ctk.CTkSwitch(self, text="Copy White", command=settingsHandler.updateConfigSettings)
        self.copywhite.grid(row=7, column=0, padx=10, pady=0)
        settingsHandler.addSetting("copywhite", self.copywhite)
        
        self.fillgaps = ctk.CTkSwitch(self, text="Fill Gaps", command=settingsHandler.updateConfigSettings)
        self.fillgaps.grid(row=7, column=1, padx=10, pady=0)
        settingsHandler.addSetting("fillgaps", self.fillgaps)
        
        self.iccProfile = ctk.StringVar()
        settingsHandler.addSetting("iccProfile", self.iccProfile)
        iccProfiles = config.getIccProfiles()
        iccProfiles.insert(0, config.getStandardValues()["iccProfile"])
        
        iccFrame = ctk.CTkFrame(self, fg_color="transparent", width=300, height=40)
        ctk.CTkLabel(iccFrame, text="Generate preview spot color").grid(row=0, column=0, padx=10, pady=(10, 0))
        self.previewColor = ctk.StringVar()
        settingsHandler.addSetting("previewColor", self.previewColor)
        ctk.CTkOptionMenu(iccFrame, values=list(config.getPreviwColors().keys()), variable=self.previewColor).grid(row=1, column=0, padx=10)
        
        ctk.CTkLabel(iccFrame, text="ICC Profile").grid(row=0, column=1, padx=10, pady=(10, 0))
        ctk.CTkOptionMenu(iccFrame, values=iccProfiles, variable=self.iccProfile).grid(row=1, column=1)
        iccFrame.grid(row=8, column=0, padx=10, pady=0, columnspan=2)
        