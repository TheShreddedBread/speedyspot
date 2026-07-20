import customtkinter as ctk

class PopupFrame(ctk.CTkToplevel):
    def __init__(self, parent, title, size):
        super().__init__()    
        self.withdraw()
        self.title(title)
        self.geometry(size)
        self.resizable(False, False)
        self.parent = parent
        self.update_idletasks()
        if (parent != None):
            self.wm_transient(parent)
        
        self.deiconify()
        self.focus()
        
    def close(self) -> None:
        self.destroy()

    def isClosed(self) -> bool:
        return not self.winfo_exists()
    
    def waitUntilClosed(self) -> None:
        self.grab_set()
        self.wait_window()