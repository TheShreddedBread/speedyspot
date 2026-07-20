import os
import json
import config
import settingsHandler
import customtkinter as ctk
from popupFrame import PopupFrame
import time

presetPath = "data/presets"
        
def getPresets() -> dict:
    presets = dict()
    presets['Default'] = config.getStandardValues()
    for presetFile in os.listdir(presetPath):
        if (presetFile.endswith(".json")):
            try:
                with open(os.path.join(presetPath, presetFile), "r") as f:
                    data = json.loads(f.read())
                    presets[data['name']] = data['settings']
            except:
                continue
    return presets

def getPresetNames():
    return getPresets().keys()

def loadPreset(presetName: str) -> None:
    foundPresets = getPresets()
    if presetName in foundPresets.keys():
        config.updateSettings(foundPresets[presetName])

def savePreset(presetName: str) -> None:
    presetJSON = dict()
    presetJSON['name'] = presetName
    presetJSON['settings'] = config.getSettingsDict()
    presetStr = json.dumps(presetJSON, indent=2)
    
    fileName = f"{presetName.encode('ascii', errors='ignore').decode("utf-8").replace(" ", "")}.json"
    filePath = f"{presetPath}/{fileName}"
    with open(filePath, "w", encoding="utf-8") as f:
        f.write(presetStr)
    
def deletePreset(presetName: str) -> None:
    if presetName in getPresetNames():
        for presetFile in os.listdir(presetPath):
            if (presetFile.endswith(".json")):
                try:
                    targetFile = os.path.join(presetPath, presetFile)
                    with open(targetFile, "r") as f:
                        data = json.loads(f.read())
                    if (data.get('name', "") == presetName):
                        os.remove(targetFile)
                except Exception as e:
                    print(e)
    
class PresetFrame(ctk.CTkFrame):
    def presetStartup(self) -> None:
        currentLoaded = config.getSelectedPreset()
        foundPresets = getPresets()
        
        if currentLoaded in foundPresets.keys():
            self.selectedPresetName.set(currentLoaded)
            for (setting, value) in config.getSettingsDict().items():
                if setting in foundPresets[currentLoaded].keys():
                    if  foundPresets[currentLoaded][setting] != value:
                        return
                
            self.unsavedLabel.grid_remove()

        else:
            self.selectedPresetName.set("Default")
        
    def markAsUnsaved(self) -> None:
        self.unsavedLabel.grid()
        
    def reloadPresetsList(self) -> None:
        self.selectPresetMenu.configure(values=list(getPresetNames()))
    
    def changePreset(self, presetName) -> None:
        loadPreset(presetName)
        config.setSelectedPreset(presetName)
        settingsHandler.allowUpdate = False
        settingsHandler.loadSettings()
        settingsHandler.allowUpdate = True
        settingsHandler.updateConfigSettings()
        self.unsavedLabel.grid_remove()
        
    def presetSave(self) -> None:
        savePreset(self.selectedPresetName.get())
        self.unsavedLabel.grid_remove()
    
    def presetSaveAs(self) -> None:
        popup = SaveAsFrame(self)
        popup.waitUntilClosed()
        if popup.saveCompleted:      
            saveAsName = popup.getValue()
            
            savePreset(saveAsName)
            self.reloadPresetsList()
            self.changePreset(saveAsName)
            self.selectedPresetName.set(saveAsName)

    def presetConfirmDelete(self) -> None:
        popup = DeleteConfirmFrame(self, self.selectedPresetName.get())
        popup.waitUntilClosed()        

        if (popup.getValue()):
            deletePreset(self.selectedPresetName.get())
            
            self.reloadPresetsList()
            self.changePreset("Default")
            self.selectedPresetName.set("Default")
            
      
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            width=340,
            height=130,
            border_color="black",
            border_width=2
        )
        self.grid_propagate(False)
        
        ctk.CTkLabel(self, text="Preset:").grid(row=0, column=0, padx=(10,10), pady=(10,0))
        self.unsavedLabel = ctk.CTkLabel(self, text="*unsaved settings", font=ctk.CTkFont(family="Arial", slant="italic"))
        self.unsavedLabel.grid(row=0, column=1, padx=10, pady=(10, 0))
        
        self.selectedPresetName = ctk.StringVar()        
        
        self.selectPresetMenu = ctk.CTkOptionMenu(self, variable=self.selectedPresetName, command=self.changePreset, dynamic_resizing=False)
        self.selectPresetMenu.grid(row=1, column=0, padx=(10,10), pady=(2,10))
        ctk.CTkButton(self, text="Save", command=self.presetSave).grid(row=1, column=1, padx=10, pady=(2,10))
        ctk.CTkButton(self, text="Save as", command=self.presetSaveAs).grid(row=2, column=0, padx=10, pady=10)
        ctk.CTkButton(self, text="Delete", command=self.presetConfirmDelete).grid(row=2, column=1, padx=10, pady=10)
        
        self.presetStartup()
        self.reloadPresetsList()
        
        settingsHandler.addFunctionToCallOnUpdate(self.markAsUnsaved)
    
        
class SaveAsFrame(PopupFrame):
    def __init__(self, parent):
        super().__init__(parent=parent, title="Save preset as", size="320x100")
        self.row0 = ctk.CTkFrame(self, width=320, height=20, fg_color="transparent")
        self.grid_propagate(False)
        self.saveCompleted = False
        
        ctk.CTkLabel(self.row0, text="Name: ").grid(row=0, column=0, padx=10, pady=10)
        self.inputvalue = ctk.StringVar()
        self.textinput = ctk.CTkEntry(self.row0, width=200, textvariable=self.inputvalue)
        self.textinput.grid(row=0, column=1, padx=10, pady=10)
        
        self.row0.grid(row=0, column=0, columnspan=2)
        
        ctk.CTkButton(self, text="Save", command=self.completeSaveAs).grid(row=1, column=0, padx=10, pady=10)
        ctk.CTkButton(self, text="Cancel", command=self.close).grid(row=1, column=1, padx=10, pady=10)
        
    def completeSaveAs(self):
        self.lastvalue = self.inputvalue.get()
        self.saveCompleted = True
        self.close()
        
    def getValue(self):
        if self.saveCompleted:
            return self.lastvalue
        return ""
    
    
class DeleteConfirmFrame(PopupFrame):
    def __init__(self, parent, presetName):
        super().__init__(parent=parent, title="Confirm delete", size="320x100")
        self.confirmed = False
        
        self.row0 = ctk.CTkFrame(self, width=320, height=20, fg_color="transparent")
        self.grid_propagate(False)
        
        ctk.CTkLabel(self.row0, text="Confirm delete preset: ").grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(self.row0, text=presetName).grid(row=0, column=1, padx=10, pady=10)
        self.row0.grid(row=0, column=0, columnspan=2)
        
        ctk.CTkButton(self, text="Confirm delete", command=self.confirmDelete).grid(row=1, column=0, padx=10, pady=10)
        ctk.CTkButton(self, text="Cancel", command=self.close).grid(row=1, column=1, padx=10, pady=10)
        
    def confirmDelete(self):
        self.confirmed = True
        self.close()
        
    def getValue(self):
        return self.confirmed