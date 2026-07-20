from popupFrame import PopupFrame
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

def px2mm(px, dpi) -> float:
    inch = 25.4
    return float(px) * inch / float(dpi)

def mm2px(mm, dpi) -> float:
    inch = 25.4
    return float(mm) * float(dpi) / inch

class HandleEPS(object):
    __tempFilename = "data/temp_eps.png"
    __filepath = ""
    __dpi = None
    __failed = False
    
    def __loadGhostScript(self) -> None:
        if not ghostScriptInstalled():
            raise OSError("Unable to locate Ghostscript on paths")
        
        if os.path.exists("data/gswin64c.exe"):
            EpsImagePlugin.gs_windows_binary =  os.path.abspath("data/gswin64c")

    
    def __init__(self, filepath):
        self.__loadGhostScript()
        self.__dpi = config.getSetting("dpi")
        self.__filepath = filepath
        
    def __convertToPng(self) -> None:
        dpi = self.__dpi
        
        size = self.popup.getSize()
        img = self.popup.getImage()
        
        target_width = int(mm2px(size['w'].get(), dpi))
        if (self.popup.imageProportional()):
            scale_factor = target_width / img.size[0]
            target_height = int(img.size[1] * scale_factor)
        else:
            target_height = int(mm2px(size['h'].get(), dpi))

        # Ensure image is in RGBA mode to preserve alpha channel
        if img.mode != "RGBA":
            img_for_resize = img.convert("RGBA") if "A" in img.getbands() or img.mode in ("LA", "PA") else img
        else:
            img_for_resize = img
        
        im = img_for_resize.resize((target_width, target_height))

        # Try save
        try:
            im.save(self.__tempFilename, format="PNG", dpi=(dpi, dpi))
            self.__failed = False
        except:
            self.__failed = True
        self.popup.close()
        
    def convertNotFailed(self) -> bool:
        return not self.__failed

    def isClosed(self) -> bool:
        return self.popup.isClosed()

    def getOutputFilename(self) -> str:
        return self.__tempFilename
    
    def open(self) -> None:
        # Create the GUI
        self.popup = EpsPopup(baseApp, self.__filepath, self.__convertToPng)
        self.popup.waitUntilClosed()

class EpsPopup(PopupFrame):
    __sizeCallbacks = {"h": None, "w": None}
    __dpi = 300
    __rememberedAppChildren = dict()
    __size = {"h" : 0, "w" : 0}
    __imgSetting = {
        "keepProportional": True,
        "lastChanged": "h" # Refering to the lates dimension that was changed om image ( height (h) or width (w) )
    }
        
    def __validate_int(self, text) -> bool:
        return text.replace(",",".").replace(".", "").isdigit() or text == ""
    
    def rememberElement(self, name, element) -> None:
        self.__rememberedAppChildren[name] = element

    def getElement(self, name):
        return self.__rememberedAppChildren[name]
    
    def getSize(self) -> int:
        return self.__size
    
    def getImage(self) -> Image:
        return self.__img
    
    def imageProportional(self) -> bool:
        return self.__imgSetting["keepProportional"]
    
    def __updateProportional(self, *args) -> None:
        self.__imgSetting["keepProportional"] = bool(self.getElement("proportional").get())
        if (self.imageProportional()):
            if (self.__imgSetting['lastChanged'] == "h"):
                self.__updateHeight()
            else:
                self.__updateWidth()

    
    def __updateDimension(self, dim: str, dimIndex: int, traceFunc) -> None:
        if (dim != "h" and dim != "w"):
            return
        if (dimIndex != 0 and dimIndex != 1):
            return
        
        dimInv = "w"
        if (dim == "w"):
            dimInv = "h"
        dimIndexInv = 1-dimIndex
        
        self.__imgSetting["lastChanged"] = dim
        if (len(self.__size[dim].get().replace(",",".").replace(".", "")) == 0):
            dim_target = 0
        else:
            dim_target = int(mm2px(self.__size[dim].get(), self.__dpi))
        if (self.__imgSetting['keepProportional']):
            
            scale_factor = dim_target / self.__img.size[dimIndex]
            dim_inv_target = int(self.__img.size[dimIndexInv] * scale_factor)
            
            # Remove trace, update size and re-enable trace 
            self.__size[dimInv].trace_remove("write", self.__sizeCallbacks[dimInv])
            self.__size[dimInv].set(str(round(px2mm(dim_inv_target, self.__dpi), 2)))
            self.__sizeCallbacks[dimInv] = self.__size[dimInv].trace_add("write", traceFunc)
        
    
    def __updateHeight(self, *args) -> None:
        self.__updateDimension("h", 1, self.__updateWidth)
        
    def __updateWidth(self, *args) -> None:
        self.__updateDimension("w", 0, self.__updateHeight)
    
    def __init__(self, parent, filepath, convertFunction):
        super().__init__(parent=parent, title="Import EPS", size="350x200")
        vcmd = self.register(self.__validate_int)
        self.__dpi = config.getSetting("dpi")
        self.__size = {"h" : customtkinter.StringVar(), "w" : customtkinter.StringVar()}

        # Labels
        customtkinter.CTkLabel(self, text="Width (mm)").grid(row=3, column=0, padx=10, pady=(10, 0))
        customtkinter.CTkLabel(self, text="Height (mm)").grid(row=3, column=1, padx=10, pady=(10, 0))

        # Varibles for settings
        customtkinter.CTkEntry(self, textvariable=self.__size["w"], validate="key", validatecommand=(vcmd, "%P")).grid(row=4, column=0, padx=10, pady=0)
        customtkinter.CTkEntry(self, textvariable=self.__size["h"], validate="key", validatecommand=(vcmd, "%P")).grid(row=4, column=1, padx=10, pady=0)

        # Import button
        impBtn = customtkinter.CTkButton(self, text="Import", fg_color="Black", command=convertFunction)  # single color name
        impBtn.grid(row=7, column=0, padx=20, pady=30)
        self.rememberElement("import", impBtn)

        # Prop
        propBtn = customtkinter.CTkSwitch(self, text="Keep Proportional", command=self.__updateProportional)
        propBtn.select()
        propBtn.grid(row=7, column=1, padx=10, pady=0)
        self.rememberElement("proportional", propBtn)
        
        self.__img = Image.open(filepath)
        self.__img.load(scale=(self.__dpi)/72, transparency=True)
        
        # Set values
        self.__size['h'].set(round(px2mm(self.__img.size[1], self.__dpi), 2))
        self.__size['w'].set(round(px2mm(self.__img.size[0], self.__dpi),2))
        
        # Add tracking of fields
        self.__sizeCallbacks['h'] = self.__size['h'].trace_add("write", self.__updateHeight)
        self.__sizeCallbacks['w'] = self.__size['w'].trace_add("write", self.__updateWidth)