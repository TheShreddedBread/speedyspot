import os
import time
import PIL
import numpy as np
import cv2
import tifffile
from handleEPS import HandleEPS

# EPS "flag" and the temp filename
usedEPS = False
epsOutputName = None

def get_scales() -> tuple:
    # Constants for scaling, these can be adjusted based on the desired output range
    rgb_scale = 255.0
    cmyk_scale = 255.0
    return rgb_scale, cmyk_scale

def rgb_to_cmyk_array(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> tuple:
    rgb_scale, cmyk_scale = get_scales()

    # Normalize RGB
    r = np.array(r).astype(np.float32) / rgb_scale
    g = np.array(g).astype(np.float32) / rgb_scale
    b = np.array(b).astype(np.float32) / rgb_scale

    # CMY intialization
    c = 1 - r
    m = 1 - g
    y = 1 - b

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
        (c * cmyk_scale).astype(np.uint8),
        (m * cmyk_scale).astype(np.uint8),
        (y * cmyk_scale).astype(np.uint8),
        (k * cmyk_scale).astype(np.uint8)
    )

def cmyk_to_rgb_array(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray) -> tuple:
    # Convert CMYK (0-255) to RGB (0-255)
    rgb_scale, cmyk_scale = get_scales()
    c = np.array(c).astype(np.float32) / cmyk_scale
    m = np.array(m).astype(np.float32) / cmyk_scale
    y = np.array(y).astype(np.float32) / cmyk_scale
    k = np.array(k).astype(np.float32) / cmyk_scale

    r = (1.0 - np.minimum(1.0, c * (1.0 - k) + k))
    g = (1.0 - np.minimum(1.0, m * (1.0 - k) + k))
    b = (1.0 - np.minimum(1.0, y * (1.0 - k) + k))

    return (
        (r * rgb_scale).astype(np.uint8),
        (g * rgb_scale).astype(np.uint8),
        (b * rgb_scale).astype(np.uint8)
    )

def getType(src: str) -> list:
    global usedEPS
    global epsOutputName
    
    # Determine the type of image based on its file extension and properties
    # Is it a tiff or png? And is it RGB or CMYK?
    ext = src.split(".")[-1]
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
        has_transparency = (
            mode in ("RGBA", "LA", "PA") or 
            (mode == "P" and "transparency" in img.info) or
            (mode in ("RGB", "L") and "transparency" in img.info)
        )
        
        img.close()
        
        # Determine the color space of the PNG image
        imgInfo = ["Unknown", "png", has_transparency]  # Add transparency flag
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
    c,m,y,k, alpha_channel = 0,0,0,0,0 # Initialize variables
    if imgInfo[1]== "tiff":
        # Read the TIFF image using tifffile
        imgSrc = tifffile.imread(src)  # shape (H,W,4)
        if imgInfo[0] == "RGB":
            c,m,y,k = rgb_to_cmyk_array(imgSrc[..., 0], imgSrc[..., 1], imgSrc[..., 2])
            alpha_channel = imgSrc[..., 3].astype(np.uint8)
        elif imgInfo[0] == "CMYK":
            c, m, y, k = imgSrc[..., 0], imgSrc[..., 1], imgSrc[..., 2], imgSrc[..., 3]
            alpha_channel = imgSrc[..., 4].astype(np.uint8)
        else:
            raise ValueError("Unknown image type")
        
    elif imgInfo[1] == "png":
        # If it has a temp path for .png
        if (usedEPS):
            src = epsOutputName
        # Read the PNG image using PIL
        imgSrc = PIL.Image.open(src)
        
        # Check if has transparency flag (3rd element in imgInfo)
        has_transparency = len(imgInfo) > 2 and imgInfo[2]
        
        # Convert to RGBA if it has transparency to ensure alpha channel exists
        if has_transparency:
            imgSrc = imgSrc.convert("RGBA")
        
        # Check if the image is RGB or CMYK and convert if needed
        if imgInfo[0] == "RGB":
            c, m, y, k = rgb_to_cmyk_array(imgSrc.getchannel("R"), imgSrc.getchannel("G"), imgSrc.getchannel("B"))
            # Get alpha channel—guaranteed to exist if has_transparency is True
            if has_transparency:
                alpha_channel = np.array(imgSrc.getchannel("A"))
            # else:
                # Create opaque (255) alpha channel
                # alpha_channel = np.full(imgSrc.size[::-1], 0, dtype=np.uint8)
        
        elif imgInfo[0] == "CMYK":
            c, m, y, k = imgSrc.split()
            # Get alpha channel if it exists
            if has_transparency:
                alpha_channel = np.array(imgSrc.getchannel("A"))
            else:
                # Create opaque (255) alpha channel
                alpha_channel = np.full(imgSrc.size[::-1], 255, dtype=np.uint8)
        else:
            raise ValueError("Unknown image type")
    return c, m, y, k, alpha_channel
    
