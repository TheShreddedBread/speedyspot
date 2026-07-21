from popupFrame import PopupFrame
import customtkinter as ctk
class LoadingScreen(PopupFrame):
    def __init__(self, parent):
        super().__init__(parent=parent, title="Loading...", size="300x80")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        bigfont = ctk.CTkFont(size=30, weight="bold")
        ctk.CTkLabel(self, font=bigfont, justify="center", text="Starting program...").grid(row=0, column=0)
        
        self.grid_propagate(False)