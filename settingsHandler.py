import config
import customtkinter

class Translator():
    def __init__(self, translationDict: dict):
        self.translation = translationDict
        
    def forward(self, text):
        return self.translation.get(text, "")

    def reverse(self, value):
        for text, val in self.translation.items():
            if val == value:
                return text
        raise ValueError(f"Unknown value: {value}")
    
class TranslatorVar(customtkinter.StringVar):
    def __init__(self, translationDict, **args):
        super().__init__(**args)
        self.translator = Translator(translationDict)
        self.firstGet = True

    def load(self):
        return self.translator.forward(super().get())
      
    def save(self, input):
        super().set(self.translator.reverse(input))

allSettings = {}
functionsToCallOnUpdate = list()
allowUpdate = False

def getAllSettings() -> dict:
    settingsDict = {}
    for setting in allSettings.keys():
        try:
            if isinstance(allSettings[setting], TranslatorVar):
                value = allSettings[setting].load()
            else:
                value = allSettings[setting].get()    
        except:
            continue
        try:
            settingsDict[setting] = config.convertValue(value, config.getStandardSettingType(setting))
        except:
            raise TypeError(f"Ignoring {setting} due to error, using default")
    return settingsDict

def loadSettings():
    savedValues = config.getSettingsDict()
    defaultValue = config.getStandardValues()
    for setting in allSettings.keys():
        backup = defaultValue.get(setting)
        data = savedValues.get(setting, backup)
        element = allSettings[setting]
        
        if isinstance(element, customtkinter.CTkSwitch):
            if data:
                element.select()
            else:
                element.deselect()
        elif isinstance(element, TranslatorVar):
            element.save(data)
        else:
            element.set(data)
            
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