import contextlib
import sqlite3
import os

def createDatabase(defaultDict: dict) -> None:
    conn = sqlite3.connect('data/program.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (setting TEXT PRIMARY KEY, value TEXT, type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS preset 
                (key TEXT PRIMARY KEY, information TEXT)
              ''')

    # Create array for executemany
    updateArr = [] 
    for key in defaultDict.keys():
        if len(key) == 0: continue
        if type(key) != str: raise ValueError("Key must be a string")
        value = defaultDict[key]
        updateArr.append((key, str(value), str(type(value).__name__)))

    # Do insert if there is data for the insert
    if len(updateArr) != 0:
        c.executemany("""
            INSERT INTO settings (setting, value, type) VALUES (?, ?, ?) """, updateArr)
    
    c.execute("INSERT INTO preset (key, information) VALUES (?, ?) ", ("current", "Default"))
        
    conn.commit()
    conn.close()
    
def settingExist(name: str) -> bool:
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:    
        c = conn.cursor()
        c.execute("SELECT * FROM settings")
        res = c.fetchall()
        for setting in res:
            if setting[0] == name:
                return True
        return False

def updateSettings(updateDict: dict) -> None:
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:    
        c = conn.cursor()
        for key in updateDict.keys():
            if len(key) == 0: continue
            if type(key) != str: raise ValueError("Key must be a string")
            
            if (settingExist(key)):
                c.execute("UPDATE settings SET value = ? WHERE setting = ?", (str(updateDict[key]), key))
            else:
                if key not in getSettingsDict().keys():
                    continue # Trying to load some old setting or something
                c.execute("INSERT INTO settings (setting, value, type) VALUES (?, ?, ?)", (key, str(updateDict[key]), str(type(getStandardValues()[key]).__name__)))
        conn.commit()

def getPreviwColors() -> dict:
    colors = {
        "Cyan": [0, 255, 255],
        "Pink": [255, 0, 255],
        "Yellow": [255, 255, 0],
        "Black": [0, 0, 0],
        "Green": [0, 255, 0],
        "Red": [255, 0, 0],
        "Blue": [0, 0, 255],
    }
    return colors

def convertValue(value, type) -> bool|int|str:
    if (type == "bool"):
        if value == "True" or str(value) == "1":
            return True
        return False
    elif (type == "int"):
        value = int(value)
    return value

def checkIfValidSetting(setting: str) -> bool:
    return getStandardValues().keys().__contains__(setting)

def getStandardSettingType(setting: str) -> str:
    if checkIfValidSetting(setting):
        return str(type(getStandardValues()[setting]).__name__)
    else:
        raise ValueError("Setting not found")

def getSetting(setting: str) -> bool|int|str:
    if not (checkIfValidSetting(setting)):
        raise ValueError("Setting not found")
    
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:
        c = conn.cursor()
        c.execute("SELECT value, type FROM settings WHERE setting = ?", (setting,))
        try:
            row = c.fetchone()
            return convertValue(row[0], row[1])
        except:
            pass
        return getStandardValues()[setting]

def getSettingsDict() -> dict:
    result = dict()
    
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:    
        c = conn.cursor()
        c.execute("SELECT * FROM settings")
        res = c.fetchall()
        for row in res:
            result[row[0]] = convertValue(row[1], row[2])
    return result

def getDefaultPreviewColorKey() ->  str:
    color = list(getPreviwColors().keys())[0]
    if (color == None):
        raise ValueError('There are no preview colors defined in "config.py", getPreviewColors()')
    return color

def getStandardValues() -> dict:
    firstKey = getDefaultPreviewColorKey()
    return {
        "colorMode": "CMYK",
        "margin": 2,
        "marginMode": 2,
        "alphaspot": False,
        "copywhite": False,
        "fillgaps": False,
        "previewColor": firstKey,
        "dpi": 300,
        "spotLayerName": "Spot_1",
        "spotOffsetX": 0,
        "spotOffsetY": 0,
        "iccProfile": "None"
    }    
    
def getIccProfiles() -> list:
    iccs = list()
    for file in os.listdir("data/icc"):
        if (file.endswith(".icc")):
            iccs.append(file)
    return iccs

def getSelectedIcc() -> str:
    currentIcc = getSetting("iccProfile")
    if currentIcc == getStandardValues()["iccProfile"]:
        return None
    return "data/icc/" + currentIcc

def setSelectedPreset(name: str):
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:    
        c = conn.cursor()
        c.execute("UPDATE preset SET information = ? WHERE key = ?", (name, "current"))
        conn.commit()

def getSelectedPreset() -> str:
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:    
        c = conn.cursor()
        c.execute("SELECT information FROM preset WHERE key = 'current'")
        res = c.fetchone()
        return res[0]
    
def setupProgram() -> None:
    # Fix data folder
    if not os.path.exists("data"):
        os.makedirs("data")
    # Add folder for icc-profiles 
    if not os.path.exists("data/icc"):
        os.makedirs("data/icc")
    # Add presets path    
    if not os.path.exists("data/presets"):
        os.makedirs("data/presets")
    # Create/setup sqlite3 db
    if not os.path.exists("data/program.db"):
        with open("data/program.db", "w") as dbFile:
            dbFile.write("")
        createDatabase(getStandardValues())