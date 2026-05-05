import mss
import numpy as np
from PIL import Image
from config import Region

def capture_region(region: Region) -> Image.Image:
    monitor = {"left": region.x, "top": region.y, "width": region.width, "height": region.height}
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        return Image.fromarray(np.array(screenshot))
