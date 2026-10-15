from PIL import Image
import sys
from pathlib import Path
p=Path(sys.argv[1]); im=Image.open(p); im.crop((0,23,im.width,im.height)).save(p)
