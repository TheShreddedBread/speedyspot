from PIL import Image
from psdtags import TiffImageResources, PsdPascalStringsBlock, PsdResourceId
import tifffile
import numpy as np
import numpy as np
import cv2
import config
import handleImage
import math
from numba import jit, njit
from abc import ABC, abstractmethod

previewImage = None  # Global variable to hold the preview image

def contractAlphaSmooth(alphaChannel: np.ndarray, pixels: int, blurSigma: float = 1.0, mode: int = 1) -> np.ndarray:
    # Create a mask from the alpha channel and apply Gaussian blur
    if pixels <= 0:
        return alphaChannel
    
    if mode == 1:
        # Normalize alpha
        alphaNorm = alphaChannel.astype(np.float32) / 255.0

        # Binary mask
        mask = (alphaNorm > 0.01).astype(np.uint8)

        # Pad with background so borders shrink correctly
        mask = np.pad(mask, ((1, 1), (1, 1)), mode='constant', constant_values=0)

        # Elliptical kernel gives smoother contraction
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2 * pixels + 1, 2 * pixels + 1))

        # Erode once with the appropriately sized kernel
        mask = cv2.erode(mask, kernel, borderType=cv2.BORDER_CONSTANT, borderValue=0)

        # Remove padding
        mask = mask[pixels:-pixels, pixels:-pixels]

        # Apply contracted mask to original alpha
        contracted = (alphaNorm * mask * 255).astype(np.uint8)

        # Smooth edges
        blurred = cv2.bilateralFilter(contracted, d=2, sigmaColor=75, sigmaSpace=75)

        return blurred
    
    else:  
        # Create a binary mask from the alpha channel
        binaryMask = (alphaChannel > 0).astype(np.uint8)

        # Pad with background so borders shrink correctly
        padded = np.pad(binaryMask, ((1, 1), (1, 1)), mode='constant', constant_values=0)
        
        # Apply Gaussian blur to the binary mask
        binary = cv2.GaussianBlur(padded, (0, 0), sigmaX=blurSigma)

        # Calculate the distance transform
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 3)
        
        # Remove padding
        dist = dist[1:-1, 1:-1]

        # Create a mask based on the distance
        mask = (dist > pixels).astype(np.uint8)

        # Create a contracted alpha channel based on the mask
        contracted = alphaChannel.copy()
        contracted[mask == 0] = 0

        # Apply Gaussian blur to the contracted alpha channel
        if blurSigma > 0:
            contracted = cv2.GaussianBlur(contracted, (0, 0), sigmaX=blurSigma)

        # Clip the values to [0, 255] and convert to uint8
        contracted = np.clip(contracted, 0, 255).astype(np.uint8)
        alphaChannel = contracted
         
    return alphaChannel

def getResolutionTag(dpi: int=300) -> tuple:
    resolution = (dpi, dpi)
    resolutionUnit = 'inch'
    return resolution, resolutionUnit

@njit
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
        holeSize = math.floor(usedMargin/2)
        kernel = np.ones((holeSize * 2 + 1, holeSize * 2 + 1), np.uint8)
        spotLayer = cv2.morphologyEx(spotLayer, cv2.MORPH_CLOSE, kernel)            

    return spotLayer

def generateRGBAimage(alphaChannel: np.ndarray, spotChannel: np.ndarray, r: np.ndarray, g: np.ndarray, b: np.ndarray, spotColor: tuple=(0, 255, 255)) -> np.ndarray:
    mask = (spotChannel == 0)
    r[mask] = spotColor[0] # Red
    g[mask] = spotColor[1] # Green
    b[mask] = spotColor[2] # Blue

    rgbaImage = np.stack([r, g, b, alphaChannel], axis=-1)  # Stack RGB channels
    return rgbaImage

def generateSpotPreview(c: np.ndarray, m: np.ndarray, y: np.ndarray, k: np.ndarray, alphaChannel: np.ndarray, spotChannel: np.ndarray, spotColor=(0, 255, 255)) -> None:
    r,g,b = handleImage.cmykToRgbArray(c, m, y, k)  # Convert CMYK to RGB
    # Create a preview image with the spot channel
    rgbaImage = generateRGBAimage(alphaChannel, spotChannel, r, g, b, spotColor)  # Generate RGBA image
    # Create mask for the spot channel and update RGB channels
    image = Image.fromarray(rgbaImage.astype('uint8'), 'RGBA')
    image.save("data/spot_preview.png")  # Save the preview image

@jit
def invertChannel(channel: np.ndarray) -> np.ndarray:
    # Invert the spot channel
    invertedSpot = 255 - channel
    return invertedSpot.astype(np.uint8)

def showPreview() -> None:
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
    baseName = inputName.rsplit(".", 1)[0]
    newName = f"{baseName}_spot.tif"
    return newName

def cacheFunctions() -> None: # cache functions with numba
    dummyArr = np.full((200, 200), 100, dtype=np.uint8)
    extractWhite(dummyArr,dummyArr,dummyArr,dummyArr,dummyArr,dummyArr)
    invertChannel(dummyArr)
    

def getSpotLayerName() -> str:
    return config.getSetting("spotLayerName")

def renameToPhotoshopStandard(channelName: str) -> str:
    return channelName.replace("_", " _")

def getPreviewColor():
    prevColorName = config.getSetting("previewColor")
    allPrevColors = config.getPreviwColors()
    return allPrevColors.get(prevColorName, allPrevColors.get(config.getDefaultPreviewColorKey()))

def generateSpotImage(inputName: str, outputName: str) -> None:
    colorMode = config.getSetting("colorMode")
    alphaAsSpot = config.getSetting("alphaspot")
    generator = CMYKTiffGenerator(alphaAsSpot) # Default to cmyk
    if (colorMode == "RGB"):
       generator = RGBTiffGenerator(alphaAsSpot)
    
    generator.generateSpot(inputName, outputName)
    
    
def getOffset() -> tuple:
    return (config.getSetting("spotOffsetX"), config.getSetting("spotOffsetY"))

def resizeAllLayersToFitOffset(layers: list|set, valueToUse: int) -> list:
    offsetX, offsetY = getOffset()

    padX = int(abs(offsetX))
    padY = int(abs(offsetY))

    padded = []
    
    padWidth = ((padY, padY), (padX, padX))
    
    for layer in layers:
        padded.append(np.pad(layer, padWidth, mode='constant', constant_values=(valueToUse, valueToUse)))

    return padded

def offsetSpot(spot: np.ndarray) -> np.ndarray:
    offsetX, offsetY = getOffset()
    # offset = [2., 3.]
    # offset = np.array([offsetX, offsetY], dtype=np.uint8)    
    # spot += offset
    newSpot = np.roll(spot, shift=(offsetY, offsetX), axis=(0, 1))
    return newSpot
    
    
class TiffGenerator(ABC):
    def __init__(self, alphaAsSpot):
        super().__init__()
        self.alphaAsSpot = alphaAsSpot
        
    @abstractmethod
    def getPhotoMetric(self) -> str:
        pass
    
    @abstractmethod
    def generateLayerList(self, c, m, y, k, alpha, spot) -> list:
        pass
    
    @abstractmethod
    def generateXmlDescription(self) -> str:
        pass
    
    def getSpotChannelXML(self):
        spotChannelXML = f"<Channel>{getSpotLayerName()}</Channel>"
        if self.alphaAsSpot:
            spotChannelXML = ""
        return spotChannelXML
    
    def generateSpot(self, inputName: str, outputName: str) -> None:
        margin = config.getSetting("margin")
        marginMode = config.getSetting("marginMode")
        smartSpot = [config.getSetting("copywhite"), config.getSetting("fillgaps")]
        
        c,m,y,k,alphaChannel = handleImage.splitImageToCmyk(inputName) # Split the image into CMYK channels and alpha channel
        
        spotChannel = np.copy(alphaChannel)  # Copy alpha channel to spot channel
        spotSized = contractAlphaSmooth(spotChannel, pixels=margin, mode=marginMode) # Contract the alpha channel
        
        if True in smartSpot:
            spotSized = fixSpotSmart(c, m, y, k, alphaChannel, spotSized, margin, smartSpot) # Function to fix the spot channel "smartly"
     

        spotFixed = spotSized.astype(np.uint8) # Make sure it is uint8

        c, m, y, k, alphaChannel, spotResize = resizeAllLayersToFitOffset([c, m, y, k, alphaChannel, spotFixed], 0)
        spotOffset = offsetSpot(spotResize)
        
        if self.alphaAsSpot:
            channelNames = ["Alpha"]
        else:
            channelNames = ["Alpha", renameToPhotoshopStandard(getSpotLayerName())] # Add channel names for the alpha and spot channels
        
        spotSend = invertChannel(spotOffset)
        alphaSend = alphaChannel
        data = np.stack(self.generateLayerList(c, m, y, k, alphaSend, spotSend), axis=-1) # Add the layers together in the correct order
        
        
        alphaPatch = np.maximum(alphaChannel, spotOffset)
        generateSpotPreview(c, m, y, k, alphaPatch, invertChannel(spotOffset), getPreviewColor())  # Generate a preview image of the spot layer
        
        # Create a list of channel names, including the spot channel
        ir = TiffImageResources(
            psdformat=True,
            blocks=[
                PsdPascalStringsBlock(
                    resourceid=PsdResourceId.ALPHA_NAMES_PASCAL,
                    values=channelNames
                ),
            ]
        )

        psTag = (34377, 'B', len(ir.tobytes()), ir.tobytes())  # Photoshop tag

        # Load ICC profile
        iccTag = None
        iccPath = config.getSelectedIcc()
        if (iccPath):
            try:
                with open(iccPath, "rb") as f:
                    iccBytes = f.read()
                    iccTag = (34675, 'B', len(iccBytes), iccBytes)
            except FileNotFoundError:
                pass

        # Add XMP metadata
        xmpXml = """<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
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

        xmpTag = (700, 'B', len(xmpXml.encode('utf-8')), xmpXml.encode('utf-8'))

        # Add XML-description
        xmlDescription = self.generateXmlDescription().strip()

        # Make tags into a tuple
        extratags = [psTag, xmpTag]
        if iccTag:
            extratags.append(iccTag)

        # Extrasamples: 2 = unassociated alpha, 0 = spot
        if self.alphaAsSpot:
            extrasamples = [0]
        else:
            extrasamples = [2, 0]
        
        # Get resolution tag
        resolution, resolutionUnit = getResolutionTag(dpi=config.getSetting("dpi"))
        
        # Write the TIFF image
        tifffile.imwrite(
            outputName,
            data,
            photometric=self.getPhotoMetric(),
            planarconfig='contig',
            extrasamples=extrasamples,
            description=xmlDescription,
            extratags=extratags,
            resolution=resolution,
            resolutionunit=resolutionUnit
        )
    
class CMYKTiffGenerator(TiffGenerator):
    def __init__(self, alphaAsSpot):
        super().__init__(alphaAsSpot)
    
    def getPhotoMetric(self) -> str:
        return 'separated'
    
    def generateLayerList(self, c, m, y, k, alpha, spot) -> list:
        if self.alphaAsSpot:
            return [c, m, y, k, spot]
        return [c, m, y, k, alpha, spot]
    
    def generateXmlDescription(self) -> str:
        return f"""
        <Metadata>
            <Name>CMYK Spot</Name>
            <Channels>
                <Channel>C</Channel>
                <Channel>M</Channel>
                <Channel>Y</Channel>
                <Channel>K</Channel>
                <Channel>Alpha</Channel>
                {self.getSpotChannelXML()}
            </Channels>
        </Metadata>
        """
        
class RGBTiffGenerator(TiffGenerator):
    def __init__(self, alphaAsSpot):
        super().__init__(alphaAsSpot)
    
    def getPhotoMetric(self) -> str:
        return 'rgb'
    
    def generateLayerList(self, c, m, y, k, alpha, spot) -> list:
        r, g, b = handleImage.cmykToRgbArray(c,m,y,k)
        if self.alphaAsSpot:
            return [r, g, b, spot]
        return [r, g, b, alpha, spot]
    
    def generateXmlDescription(self) -> str:
        return f"""
        <Metadata>
            <Name>RGB Spot</Name>
            <Channels>
                <Channel>R</Channel>
                <Channel>G</Channel>
                <Channel>B</Channel>
                <Channel>Alpha</Channel>
                {self.getSpotChannelXML()}
            </Channels>
        </Metadata>
        """