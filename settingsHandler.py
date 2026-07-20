import config
import customtkinter
allSettings = {}
functionsToCallOnUpdate = list()
allowUpdate = False

def getAllSettings() -> dict:
    settingsDict = {}
    for setting in allSettings.keys():
        try:
            value = allSettings[setting].get()
        except:
            continue
        try:
            settingsDict[setting] = config.convertValue(value, config.getStandardSettingType(setting))
        except:
            continue
    return settingsDict

def loadSettings():
    savedValues = config.getSettingsDict()
    defaultValue = config.getStandardValues()
    for setting in allSettings.keys():
        if isinstance(allSettings[setting], customtkinter.CTkSwitch):
            if savedValues.get(setting, defaultValue.get(setting)):
                allSettings[setting].select()
            else:
                allSettings[setting].deselect()
        else:
            allSettings[setting].set(savedValues.get(setting, defaultValue.get(setting)))
            

def addSetting(settingName: str, obj: object) -> None:
    if isinstance(obj, customtkinter.StringVar):
        obj.trace_add("write", updateConfigSettings)
    allSettings[settingName] = obj
    
# Use with caution: could easly create unintentional loop
def addFunctionToCallOnUpdate(func: callable):
    functionsToCallOnUpdate.append(func)
    
def __callFunctions() -> None:
    for func in functionsToCallOnUpdate:
        func()
    
def updateConfigSettings(*args):
    if allowUpdate:
        config.updateSettings(getAllSettings())
        __callFunctions()