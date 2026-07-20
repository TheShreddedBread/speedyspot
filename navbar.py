import customtkinter
import pageHandler

class Navbar(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.homeNav = customtkinter.CTkButton(self, text="Home", fg_color="transparent", text_color="blue", command=lambda: pageHandler.loadPage("Home"))
        self.homeNav.grid(row=0, column=0, padx=30, sticky="nsew")
        
        self.settingsNav = customtkinter.CTkButton(self, text="Settings", fg_color="transparent", text_color="blue", command=lambda: pageHandler.loadPage("Settings"))
        self.settingsNav.grid(row=0, column=2, padx=30, sticky="nw")
        
        self.contentArea = customtkinter.CTkFrame(master, width=300, height=300, fg_color="transparent", bg_color="transparent")
        self.contentArea.grid(row=1, column=0, pady=20)
        
        self.grid(row=0, column=0)
        
    def getContentArea(self):
        return self.contentArea
        