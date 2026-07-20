import customtkinter
import program
import config
import handleEPS
from pageHandler import PageHandler
from navbar import Navbar
import settingsHandler

config.setupProgram()

targetFile = None
programStarted = False

customtkinter.set_default_color_theme("dark-blue")
program.cacheFunctions()  # Cache the functions with dummy values

app = customtkinter.CTk()
app.title("Speedyspot")
app.geometry("400x400")
app.iconbitmap("icon.ico")
app.resizable(False, False)
navbar = Navbar(app, width=400, height=340, fg_color="transparent", bg_color="transparent")
PageHandler(navbar.getContentArea())

settingsHandler.loadSettings()

handleEPS.baseApp = app
settingsHandler.allowUpdate = True

app.update_idletasks()
app.mainloop()