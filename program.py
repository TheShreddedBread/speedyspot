from PIL import Image
from psdtags import TiffImageResources, PsdPascalStringsBlock, PsdResourceId
import tifffile
import numpy as np
import numpy as np
import cv2
import handleImage
import math
from numba import jit
from time import perf_counter_ns

previewImage = None  # Global variable to hold the preview image

def getPreviwColors():
    colors = {
        "Cyan": [0, 255, 255],
        "Pink": [255, 0, 255],
        "Yellow": [255, 255, 0],
        "Black": [0, 0, 0],
        "Green": [0, 255, 0],
        "Red": [255, 0, 0],
        "Blue": [0, 0, 255],
    }
    return colors

@jit(nopython=False, forceobj=True)
def contractAlphaSmooth(alpha_channel: np.ndarray, pixels: int, blur_sigma: float = 1.0, mode: int = 1) -> np.ndarray:
    # Create a mask from the alpha channel and apply Gaussian blur
    if pixels > 0 and mode == 1:
        # 1. In with border
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(alpha_channel, kernel, iterations=pixels)

        # Smooth the edges using a bilateral filter
        blurred = cv2.bilateralFilter(eroded, d=2, sigmaColor=75, sigmaSpace=75) # Use bilateral filter for smoother edges

        return np.clip(blurred, 0, 255).astype(np.uint8)
    
    elif mode == 2:
        # Create a binary mask from the alpha channel
        binary = (alpha_channel > 0).astype(np.uint8)

        # Apply Gaussian blur to the binary mask
        binary = cv2.GaussianBlur(binary, (0, 0), sigmaX=blur_sigma)

        # Calculate the distance transform
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 3)

        # Create a mask based on the distance
        mask = (dist > pixels).astype(np.uint8)

        # Create a contracted alpha channel based on the mask
        contracted = alpha_channel.copy()
        contracted[mask == 0] = 0

        # Apply Gaussian blur to the contracted alpha channel
        if blur_sigma > 0:
            contracted = cv2.GaussianBlur(contracted, (0, 0), sigmaX=blur_sigma)

        # Clip the values to [0, 255] and convert to uint8
        contracted = np.clip(contracted, 0, 255).astype(np.uint8)
        alpha_channel = contracted

    elif mode == 3: # Similar to mode 2, but with no blur

        # Normalize the alpha channel to [0, 1]
        alpha_norm = alpha_channel.astype(np.float32) / 255.0

        # Create a binary mask from the normalized alpha channel
        binary_mask = (alpha_norm > 0.01).astype(np.uint8)

        # Calculate the distance transform
        dist = cv2.distanceTransform(binary_mask, distanceType=cv2.DIST_L2, maskSize=5)

        # Create a contracted mask based on the distance
        contracted_mask = (dist > pixels).astype(np.float32)

        # Multiply the alpha channel by the contracted mask
        contracted_alpha = alpha_norm * contracted_mask

        # Scale back to [0, 255] and convert to uint8
        alpha_channel = np.clip(contracted_alpha * 255, 0, 255).astype(np.uint8)
        
    return alpha_channel

def getResolutionTag(dpi: int=300) -> tuple:
    resolution = (dpi, dpi)
    resolution_unit = 'inch'
    return resolution, resolution_unit

@jit
def extractWhite(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray, a: np.ndarray, spotLayer: np.ndarray) -> tuple:
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            if spotLayer[i][j] == 255:
                continue
            
            # Check if pixel is white
            if (c[i, j] == 0 and m[i, j] == 0 and y[i, j] == 0 and k[i, j] == 0 and a[i, j] != 0):
                spotLayer[i][j] = a[i][j] # If the pixel is white, set it to the alpha value
                continue
    return spotLayer

# Function to "fix" diffrent things in the spot layer
def fixSpotSmart(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray, a: np.ndarray, spotLayer: np.ndarray, usedMargin: int, options: tuple) -> np.ndarray:
    if options[0]: # If copy white is enabled
        spotLayer = extractWhite(c, m, y, k, a, spotLayer)  # Extract white pixels if copy white is enabled
    
    if options[1]: # If fill gaps is enabled
        # Use morphological operations to fill gaps in the spot layer
        hole_size = math.floor(usedMargin/2)
        kernel = np.ones((hole_size * 2 + 1, hole_size * 2 + 1), np.uint8)
        spotLayer = cv2.morphologyEx(spotLayer, cv2.MORPH_CLOSE, kernel)            

    return spotLayer

@jit(nopython=False, forceobj=True)
def generateRGBAimage(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray, alpha_channel: np.ndarray, spot_channel: np.ndarray, r: np.ndarray, g: np.ndarray, b: np.ndarray, spotColor: tuple=(0, 255, 255)) -> np.ndarray:
    mask = (spot_channel == 0)
    r[mask] = spotColor[0] # Red
    g[mask] = spotColor[1] # Green
    b[mask] = spotColor[2] # Blue

    rgba_image = np.stack([r, g, b, alpha_channel], axis=-1)  # Stack RGB channels
    return rgba_image

def generateSpotPreview(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray, alpha_channel: np.ndarray, spot_channel: np.ndarray, spotColor=(0, 255, 255)):
    r,g,b = handleImage.cmyk_to_rgb_array(c, m, y, k)  # Convert CMYK to RGB
    # Create a preview image with the spot channel
    rgba_image = generateRGBAimage(c, m, y, k, alpha_channel, spot_channel, r, g, b, spotColor)  # Generate RGBA image
    # Create mask for the spot channel and update RGB channels

    image = Image.fromarray(rgba_image.astype('uint8'), 'RGBA')
    image.save("data/spot_preview.png")  # Save the preview image

@jit
def invertSpot(spot_channel: np.ndarray) -> np.ndarray:
    # Invert the spot channel
    inverted_spot = 255 - spot_channel
    return inverted_spot

def generateSpotImage(inputName: str, outputName: str, margin: int, marginMode: int=2, smartSpot: tuple = [False, False], previewColor: str = "Cyan"):
    c,m,y,k,alpha_channel = handleImage.splitImageToCmyk(inputName) # Split the image into CMYK channels and alpha channel
    spot_channel = np.copy(alpha_channel)  # Copy alpha channel to spot channel
    spot_sized = contractAlphaSmooth(spot_channel, pixels=margin, mode=marginMode) # Contract the alpha channel
    
    if True in smartSpot:
        spot_sized = fixSpotSmart(c, m, y, k, alpha_channel, spot_sized, margin, smartSpot) # Function to fix the spot channel "smartly"

    # Invert the spot channel
    spot_sized = invertSpot(spot_sized)
    spot_fixed = spot_sized.astype(np.uint8) # Make sure it is uint8
    data = np.stack([c, m, y, k, alpha_channel, spot_fixed], axis=-1) # Add the layers together in the correct order

    channel_names = ["Alpha", "Spot _1"] # Add channel names for the alpha and spot channels. The space in "Spot _1" is to match the Photoshop standard.
    
    # Create a list of channel names, including the spot channel
    ir = TiffImageResources(
        psdformat=True,
        blocks=[
            PsdPascalStringsBlock(
                resourceid=PsdResourceId.ALPHA_NAMES_PASCAL,
                values=channel_names
            ),
        ]
    )

    ps_tag = (34377, 'B', len(ir.tobytes()), ir.tobytes())  # Photoshop tag

    # Load ICC profile
    # This is optional, if you don't have an ICC profile, it will use the default one.
    icc_tag = None
    icc_path = "data/CoatedFOGRA39.icc"
    try:
        with open(icc_path, "rb") as f:
            icc_bytes = f.read()
            icc_tag = (34675, 'B', len(icc_bytes), icc_bytes)
    except FileNotFoundError:
        print("No ICC profile found, using default.")

    # Add XMP metadata
    xmp_xml = """<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
    <x:xmpmeta xmlns:x='adobe:ns:meta/'>
    <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
        <rdf:Description rdf:about=''
        xmlns:xmp='http://ns.adobe.com/xap/1.0/'>
        <xmp:CreatorTool>Speedy Spot Tool</xmp:CreatorTool>
        <xmp:Rating>5</xmp:Rating>
        </rdf:Description>
    </rdf:RDF>
    </x:xmpmeta>
    <?xpacket end='w'?>"""

    xmp_tag = (700, 'B', len(xmp_xml.encode('utf-8')), xmp_xml.encode('utf-8'))

    # Add XML-description
    xml_description = """
    <Metadata>
        <Name>CMYK Spot</Name>
        <Channels>
            <Channel>C</Channel>
            <Channel>M</Channel>
            <Channel>Y</Channel>
            <Channel>K</Channel>
            <Channel>Alpha</Channel>
            <Channel>Spot_1</Channel>
        </Channels>
    </Metadata>
    """.strip()

    # Make a the tags into a tuple
    extratags = [ps_tag, xmp_tag]
    if icc_tag:
        extratags.append(icc_tag)

    # Extrasamples: 2 = unassociated alpha, 0 = spot
    extrasamples = [2, 0]
    # Get resolution tag
    resolution, resolution_unit = getResolutionTag(dpi=300)
    generateSpotPreview(c, m, y, k, alpha_channel, spot_fixed, getPreviwColors().get(previewColor,(255,255,0)))  # Generate a preview image of the spot layer
    # Write the TIFF file with the separated channels
    tifffile.imwrite(
        outputName,
        data,
        photometric='separated',
        planarconfig='contig',
        extrasamples=extrasamples,
        description=xml_description,
        extratags=extratags,
        resolution=resolution,
        resolutionunit=resolution_unit
    )

def showPreview():
    global previewImage
    try:
        previewImage.close()  # Try to close the previous image opbject if it exists
    except:
        pass

    try:
        previewImage = Image.open("data/spot_preview.png")  # Load the preview image
        previewImage.show()
    except FileNotFoundError:
        print("Preview image not found")

def getOutputName(inputName) -> str:
    base_name = inputName.rsplit(".", 1)[0]
    new_name = f"{base_name}_spot.tif"
    return new_name

def cacheFunctions(): # Dummy function to cache the functions in numba
    emptyArr = np.empty((1, 1), dtype=np.uint8)
    contractAlphaSmooth(emptyArr, 0, 0, 3)
    generateRGBAimage(emptyArr, emptyArr, emptyArr, emptyArr, emptyArr, emptyArr, emptyArr, emptyArr, emptyArr, (0, 255, 255))
    extractWhite(emptyArr,emptyArr,emptyArr,emptyArr,emptyArr,emptyArr)
    invertSpot(emptyArr)
    