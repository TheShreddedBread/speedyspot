import threading
import config
import customtkinter
import os
from PIL import Image, EpsImagePlugin

baseApp = None

def ghostScriptInstalled():
    if os.path.exists("data/gswin64c.exe") and os.path.exists("data/gsdll64.lib") and os.path.exists("data/gsdll64.dll"):
        return True
    return EpsImagePlugin.has_ghostscript() 

class HandleEPS(object):
    __tempFilename = "data/temp_eps.png"
    __filepath = ""
    __dpi = None
    __app = None
    __rememberedAppChildren = dict()
    __img = None
    __imgSetting = {
        "keepProp": True,
        "lastChanged": "h"
    }
    __size = None
    __failed = False
    
    def __loadGhostScript(self):
        if not ghostScriptInstalled():
            raise OSError("Unable to locate Ghostscript on paths")
        
        if os.path.exists("data/gswin64c.exe"):
            EpsImagePlugin.gs_windows_binary =  os.path.abspath("data/gswin64c")

    
    def __init__(self, filepath):
        self.__loadGhostScript()
        self.__dpi = config.getSetting("dpi")
        self.__filepath = filepath
        self.__size = {"h" : customtkinter.StringVar(), "w" : customtkinter.StringVar()}
        self.__sizeCallbacks = {"h": None, "w": None}
        
    def px2mm(self, px, dpi):
        inch = 25.4
        return float(px) * inch / float(dpi)

    def mm2px(self, mm, dpi):
        inch = 25.4
        return float(mm) * float(dpi) / inch

    def __rememberElement(self, name, element):
        self.__rememberedAppChildren[name] = element

    def __getElement(self, name):
        return self.__rememberedAppChildren[name]

    def __validate_int(self, text): # Make sure you can only enter integers in the margin input field
        return text.replace(",",".").replace(".", "").isdigit() or text == ""

    def __convertToPng(self):
        # try:
        dpi = self.__dpi

        target_width = int(self.mm2px(self.__size['w'].get(), dpi))
        if (self.__imgSetting['keepProp']):
            scale_factor = target_width / self.__img.size[0]
            target_height = int(self.__img.size[1] * scale_factor)
        else:
            target_height = int(self.mm2px(self.__size['h'].get(), dpi))

        # Ensure image is in RGBA mode to preserve alpha channel
        if self.__img.mode != "RGBA":
            img_for_resize = self.__img.convert("RGBA") if "A" in self.__img.getbands() or self.__img.mode in ("LA", "PA") else self.__img
        else:
            img_for_resize = self.__img
        
        im = img_for_resize.resize((target_width, target_height))

        # Save with explicit PNG format and transparency preservation
        im.save(self.__tempFilename, format="PNG", dpi=(dpi, dpi))
        self.__failed = False
        # except:
        #     self.__failed = True
        self.__app.destroy()
        
    def __updateProportional(self, *args):
        self.__imgSetting["keepProp"] = bool(self.__getElement("proportional").get())
        if (self.__imgSetting["keepProp"]):
            if (self.__imgSetting['lastChanged'] == "h"):
                self.__updateHeight()
            else:
                self.__updateWidth

    def __updateHeight(self, *args):
        self.__imgSetting["lastChanged"] = "h"
        if (len(self.__size['h'].get().replace(",",".").replace(".", "")) == 0):
            target_height = 0
        else:
            target_height = int(self.mm2px(self.__size['h'].get(), self.__dpi))
        if (self.__imgSetting['keepProp']):
            
            scale_factor = target_height / self.__img.size[1]
            target_width = int(self.__img.size[0] * scale_factor)
            
            # Remove trace, update size and re-enable trace 
            self.__size['w'].trace_remove("write", self.__sizeCallbacks['w'])
            self.__size['w'].set(str(round(self.px2mm(target_width, self.__dpi), 2)))
            self.__sizeCallbacks['w'] = self.__size['w'].trace_add("write", self.__updateWidth)
            
    def __updateWidth(self, *args):
        self.__imgSetting["lastChanged"] = "w"
        if (len(self.__size['w'].get().replace(",",".").replace(".", "")) == 0):
            target_width = 0
        else:
            target_width = int(self.mm2px(self.__size['w'].get(), self.__dpi))
        if (self.__imgSetting['keepProp']):
            if (self.__size['h'].get() == ""):
                target_height = 0
            else:
                scale_factor = target_width / self.__img.size[0]
                target_height = int(self.__img.size[1] * scale_factor)
                
            # Remove trace, update size and re-enable trace 
            self.__size['h'].trace_remove("write", self.__sizeCallbacks['h'])
            self.__size['h'].set(str(round(self.px2mm(target_height, self.__dpi), 2)))
            self.__sizeCallbacks['h'] = self.__size['h'].trace_add("write", self.__updateHeight)

    def convertNotFailed(self):
        return not self.__failed

    def __setupGUI(self):
        app = customtkinter.CTkToplevel()
        app.withdraw()
        app.title("Speedyspot - import EPS")
        app.geometry("350x200")
        app.resizable(False, False)
        vcmd = app.register(self.__validate_int)

        # Labels
        customtkinter.CTkLabel(app, text="Width (mm)").grid(row=3, column=0, padx=10, pady=(10, 0))
        customtkinter.CTkLabel(app, text="Height (mm)").grid(row=3, column=1, padx=10, pady=(10, 0))

        # Varibles for settings
        customtkinter.CTkEntry(app, textvariable=self.__size["w"], validate="key", validatecommand=(vcmd, "%P")).grid(row=4, column=0, padx=10, pady=0)
        customtkinter.CTkEntry(app, textvariable=self.__size["h"], validate="key", validatecommand=(vcmd, "%P")).grid(row=4, column=1, padx=10, pady=0)

        # Import button
        impBtn = customtkinter.CTkButton(app, text="Import", fg_color="Black", command=self.__convertToPng)  # single color name
        impBtn.grid(row=7, column=0, padx=20, pady=30)
        self.__rememberElement("import", impBtn)

        # Prop
        propBtn = customtkinter.CTkSwitch(app, text="Keep Proportional", command=self.__updateProportional)
        propBtn.select()
        propBtn.grid(row=7, column=1, padx=10, pady=0)
        self.__rememberElement("proportional", propBtn)
        
        customtkinter.set_default_color_theme("dark-blue")
        
        app.update_idletasks()
        if (baseApp != None):
            app.wm_transient(baseApp)

        self.__app = app

    def isClosed(self):
        return not self.__app.winfo_exists()

    def getOutputFilename(self):
        return self.__tempFilename
    
    def open(self):
        # Create the GUI
        self.__setupGUI()
        
        # Load Img
        self.__img = Image.open(self.__filepath)
        self.__img.load(scale=(self.__dpi)/72, transparency=True)
        
        # Set values
        self.__size['h'].set(round(self.px2mm(self.__img.size[1], self.__dpi), 2))
        self.__size['w'].set(round(self.px2mm(self.__img.size[0], self.__dpi),2))
        
        # Add tracking of fields
        self.__sizeCallbacks['h'] = self.__size['h'].trace_add("write", self.__updateHeight)
        self.__sizeCallbacks['w'] = self.__size['w'].trace_add("write", self.__updateWidth)
        
        
        # Show and foucs app
        self.__app.deiconify()
        self.__app.focus()
        
    