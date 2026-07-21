# Command to compile: pyinstaller --name "Speedyspot" --onefile --icon "icon.ico" --noconsole --add-data=icon.ico:. main.py

import customtkinter
import program
import config
import handleEPS
import threading
from pageHandler import PageHandler
from navbar import Navbar
import settingsHandler
from loadingScreen import LoadingScreen
from setCtkIcon import setIcon

app = customtkinter.CTk()
app.withdraw()

customtkinter.set_default_color_theme("dark-blue")

loader = LoadingScreen(app)

def initialize():
    program.cacheFunctions()  # Cache the functions with dummy values
    settingsHandler.loadSettings()

    loader.close()
    app.deiconify()

    
targetFile = None
programStarted = False

app.title("Speedyspot")
app.geometry("400x400")
setIcon(app)
app.resizable(False, False)

config.setupProgram()
navbar = Navbar(app, width=400, height=340, fg_color="transparent", bg_color="transparent")
PageHandler(navbar.getContentArea())

threading.Thread(target=initialize, daemon=True).start()


handleEPS.baseApp = app
settingsHandler.allowUpdate = True


app.mainloop()