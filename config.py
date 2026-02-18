import contextlib
import sqlite3
import os

def createDatabase(default_dict: dict) -> None:
    conn = sqlite3.connect('data/program.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (setting TEXT PRIMARY KEY, value TEXT, type TEXT)''')

    # Create array for executemany
    update_arr = [] 
    for key in default_dict.keys():
        if len(key) == 0: continue
        if type(key) != str: raise ValueError("Key must be a string")
        value = default_dict[key]
        update_arr.append((key, str(value), str(type(value).__name__)))

    # Do insert if there is data for the insert
    if len(update_arr) != 0:
        c.executemany("""
            INSERT INTO settings (setting, value, type) VALUES (?, ?, ?) """, update_arr)
    conn.commit() # Save
    conn.close()

def updateSettings(update_dict: dict) -> None:
    # Create connection
    with contextlib.closing(sqlite3.connect('data/program.db')) as conn:    
        c = conn.cursor()

        # Create array for executemany
        update_arr = [] 
        for key in update_dict.keys():
            if len(key) == 0: continue
            if type(key) != str: raise ValueError("Key must be a string")
            value = update_dict[key]
            update_arr.append((str(value), key))

        # Update if there is data for the update
        if len(update_arr) != 0:
            c.executemany("""
                UPDATE settings SET value=? WHERE setting=?""", update_arr)
            conn.commit() # Save

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

def convertValue(value, type):
    if (type == "bool"):
        if value == "True":
            return True
        return False
    elif (type == "int"):
        value = int(value)
    return value

def checkIfValidSetting(setting: str):
    return getStandardValues().keys().__contains__(setting)

def getSetting(setting: str): 
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
            print(row[1], row[2])
            print(convertValue(row[1], row[2]))
            result[row[0]] = convertValue(row[1], row[2])
            # Else it stays as string
    return result


def getStandardValues() -> dict:
    firstKey = list(getPreviwColors().keys())[0]
    if (firstKey == None):
        raise ValueError('There are no preview colors defined in "config.py", getPreviewColors()')
    return {
        "margin": 2,
        "marginMode": 3,
        "copywhite": False,
        "fillgaps": False,
        "previewColor": firstKey,
        "dpi": 300
    }    

def setupProgram() -> None:
    # Fix data folder
    if not os.path.exists("data"):
        os.makedirs("data")
    # Create/setup sqlite3 db
    if not os.path.exists("data/program.db"):
        with open("data/program.db", "w") as db_file:
            db_file.write("")
        createDatabase(getStandardValues())