from home import Home
from settings import Settings

currentPage = "Home"
pages = {}

class PageHandler():
    def __init__(self, app):
        pages["Home"] = Home(master=app, width=300, height=300, fg_color="transparent", bg_color="transparent")
        pages["Settings"] = Settings(master=app, width=300, height=300, fg_color="transparent", bg_color="transparent")
        loadCurrentPage()

def loadCurrentPage():
    for pageFrame in pages.values():
        pageFrame.grid(row=0, column=0, sticky="nsew")
    pages[currentPage].tkraise()
            
def loadPage(page : str):
    global currentPage
    currentPage = page
    loadCurrentPage()
