from PIL import Image
from psdtags import TiffImageResources, PsdPascalStringsBlock, PsdResourceId
import tifffile
import numpy as np
import numpy as np
import cv2

def refine_alpha_edge(alpha_channel: np.ndarray, erosion_pixels: int = 2, mode: int = 1) -> np.ndarray:
    """

    Args:
        alpha_channel (np.ndarray): grayscale-alpha-channel (uint8, value 0–255).
        erosion_pixels (int): pixles to erode the alpha channel.
    
    Returns:
        np.ndarray: improved alpha-kanal.
    """
    if erosion_pixels > 0:
        # 1. In with border
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(alpha_channel, kernel, iterations=erosion_pixels)

        # 2. smooting
        if mode == 2:
            blurred = cv2.bilateralFilter(eroded, d=1, sigmaColor=25, sigmaSpace=25)
        else:
            blurred = cv2.GaussianBlur(eroded, (1, 1), sigmaX=1.0)

    # 3. Make sure it's in the range [0, 255]
        smoothed_alpha = np.clip(eroded, 0, 255).astype(np.uint8)
    else:
        smoothed_alpha = alpha_channel
    return smoothed_alpha

def fixWhiteOutsideSpot(c,m,y,k,a,spotLayer,usedMargin):
    # Add spot back if it is white
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            if spotLayer[i][j] == 255:
                continue
            # Check if pixel is white
            if (c[i,j]==m[i,j]==y[i,j]==k[i,j]==0 and a[i,j]!=0):
                spotLayer[i][j] = a[i][j]
            # Just make sure that there are no "unspotted" areas
            elif (a[i][j] == 0):
                try:
                    region = a[i - usedMargin:i + usedMargin + 1, j - usedMargin:j + usedMargin + 1]
                    if np.all(region == 255):
                        spotLayer[i, j] = a[i, j]
                except:
                    continue   

    return spotLayer

def generateSpotImage(inputName, outputName, margin, marginMode=2, smartSpot = False):
    imgSrc = tifffile.imread(inputName)  # shape (H,W,4)
    # --- 4. Stack channels: C, M, Y, K, Alpha, Spot ---
    c, m, y, k = imgSrc[..., 0], imgSrc[..., 1], imgSrc[..., 2], imgSrc[..., 3]
    alpha_channel = imgSrc[..., 4].astype(np.uint8)
    spot_channel = np.copy(imgSrc[..., 4])  # Copy alpha from cmyk to spot
    spot_sized = refine_alpha_edge(spot_channel, margin, mode=marginMode)

    if smartSpot:
        spot_sized = fixWhiteOutsideSpot(c, m, y, k, alpha_channel, spot_sized, margin)

    for i in spot_sized:
        for j in range(len(i)):
            i[j] = 255-i[j]

    spot_fixed = spot_sized.astype(np.uint8)
    data = np.stack([c, m, y, k, alpha_channel, spot_fixed], axis=-1)

    # --- 5. Photoshop Image Resources ---
    channel_names = ["Alpha", "Spot _1"]
    ir = TiffImageResources(
        psdformat=True,
        blocks=[
            # Channel names
            PsdPascalStringsBlock(
                resourceid=PsdResourceId.ALPHA_NAMES_PASCAL,
                values=channel_names
            ),
        ]
    )

    ps_tag = (34377, 'B', len(ir.tobytes()), ir.tobytes())  # Photoshop tag

    # --- 6. Load ICC-profil ---
    icc_tag = None
    icc_path = "data/CoatedFOGRA39.icc"
    try:
        with open(icc_path, "rb") as f:
            icc_bytes = f.read()
            icc_tag = (34675, 'B', len(icc_bytes), icc_bytes)
    except FileNotFoundError:
        print("No ICC profile found, using default.")

    # --- 7. Add XMP-metadata ---
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

    # --- 8. XML-beskrivning ---
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

    # --- 9. Extra tags ---
    extratags = [ps_tag, xmp_tag]
    if icc_tag:
        extratags.append(icc_tag)

    # --- 10. extrasamples: 2 = unassociated alpha, 0 = spot ---
    extrasamples = [2, 0]

    # --- 11. Write to a tif ---
    tifffile.imwrite(
        outputName,
        data,
        photometric='separated',
        planarconfig='contig',
        extrasamples=extrasamples,
        description=xml_description,
        extratags=extratags
    )

def getOutputName(inputName):
    base_name = inputName.rsplit(".", 1)[0]
    new_name = f"{base_name}_spot.tif"
    return new_name
