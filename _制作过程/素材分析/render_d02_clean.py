import pymupdf as f,sys,re
from pathlib import Path
from PIL import Image
src=Path(sys.argv[1]); out=Path(sys.argv[2]); d=f.open(src)
for i in [1,5,6,7]:
 p=d[i-1]
 for xr in p.get_contents():
  stream=d.xref_stream(xr)
  pattern=rb'/Artifact <</Subtype/Watermark/Type/Pagination>>BDC\s+q\s+/KSPE1 gs.*?\nQ\s+EMC\s*'
  clean,n=re.subn(pattern,b'',stream,flags=re.S)
  if n: d.update_stream(xr,clean)
 p.get_pixmap(matrix=f.Matrix(1.8,1.8)).save(out/f'D02_page{i:02d}.png')
 print('clean rendered PDF page',i)
im=Image.open(out/'D02_page01.png'); im.crop((130,280,950,820)).save(out/'D02_notice_title.png')
im=Image.open(out/'D02_page05.png'); im.crop((130,195,950,450)).save(out/'D02_rules_heading.png')
