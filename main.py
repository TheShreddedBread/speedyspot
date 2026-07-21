import customtkinter
import program
import config
import handleEPS
import threading
from pageHandler import PageHandler
from navbar import Navbar
import settingsHandler
from loadingScreen import LoadingScreen

app = customtkinter.CTk()
app.withdraw()

customtkinter.set_default_color_theme("dark-blue")

loader = LoadingScreen(app)

def initialize():
    config.setupProgram()
    program.cacheFunctions()  # Cache the functions with dummy values
    settingsHandler.loadSettings()

    loader.close()
    app.deiconify()

    
targetFile = None
programStarted = False

app.title("Speedyspot")
app.geometry("400x400")
app.iconbitmap("icon.ico")
app.resizable(False, False)

navbar = Navbar(app, width=400, height=340, fg_color="transparent", bg_color="transparent")
PageHandler(navbar.getContentArea())

threading.Thread(target=initialize, daemon=True).start()


handleEPS.baseApp = app
settingsHandler.allowUpdate = True


app.mainloop()