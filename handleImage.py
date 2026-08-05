import os
import time
import PIL
import numpy as np
import tifffile
from handleEPS import HandleEPS

# EPS "flag" and the temp filename
usedEPS = False
epsOutputName = None

def getScales() -> tuple:
    # Constants for scaling, these can be adjusted based on the desired output range
    rgbScale = 255.0
    cmykScale = 255.0
    return rgbScale, cmykScale

def rgbToCmykArray(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> tuple:
    rgbScale, cmykScale = getScales()

    # Normalize RGB
    r = np.array(r).astype(np.float32) / rgbScale
    g = np.array(g).astype(np.float32) / rgbScale
    b = np.array(b).astype(np.float32) / rgbScale

    # CMY intialization
    c = 1.0 - r
    m = 1.0 - g
    y = 1.0 - b

    k = np.minimum.reduce([c, m, y])
    # Avoid division by zero
    mask = k < 1.0
    # Normalize CMY values
    # Only apply normalization where k < 1 to avoid division by zero
    c[mask] = (c[mask] - k[mask]) / (1 - k[mask])
    m[mask] = (m[mask] - k[mask]) / (1 - k[mask])
    y[mask] = (y[mask] - k[mask]) / (1 - k[mask])

    c[~mask] = 0
    m[~mask] = 0
    y[~mask] = 0

    return (
        (c * cmykScale).astype(np.uint8),
        (m * cmykScale).astype(np.uint8),
        (y * cmykScale).astype(np.uint8),
        (k * cmykScale).astype(np.uint8)
    )

def cmykToRgbArray(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray) -> tuple:
    # Convert CMYK (0-255) to RGB (0-255)
    rgbScale, cmykScale = getScales()
    c = np.array(c).astype(np.float32) / cmykScale
    m = np.array(m).astype(np.float32) / cmykScale
    y = np.array(y).astype(np.float32) / cmykScale
    k = np.array(k).astype(np.float32) / cmykScale

    r = (1.0 - np.minimum(1.0, c * (1.0 - k) + k))
    g = (1.0 - np.minimum(1.0, m * (1.0 - k) + k))
    b = (1.0 - np.minimum(1.0, y * (1.0 - k) + k))

    return (
        (r * rgbScale).astype(np.uint8),
        (g * rgbScale).astype(np.uint8),
        (b * rgbScale).astype(np.uint8)
    )

def getType(src: str) -> list:
    global usedEPS
    global epsOutputName
    
    # Determine the type of image based on its file extension and properties
    # Is it a tiff or png? And is it RGB or CMYK?
    ext = src.split(".")[-1].lower()
    if ext == "tif" or ext == "tiff":
        with tifffile.TiffFile(src) as tif:
            photometric = tif.pages[0].photometric
            # Determine the color space of the TIFF image
            imgInfo = ["Unknown", "tiff"]
            if photometric == 2:
                imgInfo[0] = "RGB"
            elif photometric == 5:
                imgInfo[0] = "CMYK"
            return imgInfo
            
    elif ext == "png":
        img = PIL.Image.open(src)
        mode = img.mode
        
        # Check if image has transparency in any form
        hasTransparency = (
            mode in ("RGBA", "LA", "PA") or 
            (mode == "P" and "transparency" in img.info) or
            (mode in ("RGB", "L") and "transparency" in img.info)
        )
        
        img.close()
        
        # Determine the color space of the PNG image
        imgInfo = ["Unknown", "png", hasTransparency]  # Add transparency flag
        if mode in ("RGBA", "RGB", "LA", "L", "P"):
            imgInfo[0] = "RGB"
        elif mode == "CMYK":
            imgInfo[0] = "CMYK"
        
        return imgInfo
    
    elif ext == "eps":
        eps = HandleEPS(src)
        eps.open()
        while (not eps.isClosed()):
            time.sleep(1)
        if (eps.convertNotFailed()):
            # Set usedEPS "flag"
            usedEPS = True
            # remeber temp path for eps convertion
            epsOutputName = eps.getOutputFilename()
            imgInfo = getType(os.path.abspath(eps.getOutputFilename()))
            return imgInfo
        else:
            raise ValueError("EPS convertion failed")

def splitImageToCmyk(src: str) -> tuple:
    global usedEPS
    global epsOutputName
    # Make sure to reset usedEPS "flag"
    usedEPS = False
    epsOutputName = None
    # Create a CMYK image from an RGB or CMYK source image, using information from the function getType
    imgInfo = getType(src) # Get image type and color space (RGB or CMYK)
    c, m, y, k, alphaChannel = 0,0,0,0,0 # Initialize variables
    if imgInfo[1]== "tiff":
        # Read the TIFF image using tifffile
        imgSrc = tifffile.imread(src)  # shape (H,W,4)
        if imgInfo[0] == "RGB":
            c,m,y,k = rgbToCmykArray(imgSrc[..., 0], imgSrc[..., 1], imgSrc[..., 2])
            alphaChannel = imgSrc[..., 3].astype(np.uint8)
        elif imgInfo[0] == "CMYK":
            c, m, y, k = imgSrc[..., 0], imgSrc[..., 1], imgSrc[..., 2], imgSrc[..., 3]
            alphaChannel = imgSrc[..., 4].astype(np.uint8)
        else:
            raise ValueError("Unknown image type")
        
    elif imgInfo[1] == "png":
        # If it has a temp path for .png
        if (usedEPS):
            src = epsOutputName
        # Read the PNG image using PIL
        imgSrc = PIL.Image.open(src)
        
        # Check if has transparency flag (3rd element in imgInfo)
        hasTransparency = len(imgInfo) > 2 and imgInfo[2]
        # Convert to RGBA if it has transparency to ensure alpha channel exists
        if hasTransparency:
            imgSrc = imgSrc.convert("RGBA")
        else:
            imgSrc = imgSrc.convert("RGB")
        # Check if the image is RGB or CMYK and convert if needed
        if imgInfo[0] == "RGB":
            c, m, y, k = rgbToCmykArray(imgSrc.getchannel("R"), imgSrc.getchannel("G"), imgSrc.getchannel("B"))
            # Get alpha channel—guaranteed to exist if has transparency is True
            if hasTransparency:
                alphaChannel = np.array(imgSrc.getchannel("A"))
            else:
                alphaChannel = np.full(imgSrc.size[::-1], 255, dtype=np.uint8)
        
        elif imgInfo[0] == "CMYK":
            c, m, y, k = imgSrc.split()
            # Get alpha channel if it exists
            if hasTransparency:
                alphaChannel = np.array(imgSrc.getchannel("A"))
            else:
                # Create opaque (255) alpha channel
                alphaChannel = np.full(imgSrc.size[::-1], 255, dtype=np.uint8)
        else:
            raise ValueError("Unknown image type")
    return c, m, y, k, alphaChannel
    
