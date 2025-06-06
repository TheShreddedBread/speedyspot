import PIL
import numpy as np
import cv2
import tifffile

def rgb_to_cmyk_array(r, g, b):
    # Constants for scaling, these can be adjusted based on the desired output range
    rgb_scale = 255.0
    cmyk_scale = 255.0

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

def getType(src: str) -> list:
    # Determine the type of image based on its file extension and properties
    # Is it a tiff, png or eps? And is it RGB or CMYK?
    ext = src.split(".")[-1]
    if ext == "tif" or ext == "tiff":
        with tifffile.TiffFile(src) as tif:
            photometric = tif.pages[0].photometric

            imgInfo = ["Unknown", "tiff"]
            if photometric == 2:
                imgInfo[0] = "RGB"
            elif photometric == 5:
                imgInfo[0] = "CMYK"
            return imgInfo
            
    elif ext == "png":
        img = PIL.Image.open(src)
        mode = img.mode
        img.close()

        imgInfo = ["Unknown", "png"]
        if mode == "RGBA":
            imgInfo[0] = "RGB"
        elif mode == "CMYK":
            imgInfo[0] = "CMYK"
        
        return imgInfo

def splitImageToCmyk(src):
    imgInfo = getType(src) # Get image type and color space (RGB or CMYK)
    c,m,y,k, alpha_channel = 0,0,0,0,0 # Initialize variables
    if imgInfo[1]== "tiff":
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
        imgSrc = PIL.Image.open(src)
        if imgInfo[0] == "RGB":
            c, m, y, k = rgb_to_cmyk_array(imgSrc.getchannel("R"), imgSrc.getchannel("G"), imgSrc.getchannel("B"))
            alpha_channel = np.array(imgSrc.getchannel("A"))
        elif imgInfo[0] == "CMYK":
            c, m, y, k = imgSrc.split()
            alpha_channel = np.array(imgSrc.getchannel("A"))
        else:
            raise ValueError("Unknown image type")
    return c, m, y, k, alpha_channel
    
